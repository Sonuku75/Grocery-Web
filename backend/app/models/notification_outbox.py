"""
Notification Transactional Outbox Model (Module 13)

Ensures zero message loss by persisting events atomically inside business transactions
(e.g., Order created, Payment verified) before asynchronous worker delivery.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from app.db.base import Base, generate_uuid


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class NotificationOutboxEvent(Base):
    """
    Transactional outbox event entry.
    """
    __tablename__ = "notification_outbox_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(36), nullable=False)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload = Column(JSON, nullable=False, default=dict)
    idempotency_key = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(
        String(20),
        nullable=False,
        default=OutboxStatus.PENDING.value,
        index=True,
    )
    attempt_count = Column(Integer, nullable=False, default=0)
    available_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_outbox_status_available", "status", "available_at"),
    )
