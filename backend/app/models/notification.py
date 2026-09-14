"""
Notification Models (Module 13)

Defines core in-app notifications, multi-channel deliveries, and templating system:
- Notification: In-app notification center entity
- NotificationDelivery: Delivery attempt tracking across Email, SMS, Push, and In-App
- NotificationTemplate: Reusable notification templates with variable allowlists
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class NotificationType(str, Enum):
    # Orders
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_CONFIRMED = "ORDER_CONFIRMED"
    ORDER_SHIPPED = "ORDER_SHIPPED"
    ORDER_OUT_FOR_DELIVERY = "ORDER_OUT_FOR_DELIVERY"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    ORDER_CANCELLED = "ORDER_CANCELLED"

    # Payments & Refunds
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_SUCCESS = "REFUND_SUCCESS"
    REFUND_FAILED = "REFUND_FAILED"

    # Account & Security
    WELCOME = "WELCOME"
    PASSWORD_RESET = "PASSWORD_RESET"
    SECURITY_ALERT = "SECURITY_ALERT"

    # Inventory & Operations
    LOW_STOCK_ADMIN = "LOW_STOCK_ADMIN"
    PROMOTION = "PROMOTION"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    EXPIRED = "EXPIRED"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Notification(Base):
    """
    In-app notification entity stored in PostgreSQL.
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=False, default=dict)
    priority = Column(
        String(20),
        nullable=False,
        default=NotificationPriority.MEDIUM.value,
    )
    status = Column(
        String(20),
        nullable=False,
        default=NotificationStatus.UNREAD.value,
    )
    reference_key = Column(String(100), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    read_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    deliveries = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
        order_by="NotificationDelivery.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_expires_at", "expires_at"),
    )


class NotificationDelivery(Base):
    """
    Tracks delivery attempts and status across each channel.
    """
    __tablename__ = "notification_deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    notification_id = Column(
        String(36),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(20), nullable=False)
    provider = Column(String(30), nullable=False)
    provider_message_id = Column(String(100), nullable=True, index=True)
    status = Column(
        String(20),
        nullable=False,
        default=DeliveryStatus.PENDING.value,
    )
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(50), nullable=True)
    failure_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    notification = relationship("Notification", back_populates="deliveries")

    __table_args__ = (
        Index("ix_notification_deliveries_status", "status"),
        Index("ix_notification_deliveries_channel", "channel"),
    )


class NotificationTemplate(Base, TimestampMixin):
    """
    Reusable notification templates with strict variable allowlists.
    """
    __tablename__ = "notification_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=True)
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    locale = Column(String(10), nullable=False, default="en-IN")
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    allowed_variables = Column(JSON, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint(
            "key", "channel", "locale", "version",
            name="uq_notification_template_key_channel_locale_version",
        ),
        Index("ix_notification_templates_lookup", "key", "channel", "locale", "is_active"),
    )
