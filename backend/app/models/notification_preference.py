"""
Notification Preferences Model (Module 13)

Tracks per-channel user preferences. Security alerts are non-disableable.
"""

from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class NotificationCategory(str, Enum):
    ORDER_UPDATES = "ORDER_UPDATES"
    PAYMENT_UPDATES = "PAYMENT_UPDATES"
    PROMOTIONS = "PROMOTIONS"
    SECURITY_ALERTS = "SECURITY_ALERTS"


class NotificationPreference(Base, TimestampMixin):
    """
    User notification preference per category and channel.
    """
    __tablename__ = "notification_preferences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "notification_type", "channel",
            name="uq_notification_preferences_user_type_channel",
        ),
        Index("ix_notification_preferences_user", "user_id"),
    )
