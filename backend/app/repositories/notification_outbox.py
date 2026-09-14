"""
Notification Outbox Repository (Module 13)

Transactional Outbox storage and worker job claiming with exponential backoff.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification_outbox import (
    NotificationOutboxEvent,
    OutboxStatus,
)


class NotificationOutboxRepository:
    """Repository for Transactional Outbox operations."""

    @staticmethod
    async def create_event(
        db: AsyncSession,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        user_id: str,
        payload: Dict[str, Any],
        idempotency_key: str,
    ) -> NotificationOutboxEvent:
        # Check idempotency
        stmt = select(NotificationOutboxEvent).where(
            NotificationOutboxEvent.idempotency_key == idempotency_key
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        event = NotificationOutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            user_id=user_id,
            payload=payload,
            idempotency_key=idempotency_key,
            status=OutboxStatus.PENDING.value,
            attempt_count=0,
            available_at=now,
            created_at=now,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def claim_pending_events(
        db: AsyncSession,
        limit: int = 20,
    ) -> List[NotificationOutboxEvent]:
        """
        Fetches and claims pending outbox events ready for processing.
        Transitions status from PENDING to PROCESSING.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(NotificationOutboxEvent)
            .where(
                NotificationOutboxEvent.status == OutboxStatus.PENDING.value,
                NotificationOutboxEvent.available_at <= now,
            )
            .order_by(NotificationOutboxEvent.available_at.asc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        events = list(res.scalars().all())

        for event in events:
            event.status = OutboxStatus.PROCESSING.value
            event.attempt_count += 1
        await db.flush()

        return events

    @staticmethod
    async def mark_processed(
        db: AsyncSession,
        event_id: str,
    ) -> None:
        stmt = select(NotificationOutboxEvent).where(NotificationOutboxEvent.id == event_id)
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if event:
            event.status = OutboxStatus.PROCESSED.value
            event.processed_at = datetime.now(timezone.utc)
            await db.flush()

    @staticmethod
    async def mark_failed_or_retry(
        db: AsyncSession,
        event_id: str,
        error_message: str,
        max_retries: Optional[int] = None,
        base_delay: Optional[int] = None,
    ) -> NotificationOutboxEvent:
        max_retries = max_retries or settings.NOTIFICATION_MAX_RETRIES
        base_delay = base_delay or settings.NOTIFICATION_RETRY_BASE_DELAY

        stmt = select(NotificationOutboxEvent).where(NotificationOutboxEvent.id == event_id)
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise ValueError(f"Outbox event {event_id} not found")

        event.error_message = error_message
        now = datetime.now(timezone.utc)

        if event.attempt_count >= max_retries:
            # Dead letter - permanently failed
            event.status = OutboxStatus.FAILED.value
            event.processed_at = now
        else:
            # Exponential backoff: delay = base_delay * (2 ** (attempt - 1))
            backoff_seconds = base_delay * (2 ** max(0, event.attempt_count - 1))
            event.status = OutboxStatus.PENDING.value
            event.available_at = now + timedelta(seconds=backoff_seconds)

        await db.flush()
        return event
