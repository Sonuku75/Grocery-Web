"""
Cartify Checkout Session Model (Module 9)

Database models for temporary purchase preparation, authoritative pricing snapshots,
address/items preservation for future order handoff, and safe idempotency control:
- Scoped strictly to authenticated user_id
- Configurable expiration (default 30 mins) with timezone-aware timestamps
- Immutable address and item snapshots preserved for historical integrity
- Safe idempotent confirmation coordination
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class CheckoutStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class CheckoutSession(Base, TimestampMixin):
    __tablename__ = "checkout_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cart_id = Column(
        String(36),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    address_id = Column(
        String(36),
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
    )
    coupon_id = Column(
        String(36),
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(String(32), default=CheckoutStatus.ACTIVE.value, nullable=False, index=True)
    delivery_method = Column(String(64), default="STANDARD", nullable=False)
    delivery_slot = Column(String(128), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    address_snapshot = Column(JSON, nullable=True)
    items_snapshot = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="checkout_sessions", lazy="selectin")
    cart = relationship("Cart", lazy="selectin")
    address = relationship("Address", lazy="selectin")
    coupon = relationship("Coupon", lazy="selectin")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="chk_checkout_subtotal_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_checkout_total_non_negative"),
        Index("idx_checkout_sessions_user_status", "user_id", "status"),
        Index("idx_checkout_sessions_expires_at", "expires_at"),
        Index("idx_checkout_sessions_idempotency", "idempotency_key"),
        Index("idx_checkout_sessions_cart_id", "cart_id"),
    )

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp

    def __repr__(self) -> str:
        return f"<CheckoutSession(id='{self.id}', user_id='{self.user_id}', status='{self.status}', total={self.total_amount})>"
