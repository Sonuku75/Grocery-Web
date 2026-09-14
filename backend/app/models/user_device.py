"""
User Device Model for Push Notifications (Module 13)

Stores device push tokens for iOS, Android, and Web.
Device tokens are sensitive identifiers and must never be exposed to other users or logged raw.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)

from app.db.base import Base, TimestampMixin, generate_uuid


class DevicePlatform(str, Enum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"


class UserDevice(Base, TimestampMixin):
    """
    Registered client device push token.
    """
    __tablename__ = "user_devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String(20), nullable=False)
    device_token = Column(String(255), nullable=False, index=True)
    app_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "device_token",
            name="uq_user_device_user_token",
        ),
        Index("ix_user_devices_lookup", "user_id", "is_active"),
    )
