"""
Payment Service & State Machine (Module 12)

Bank-grade payment orchestration, strict server-authoritative monetary derivation,
tamper-proof cryptographic state machine transitions, and webhook ingestion.
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.errors import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.security_redaction import redact_sensitive_payload
from app.models.order import Order, OrderStatus, PaymentStatus as OrderPaymentStatus, OrderStatusHistory
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentProviderType,
    PaymentStatus,
    WebhookProcessingStatus,
)
from app.providers.factory import get_payment_provider
from app.repositories.payment import (
    PaymentRefundRepository,
    PaymentRepository,
    PaymentWebhookRepository,
)
from app.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
)


class PaymentStateMachine:
    """
    Enforces strict, tamper-proof payment lifecycle transitions.
    """

    ALLOWED_TRANSITIONS = {
        PaymentStatus.PENDING.value: {
            PaymentStatus.AUTHORIZED.value,
            PaymentStatus.PAID.value,
            PaymentStatus.FAILED.value,
            PaymentStatus.CANCELLED.value,
        },
        PaymentStatus.AUTHORIZED.value: {
            PaymentStatus.PAID.value,
            PaymentStatus.FAILED.value,
            PaymentStatus.CANCELLED.value,
        },
        PaymentStatus.PAID.value: {
            PaymentStatus.REFUND_PENDING.value,
            PaymentStatus.PARTIALLY_REFUNDED.value,
            PaymentStatus.REFUNDED.value,
        },
        PaymentStatus.REFUND_PENDING.value: {
            PaymentStatus.PARTIALLY_REFUNDED.value,
            PaymentStatus.REFUNDED.value,
            PaymentStatus.PAID.value,  # Rollback if refund failed upstream
        },
        PaymentStatus.PARTIALLY_REFUNDED.value: {
            PaymentStatus.REFUND_PENDING.value,
            PaymentStatus.PARTIALLY_REFUNDED.value,
            PaymentStatus.REFUNDED.value,
        },
        # Terminal states
        PaymentStatus.FAILED.value: set(),
        PaymentStatus.CANCELLED.value: set(),
        PaymentStatus.REFUNDED.value: set(),
    }

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        if current_status == target_status:
            return

        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValidationError(
                f"Illegal payment status transition from '{current_status}' to '{target_status}'"
            )


class PaymentService:
    """Central business logic engine for Cartify payments."""

    @staticmethod
    async def initiate_payment(
        db: AsyncSession,
        user_id: str,
        req: InitiatePaymentRequest,
        idempotency_key: Optional[str] = None,
    ) -> InitiatePaymentResponse:
        # 1. Fetch Order and verify ownership
        order_stmt = select(Order).where(Order.id == req.order_id)
        order_res = await db.execute(order_stmt)
        order = order_res.scalar_one_or_none()
        if not order:
            raise NotFoundError("Order", req.order_id)

        if order.user_id != user_id:
            raise ForbiddenError("You do not have access to pay for this order.")

        # 2. Check if Order is already paid
        if order.payment_status == OrderPaymentStatus.PAID.value:
            raise ConflictError("This order is already paid.")

        if order.status in {OrderStatus.CANCELLED.value, OrderStatus.FAILED.value}:
            raise ValidationError(f"Cannot initiate payment for order in '{order.status}' status.")

        # 3. Server-authoritative monetary derivation: strictly derived from order.total_amount
        authoritative_amount = Decimal(str(order.total_amount))
        currency = order.currency or "INR"

        # 4. Handle Cash On Delivery (COD)
        if req.payment_method == PaymentMethod.COD:
            payment = await PaymentRepository.create_payment(
                db=db,
                order_id=order.id,
                user_id=user_id,
                provider=PaymentProviderType.MOCK.value,
                payment_method=PaymentMethod.COD.value,
                amount=authoritative_amount,
                currency=currency,
                status=PaymentStatus.PENDING.value,
                metadata={"payment_type": "cash_on_delivery"},
            )
            order.payment_status = OrderPaymentStatus.PENDING.value
            await db.commit()
            await db.refresh(payment)

            return InitiatePaymentResponse(
                payment_id=payment.id,
                order_id=order.id,
                amount=payment.amount,
                currency=payment.currency,
                provider=payment.provider,
                provider_order_id=None,
                payment_method=payment.payment_method,
                status=PaymentStatus(payment.status),
                client_secret=None,
                gateway_data={"instructions": "Pay exact cash upon arrival."},
            )

        # 5. Online Payment Gateways (Mock, Razorpay)
        provider = get_payment_provider(req.provider)

        # Cancel any previous active PENDING payment attempt for this order
        latest_payment = await PaymentRepository.get_latest_by_order_id(db, order.id, for_update=True)
        if latest_payment and latest_payment.status == PaymentStatus.PENDING.value:
            await PaymentRepository.update_payment_status(
                db=db,
                payment=latest_payment,
                new_status=PaymentStatus.CANCELLED.value,
                reason="Superseded by new payment initiation attempt",
            )

        # 6. Create order with upstream gateway
        gateway_order = await provider.create_order(
            amount=authoritative_amount,
            currency=currency,
            receipt=order.order_number,
            notes={"order_id": order.id, "user_id": user_id},
        )
        provider_order_id = gateway_order.get("provider_order_id")

        # 7. Persist payment record
        payment = await PaymentRepository.create_payment(
            db=db,
            order_id=order.id,
            user_id=user_id,
            provider=provider.provider_name,
            payment_method=req.payment_method.value,
            amount=authoritative_amount,
            currency=currency,
            provider_order_id=provider_order_id,
            status=PaymentStatus.PENDING.value,
            metadata=gateway_order.get("metadata", {}),
        )
        await db.commit()
        await db.refresh(payment)

        # Prepare client-facing SDK payload
        gateway_data = {
            "provider": provider.provider_name,
            "provider_order_id": provider_order_id,
            "amount": float(authoritative_amount),
            "currency": currency,
        }
        if provider.provider_name == "RAZORPAY":
            gateway_data["key_id"] = settings.RAZORPAY_KEY_ID
            gateway_data["amount_in_paise"] = int(round(authoritative_amount * 100))

        client_secret = f"pi_{payment.id}_{provider_order_id}"

        return InitiatePaymentResponse(
            payment_id=payment.id,
            order_id=order.id,
            amount=payment.amount,
            currency=payment.currency,
            provider=payment.provider,
            provider_order_id=provider_order_id,
            payment_method=payment.payment_method,
            status=PaymentStatus(payment.status),
            client_secret=client_secret,
            gateway_data=gateway_data,
        )

    @staticmethod
    async def verify_payment(
        db: AsyncSession,
        user_id: str,
        req: VerifyPaymentRequest,
    ) -> Payment:
        # 1. Lock payment row to prevent concurrent verification races
        payment = await PaymentRepository.get_by_id(db, req.payment_id, for_update=True)
        if not payment:
            raise NotFoundError("Payment", req.payment_id)

        # IDOR check
        if payment.user_id != user_id:
            raise ForbiddenError("You do not have permission to verify this payment.")

        # Idempotency check: if already PAID, return cleanly
        if payment.status == PaymentStatus.PAID.value:
            return payment

        # Validate state transition
        PaymentStateMachine.validate_transition(payment.status, PaymentStatus.PAID.value)

        # 2. Cryptographic signature check via provider
        provider = get_payment_provider(payment.provider)
        provider_order_id = payment.provider_order_id or req.provider_order_id or ""
        provider_payment_id = req.provider_payment_id or ""
        signature = req.provider_signature or ""

        is_valid = provider.verify_signature(
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
            signature=signature,
        )

        order_stmt = select(Order).where(Order.id == payment.order_id).with_for_update()
        order_res = await db.execute(order_stmt)
        order = order_res.scalar_one_or_none()

        if not is_valid:
            # Transition to FAILED on signature failure
            await PaymentRepository.update_payment_status(
                db=db,
                payment=payment,
                new_status=PaymentStatus.FAILED.value,
                reason="Cryptographic signature verification failed",
                failure_code="SIGNATURE_VERIFICATION_FAILED",
                failure_message="Gateway signature did not match expected HMAC.",
            )
            if order:
                order.payment_status = OrderPaymentStatus.FAILED.value

            from app.services.notification_service import NotificationService
            await NotificationService.emit_outbox_event(
                db=db,
                event_type="PAYMENT_FAILED",
                aggregate_type="PAYMENT",
                aggregate_id=payment.id,
                user_id=payment.user_id,
                payload={
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "order_number": order.order_number if order else "",
                    "reason": "Cryptographic signature verification failed",
                    "user_id": payment.user_id,
                },
            )
            await db.commit()
            raise ValidationError("Payment verification failed: Invalid provider signature.")

        # 3. Transition to PAID
        await PaymentRepository.update_payment_status(
            db=db,
            payment=payment,
            new_status=PaymentStatus.PAID.value,
            reason="Verified signature successfully",
            provider_payment_id=provider_payment_id,
            provider_event_reference=provider_payment_id,
        )

        # 4. Synchronize Order state
        if order:
            order.payment_status = OrderPaymentStatus.PAID.value
            if order.status == OrderStatus.PENDING.value:
                order.status = OrderStatus.CONFIRMED.value
                db.add(
                    OrderStatusHistory(
                        order_id=order.id,
                        old_status=OrderStatus.PENDING.value,
                        new_status=OrderStatus.CONFIRMED.value,
                        reason="Payment received; order confirmed automatically.",
                        changed_by_user_id=user_id,
                    )
                )

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="PAYMENT_SUCCESS",
            aggregate_type="PAYMENT",
            aggregate_id=payment.id,
            user_id=payment.user_id,
            payload={
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "order_number": order.order_number if order else "",
                "amount": str(payment.amount),
                "currency": payment.currency,
                "user_id": payment.user_id,
            },
        )
        if order and order.status == OrderStatus.CONFIRMED.value:
            await NotificationService.emit_outbox_event(
                db=db,
                event_type="ORDER_CONFIRMED",
                aggregate_type="ORDER",
                aggregate_id=order.id,
                user_id=order.user_id,
                payload={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "user_id": order.user_id,
                },
            )

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def process_webhook(
        db: AsyncSession,
        provider_name: str,
        raw_body_bytes: bytes,
        signature_header: str,
    ) -> Dict[str, Any]:
        # 1. Payload size guard
        if len(raw_body_bytes) > settings.PAYMENT_WEBHOOK_MAX_BYTES:
            raise ValidationError("Webhook payload exceeded maximum allowed size.")

        # 2. Compute SHA256 of raw bytes
        payload_hash = hashlib.sha256(raw_body_bytes).hexdigest()

        # 3. Verify signature using raw bytes before deserializing
        provider = get_payment_provider(provider_name)
        if not provider.verify_webhook_signature(raw_body_bytes, signature_header):
            raise ValidationError("Webhook HMAC signature verification failed.")

        # 4. Parse payload
        try:
            payload = json.loads(raw_body_bytes.decode("utf-8"))
        except Exception as exc:
            raise ValidationError(f"Invalid JSON in webhook payload: {str(exc)}")

        # Extract event ID and type
        event_id = (
            payload.get("event_id")
            or payload.get("id")
            or f"evt_{payload_hash[:16]}"
        )
        event_type = payload.get("event") or payload.get("type") or "unknown"

        # 5. Check duplicate in payment_webhook_events
        existing = await PaymentWebhookRepository.get_event(db, provider.provider_name, event_id)
        if existing:
            return {"status": "ignored", "reason": "duplicate_event", "event_id": event_id}

        webhook_event = await PaymentWebhookRepository.create_event(
            db=db,
            provider=provider.provider_name,
            provider_event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            payload=redact_sensitive_payload(payload),
            status=WebhookProcessingStatus.PROCESSING.value,
        )

        try:
            # 6. Apply event logic
            # Handle payment.captured / payment.authorized / payment.failed
            entity = (
                payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
            ) or payload

            provider_order_id = entity.get("order_id")
            provider_payment_id = entity.get("id") or entity.get("payment_id")

            payment = None
            if provider_order_id:
                payment = await PaymentRepository.get_by_provider_order_id(
                    db, provider.provider_name, provider_order_id, for_update=True
                )
            elif provider_payment_id:
                payment = await PaymentRepository.get_by_provider_payment_id(
                    db, provider.provider_name, provider_payment_id, for_update=True
                )

            if payment:
                if event_type in {"payment.captured", "payment.paid", "mock.payment.captured"}:
                    if payment.status != PaymentStatus.PAID.value:
                        await PaymentRepository.update_payment_status(
                            db=db,
                            payment=payment,
                            new_status=PaymentStatus.PAID.value,
                            reason=f"Webhook event '{event_type}'",
                            provider_payment_id=provider_payment_id,
                            provider_event_reference=event_id,
                        )
                        order_stmt = select(Order).where(Order.id == payment.order_id).with_for_update()
                        order_res = await db.execute(order_stmt)
                        order = order_res.scalar_one_or_none()
                        if order:
                            order.payment_status = OrderPaymentStatus.PAID.value
                            if order.status == OrderStatus.PENDING.value:
                                order.status = OrderStatus.CONFIRMED.value

                        from app.services.notification_service import NotificationService
                        await NotificationService.emit_outbox_event(
                            db=db,
                            event_type="PAYMENT_SUCCESS",
                            aggregate_type="PAYMENT",
                            aggregate_id=payment.id,
                            user_id=payment.user_id,
                            payload={
                                "payment_id": payment.id,
                                "order_id": payment.order_id,
                                "order_number": order.order_number if order else "",
                                "amount": str(payment.amount),
                                "currency": payment.currency,
                                "user_id": payment.user_id,
                            },
                        )

                elif event_type in {"payment.failed", "mock.payment.failed"}:
                    if payment.status == PaymentStatus.PENDING.value:
                        await PaymentRepository.update_payment_status(
                            db=db,
                            payment=payment,
                            new_status=PaymentStatus.FAILED.value,
                            reason=f"Webhook event '{event_type}'",
                            failure_code=entity.get("error_code", "PAYMENT_FAILED"),
                            failure_message=entity.get("error_description", "Payment failed upstream"),
                            provider_event_reference=event_id,
                        )

                        from app.services.notification_service import NotificationService
                        await NotificationService.emit_outbox_event(
                            db=db,
                            event_type="PAYMENT_FAILED",
                            aggregate_type="PAYMENT",
                            aggregate_id=payment.id,
                            user_id=payment.user_id,
                            payload={
                                "payment_id": payment.id,
                                "order_id": payment.order_id,
                                "reason": entity.get("error_description", "Payment failed upstream"),
                                "user_id": payment.user_id,
                            },
                        )

            await PaymentWebhookRepository.update_event_status(
                db=db,
                event=webhook_event,
                new_status=WebhookProcessingStatus.PROCESSED.value,
            )
            await db.commit()
            return {"status": "processed", "event_id": event_id}

        except Exception as exc:
            await db.rollback()
            await PaymentWebhookRepository.update_event_status(
                db=db,
                event=webhook_event,
                new_status=WebhookProcessingStatus.FAILED.value,
                error_message=str(exc),
            )
            await db.commit()
            raise AppError(status_code=500, message=f"Failed to process webhook event: {str(exc)}")

    @staticmethod
    async def retry_payment(
        db: AsyncSession,
        user_id: str,
        order_id: str,
        payment_method: Optional[PaymentMethod] = None,
        provider: Optional[str] = None,
    ) -> InitiatePaymentResponse:
        req = InitiatePaymentRequest(
            order_id=order_id,
            payment_method=payment_method or PaymentMethod.UPI,
            provider=provider,
        )
        return await PaymentService.initiate_payment(db=db, user_id=user_id, req=req)
