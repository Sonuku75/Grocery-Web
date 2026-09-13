"""
Cartify Coupon & CouponUsage Models (Module 8)

Database models for coupons, promotional codes, and customer usage tracking:
- Unique normalized coupon code (uppercase)
- Constrained discount types (PERCENTAGE, FIXED_AMOUNT)
- Authoritative thresholds: minimum_order_value, maximum_discount
- Timezone-aware validity dates: starts_at, expires_at
- Usage limits: global usage_limit, per_user_usage_limit
- Tracking: used_count, coupon_usages table for per-user history
- Extensible for future Module 10 Orders
"""

from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(32), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    minimum_order_value = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    maximum_discount = Column(Numeric(10, 2), nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    usage_limit = Column(Integer, nullable=True)
    per_user_usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    usages = relationship(
        "CouponUsage",
        back_populates="coupon",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    carts = relationship("Cart", back_populates="coupon")

    __table_args__ = (
        CheckConstraint("discount_value > 0", name="chk_coupon_discount_value_positive"),
        CheckConstraint("minimum_order_value >= 0", name="chk_coupon_min_order_non_negative"),
        Index("idx_coupons_code", "code"),
        Index("idx_coupons_active_validity", "is_active", "starts_at", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<Coupon(code='{self.code}', type='{self.discount_type}', value={self.discount_value})>"


class CouponUsage(Base, TimestampMixin):
    __tablename__ = "coupon_usages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    coupon_id = Column(
        String(36),
        ForeignKey("coupons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usage_count = Column(Integer, default=1, nullable=False)

    # Relationships
    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("coupon_id", "user_id", name="uq_coupon_usages_coupon_user"),
        Index("idx_coupon_usages_lookup", "coupon_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<CouponUsage(coupon_id='{self.coupon_id}', user_id='{self.user_id}', count={self.usage_count})>"
