"""
Cartify Payment Models (Module 12)

High-security payment processing, status auditing, webhook idempotency, and refund tracking:
- payments: provider-agnostic payment records storing authoritative monetary values
- payment_status_history: append-only audit trail for state machine transitions
- payment_webhook_events: deduplicated inbound webhook event records
- payment_refunds: full and partial refund records with strict balance constraints
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUND_PENDING = "REFUND_PENDING"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    COD = "COD"


class PaymentProviderType(str, Enum):
    MOCK = "MOCK"
    RAZORPAY = "RAZORPAY"


class WebhookProcessingStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"


class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(
        String(36),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider = Column(String(32), default=PaymentProviderType.MOCK.value, nullable=False, index=True)
    provider_payment_id = Column(String(128), nullable=True, index=True)
    provider_order_id = Column(String(128), nullable=True, index=True)
    payment_method = Column(String(32), default=PaymentMethod.UPI.value, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    status = Column(String(32), default=PaymentStatus.PENDING.value, nullable=False, index=True)
    failure_code = Column(String(64), nullable=True)
    failure_message = Column(Text, nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payments", lazy="selectin")
    user = relationship("User", lazy="selectin")
    status_history = relationship(
        "PaymentStatusHistory",
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentStatusHistory.created_at.asc()",
        lazy="selectin",
    )
    refunds = relationship(
        "PaymentRefund",
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentRefund.created_at.desc()",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payments_amount_non_negative"),
        Index("idx_payments_order_id", "order_id"),
        Index("idx_payments_user_id", "user_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_provider_order", "provider", "provider_order_id"),
        Index("idx_payments_provider_payment", "provider", "provider_payment_id"),
    )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            PaymentStatus.FAILED.value,
            PaymentStatus.CANCELLED.value,
            PaymentStatus.REFUNDED.value,
        }

    @property
    def is_paid(self) -> bool:
        return self.status in {
            PaymentStatus.PAID.value,
            PaymentStatus.PARTIALLY_REFUNDED.value,
        }

    @property
    def total_refunded_amount(self) -> Decimal:
        if not self.refunds:
            return Decimal("0.00")
        return sum(
            (r.amount for r in self.refunds if r.status == RefundStatus.PROCESSED.value),
            Decimal("0.00"),
        )

    @property
    def refundable_amount(self) -> Decimal:
        if not self.is_paid:
            return Decimal("0.00")
        return max(Decimal("0.00"), Decimal(str(self.amount)) - self.total_refunded_amount)

    def __repr__(self) -> str:
        return f"<Payment(id='{self.id}', order_id='{self.order_id}', status='{self.status}', amount={self.amount})>"


class PaymentStatusHistory(Base):
    __tablename__ = "payment_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(
        String(36),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    reason = Column(String(255), nullable=True)
    provider_event_reference = Column(String(128), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    payment = relationship("Payment", back_populates="status_history")

    __table_args__ = (
        Index("idx_payment_status_history_payment_id", "payment_id"),
        Index("idx_payment_status_history_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PaymentStatusHistory(payment_id='{self.payment_id}', {self.old_status} -> {self.new_status})>"


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(32), nullable=False)
    provider_event_id = Column(String(128), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    processing_status = Column(
        String(32),
        default=WebhookProcessingStatus.RECEIVED.value,
        nullable=False,
        index=True,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_webhooks_provider_event"),
        Index("idx_payment_webhooks_status", "processing_status"),
        Index("idx_payment_webhooks_provider_event", "provider", "provider_event_id"),
    )

    def __repr__(self) -> str:
        return f"<PaymentWebhookEvent(provider='{self.provider}', event_id='{self.provider_event_id}', status='{self.processing_status}')>"


class PaymentRefund(Base, TimestampMixin):
    __tablename__ = "payment_refunds"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(
        String(36),
        ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_refund_id = Column(String(128), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(
        String(32),
        default=RefundStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    created_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    created_by = relationship("User", lazy="selectin")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_refunds_amount_positive"),
        Index("idx_payment_refunds_payment_id", "payment_id"),
        Index("idx_payment_refunds_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PaymentRefund(id='{self.id}', payment_id='{self.payment_id}', amount={self.amount}, status='{self.status}')>"
