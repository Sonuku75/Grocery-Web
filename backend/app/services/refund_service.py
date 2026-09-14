"""
Refund Service (Module 12)

Bank-grade full and partial refund processing, balance constraint validation,
upstream gateway dispatch, and automatic payment/order status synchronization.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.errors import AppError, NotFoundError, ValidationError
from app.models.order import Order, PaymentStatus as OrderPaymentStatus
from app.models.payment import Payment, PaymentRefund, PaymentStatus, RefundStatus
from app.models.user import User
from app.providers.factory import get_payment_provider
from app.repositories.payment import PaymentRefundRepository, PaymentRepository
from app.services.payment_service import PaymentStateMachine


class RefundService:
    """Service managing payment refunds and ledger integrity."""

    @staticmethod
    async def initiate_refund(
        db: AsyncSession,
        payment_id: str,
        amount: Decimal,
        reason: Optional[str] = None,
        admin_user: Optional[User] = None,
    ) -> PaymentRefund:
        # 1. Fetch payment with row-level lock
        payment = await PaymentRepository.get_by_id(db, payment_id, for_update=True)
        if not payment:
            raise NotFoundError("Payment", payment_id)

        # 2. Check refundable status
        if payment.status not in {PaymentStatus.PAID.value, PaymentStatus.PARTIALLY_REFUNDED.value}:
            raise ValidationError(
                f"Cannot refund payment with status '{payment.status}'. Only PAID or PARTIALLY_REFUNDED payments can be refunded."
            )

        if amount <= Decimal("0.00"):
            raise ValidationError("Refund amount must be strictly greater than zero.")

        # 3. Check cumulative balance
        already_refunded = await PaymentRefundRepository.get_total_refunded_amount(db, payment.id)
        payment_amount = Decimal(str(payment.amount))
        remaining_refundable = payment_amount - already_refunded

        if amount > remaining_refundable:
            raise ValidationError(
                f"Requested refund amount {amount} exceeds remaining refundable balance {remaining_refundable}."
            )

        previous_status = payment.status
        # Transition to REFUND_PENDING
        PaymentStateMachine.validate_transition(previous_status, PaymentStatus.REFUND_PENDING.value)
        await PaymentRepository.update_payment_status(
            db=db,
            payment=payment,
            new_status=PaymentStatus.REFUND_PENDING.value,
            reason=f"Initiating refund of {amount} {payment.currency}",
        )

        # 4. Dispatch upstream to payment provider
        provider = get_payment_provider(payment.provider)
        provider_payment_id = payment.provider_payment_id or f"mock_{payment.id}"

        try:
            gateway_res = await provider.initiate_refund(
                provider_payment_id=provider_payment_id,
                amount=amount,
                currency=payment.currency,
                notes={"reason": reason or "Admin initiated refund", "payment_id": payment.id},
            )
        except Exception as exc:
            # Rollback payment status to previous on failure
            await PaymentRepository.update_payment_status(
                db=db,
                payment=payment,
                new_status=previous_status,
                reason=f"Refund dispatch failed: {str(exc)}",
            )
            await db.commit()
            raise AppError(status_code=502, message=f"Payment gateway refund initiation failed: {str(exc)}")

        gateway_status = gateway_res.get("status", "processed")
        if gateway_status == "failed":
            await PaymentRepository.update_payment_status(
                db=db,
                payment=payment,
                new_status=previous_status,
                reason="Gateway declined refund request",
            )
            await db.commit()
            raise ValidationError("Payment gateway declined refund request.")

        # 5. Persist PaymentRefund record
        refund_record_status = (
            RefundStatus.PROCESSED.value if gateway_status == "processed" else RefundStatus.PENDING.value
        )
        refund = await PaymentRefundRepository.create_refund(
            db=db,
            payment_id=payment.id,
            amount=amount,
            currency=payment.currency,
            reason=reason,
            provider_refund_id=gateway_res.get("provider_refund_id"),
            status=refund_record_status,
            created_by_user_id=admin_user.id if admin_user else None,
        )

        # 6. Re-evaluate final payment and order statuses
        new_total_refunded = already_refunded + amount
        if new_total_refunded >= payment_amount:
            target_payment_status = PaymentStatus.REFUNDED.value
            target_order_payment_status = OrderPaymentStatus.REFUNDED.value
        else:
            target_payment_status = PaymentStatus.PARTIALLY_REFUNDED.value
            target_order_payment_status = OrderPaymentStatus.PARTIALLY_REFUNDED.value

        await PaymentRepository.update_payment_status(
            db=db,
            payment=payment,
            new_status=target_payment_status,
            reason=f"Refund of {amount} {payment.currency} processed successfully.",
            provider_event_reference=gateway_res.get("provider_refund_id"),
        )

        # Update order payment status
        order_stmt = select(Order).where(Order.id == payment.order_id).with_for_update()
        order_res = await db.execute(order_stmt)
        order = order_res.scalar_one_or_none()
        if order:
            order.payment_status = target_order_payment_status

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="REFUND_SUCCESS",
            aggregate_type="REFUND",
            aggregate_id=refund.id,
            user_id=payment.user_id,
            payload={
                "refund_id": refund.id,
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "order_number": order.order_number if order else "",
                "amount": str(amount),
                "currency": payment.currency,
                "user_id": payment.user_id,
            },
        )

        await db.commit()
        await db.refresh(refund)
        return refund
