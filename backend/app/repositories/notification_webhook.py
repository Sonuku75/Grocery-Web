"""
Notification Webhook Repository (Module 13)

Idempotent deduplication and processing tracking for provider delivery webhooks.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_webhook_event import NotificationWebhookEvent


class NotificationWebhookRepository:
    """Repository for incoming provider webhooks."""

    @staticmethod
    async def get_by_provider_event(
        db: AsyncSession,
        provider: str,
        provider_event_id: str,
    ) -> Optional[NotificationWebhookEvent]:
        stmt = select(NotificationWebhookEvent).where(
            NotificationWebhookEvent.provider == provider.upper(),
            NotificationWebhookEvent.provider_event_id == provider_event_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def record_event(
        db: AsyncSession,
        provider: str,
        provider_event_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> NotificationWebhookEvent:
        event = NotificationWebhookEvent(
            provider=provider.upper(),
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
            processing_status="RECEIVED",
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        await db.flush()
        return event

    @classmethod
    async def create_event(
        cls,
        db: AsyncSession,
        provider: str,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> NotificationWebhookEvent:
        return await cls.record_event(
            db=db,
            provider=provider,
            provider_event_id=event_id,
            event_type=event_type,
            payload=payload,
        )

    @staticmethod
    async def mark_processed(
        db: AsyncSession,
        event_id: str,
    ) -> None:
        stmt = select(NotificationWebhookEvent).where(NotificationWebhookEvent.id == event_id)
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if event:
            event.processing_status = "PROCESSED"
            event.processed_at = datetime.now(timezone.utc)
            await db.flush()

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        event_id: str,
        error_message: str,
    ) -> None:
        stmt = select(NotificationWebhookEvent).where(NotificationWebhookEvent.id == event_id)
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if event:
            event.processing_status = "FAILED"
            event.error_message = error_message
            event.processed_at = datetime.now(timezone.utc)
            await db.flush()
