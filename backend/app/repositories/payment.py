"""
Payment Repositories (Module 12)

Data access layer for payments, append-only status history, webhook events, and refunds.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import (
    Payment,
    PaymentRefund,
    PaymentStatus,
    PaymentStatusHistory,
    PaymentWebhookEvent,
    RefundStatus,
    WebhookProcessingStatus,
)


class PaymentRepository:
    """Repository for Payments and PaymentStatusHistory."""

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        order_id: str,
        user_id: str,
        provider: str,
        payment_method: str,
        amount: Decimal,
        currency: str = "INR",
        provider_order_id: Optional[str] = None,
        provider_payment_id: Optional[str] = None,
        status: str = PaymentStatus.PENDING.value,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            user_id=user_id,
            provider=provider.upper(),
            payment_method=payment_method.upper(),
            amount=amount,
            currency=currency.upper(),
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
            status=status,
            payment_metadata=metadata or {},
        )
        db.add(payment)
        await db.flush()

        # Append initial status history
        history = PaymentStatusHistory(
            payment_id=payment.id,
            old_status=None,
            new_status=status,
            reason="Payment initiated",
            provider_event_reference=provider_order_id,
        )
        db.add(history)
        await db.flush()
        return payment

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        payment_id: str,
        for_update: bool = False,
    ) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.status_history),
                selectinload(Payment.refunds),
            )
            .where(Payment.id == payment_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_latest_by_order_id(
        db: AsyncSession,
        order_id: str,
        for_update: bool = False,
    ) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.status_history),
                selectinload(Payment.refunds),
            )
            .where(Payment.order_id == order_id)
            .order_by(desc(Payment.created_at))
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_provider_order_id(
        db: AsyncSession,
        provider: str,
        provider_order_id: str,
        for_update: bool = False,
    ) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.status_history),
                selectinload(Payment.refunds),
            )
            .where(
                Payment.provider == provider.upper(),
                Payment.provider_order_id == provider_order_id,
            )
            .order_by(desc(Payment.created_at))
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_provider_payment_id(
        db: AsyncSession,
        provider: str,
        provider_payment_id: str,
        for_update: bool = False,
    ) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.status_history),
                selectinload(Payment.refunds),
            )
            .where(
                Payment.provider == provider.upper(),
                Payment.provider_payment_id == provider_payment_id,
            )
            .order_by(desc(Payment.created_at))
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_payment_status(
        db: AsyncSession,
        payment: Payment,
        new_status: str,
        reason: Optional[str] = None,
        provider_event_reference: Optional[str] = None,
        provider_payment_id: Optional[str] = None,
        failure_code: Optional[str] = None,
        failure_message: Optional[str] = None,
        paid_at: Optional[datetime] = None,
    ) -> Payment:
        old_status = payment.status
        payment.status = new_status

        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        if failure_code:
            payment.failure_code = failure_code
        if failure_message:
            payment.failure_message = failure_message
        if paid_at:
            payment.paid_at = paid_at
        elif new_status == PaymentStatus.PAID.value and not payment.paid_at:
            payment.paid_at = datetime.now(timezone.utc)

        history = PaymentStatusHistory(
            payment_id=payment.id,
            old_status=old_status,
            new_status=new_status,
            reason=reason or f"Transition from {old_status} to {new_status}",
            provider_event_reference=provider_event_reference,
        )
        db.add(history)
        await db.flush()
        return payment

    @staticmethod
    async def list_admin_payments(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        payment_method: Optional[str] = None,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[List[Payment], int]:
        filters = []
        if status:
            filters.append(Payment.status == status.upper())
        if provider:
            filters.append(Payment.provider == provider.upper())
        if payment_method:
            filters.append(Payment.payment_method == payment_method.upper())
        if order_id:
            filters.append(Payment.order_id == order_id)
        if user_id:
            filters.append(Payment.user_id == user_id)

        count_stmt = select(func.count(Payment.id)).where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(Payment)
            .options(
                selectinload(Payment.status_history),
                selectinload(Payment.refunds),
            )
            .where(*filters)
            .order_by(desc(Payment.created_at))
            .offset(offset)
            .limit(limit)
        )
        items_res = await db.execute(stmt)
        items = list(items_res.scalars().all())
        return items, total


class PaymentWebhookRepository:
    """Repository for deduplicating and auditing webhook events."""

    @staticmethod
    async def get_event(
        db: AsyncSession,
        provider: str,
        provider_event_id: str,
    ) -> Optional[PaymentWebhookEvent]:
        stmt = select(PaymentWebhookEvent).where(
            PaymentWebhookEvent.provider == provider.upper(),
            PaymentWebhookEvent.provider_event_id == provider_event_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_event(
        db: AsyncSession,
        provider: str,
        provider_event_id: str,
        event_type: str,
        payload_hash: str,
        payload: Dict[str, Any],
        status: str = WebhookProcessingStatus.RECEIVED.value,
    ) -> PaymentWebhookEvent:
        event = PaymentWebhookEvent(
            provider=provider.upper(),
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            payload=payload,
            processing_status=status,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def update_event_status(
        db: AsyncSession,
        event: PaymentWebhookEvent,
        new_status: str,
        error_message: Optional[str] = None,
    ) -> PaymentWebhookEvent:
        event.processing_status = new_status
        if new_status in {WebhookProcessingStatus.PROCESSED.value, WebhookProcessingStatus.IGNORED.value}:
            event.processed_at = datetime.now(timezone.utc)
        if error_message:
            event.error_message = error_message
        await db.flush()
        return event


class PaymentRefundRepository:
    """Repository for tracking payment refunds."""

    @staticmethod
    async def create_refund(
        db: AsyncSession,
        payment_id: str,
        amount: Decimal,
        currency: str = "INR",
        reason: Optional[str] = None,
        provider_refund_id: Optional[str] = None,
        status: str = RefundStatus.PENDING.value,
        created_by_user_id: Optional[str] = None,
    ) -> PaymentRefund:
        refund = PaymentRefund(
            payment_id=payment_id,
            amount=amount,
            currency=currency.upper(),
            reason=reason,
            provider_refund_id=provider_refund_id,
            status=status,
            created_by_user_id=created_by_user_id,
        )
        db.add(refund)
        await db.flush()
        return refund

    @staticmethod
    async def get_by_id(db: AsyncSession, refund_id: str) -> Optional[PaymentRefund]:
        stmt = select(PaymentRefund).where(PaymentRefund.id == refund_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_by_payment_id(db: AsyncSession, payment_id: str) -> List[PaymentRefund]:
        stmt = (
            select(PaymentRefund)
            .where(PaymentRefund.payment_id == payment_id)
            .order_by(desc(PaymentRefund.created_at))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_total_refunded_amount(db: AsyncSession, payment_id: str) -> Decimal:
        stmt = select(func.coalesce(func.sum(PaymentRefund.amount), Decimal("0.00"))).where(
            PaymentRefund.payment_id == payment_id,
            PaymentRefund.status == RefundStatus.PROCESSED.value,
        )
        res = await db.execute(stmt)
        return Decimal(str(res.scalar_one()))
