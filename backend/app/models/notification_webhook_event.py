"""
Notification Webhook Event Model (Module 13)

Provides idempotent deduplication for incoming delivery receipt webhooks
from external communication providers (Email, SMS, Push).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from app.db.base import Base, generate_uuid


class NotificationWebhookEvent(Base):
    """
    Inbound webhook event deduplication and processing log.
    """
    __tablename__ = "notification_webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(30), nullable=False)
    provider_event_id = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    processing_status = Column(String(20), nullable=False, default="RECEIVED")
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_event_id",
            name="uq_notification_webhook_provider_event",
        ),
        Index("ix_notification_webhooks_lookup", "provider", "provider_event_id"),
    )
