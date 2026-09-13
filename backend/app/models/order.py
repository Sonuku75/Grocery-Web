"""
Cartify Order Models (Module 10)

Database models for permanent orders, purchase-time snapshots, status history, and idempotency:
- orders: primary order entity storing immutable delivery address and monetary snapshots
- order_items: purchase-time product snapshots preserving prices, SKUs, and names
- order_status_history: audit log tracking each status transition with timestamp and actor
- idempotency_keys: deduplication records for reliable distributed order placement
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
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class FulfillmentStatus(str, Enum):
    UNFULFILLED = "UNFULFILLED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), default=OrderStatus.PENDING.value, nullable=False, index=True)
    payment_status = Column(String(32), default=PaymentStatus.PENDING.value, nullable=False, index=True)
    fulfillment_status = Column(String(32), default=FulfillmentStatus.UNFULFILLED.value, nullable=False, index=True)
    currency = Column(String(8), default="INR", nullable=False)

    # Monetary Snapshots (High-precision Decimal)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Coupon Snapshot
    coupon_code = Column(String(64), nullable=True)
    coupon_discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Recipient & Address Snapshot (Immutable at order creation time)
    recipient_name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=False)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    landmark = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(64), default="India", nullable=False)
    postal_code = Column(String(32), nullable=False)
    address_label = Column(String(32), default="Home", nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Delivery Method & Slot
    delivery_method = Column(String(64), default="STANDARD", nullable=False)
    delivery_slot = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)

    # Reference to original CheckoutSession
    checkout_session_id = Column(
        String(36),
        ForeignKey("checkout_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="orders", lazy="selectin")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at.asc()",
        lazy="selectin",
    )
    status_history = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at.desc()",
        lazy="selectin",
    )
    checkout_session = relationship("CheckoutSession", lazy="selectin")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="chk_orders_subtotal_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_orders_total_non_negative"),
        Index("idx_orders_user_id_created_at", "user_id", "created_at"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_number", "order_number", unique=True),
        Index("idx_orders_checkout_session_id", "checkout_session_id"),
    )

    def __repr__(self) -> str:
        return f"<Order(id='{self.id}', order_number='{self.order_number}', status='{self.status}', total={self.total_amount})>"


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variant_id = Column(
        String(36),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Purchase-time Snapshots (Survives catalog modifications)
    product_name = Column(String(255), nullable=False)
    variant_name = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    unit_value = Column(String(50), nullable=True)
    unit_type = Column(String(50), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=True)
    quantity = Column(Integer, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    thumbnail_url = Column(String(1024), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", lazy="selectin")
    variant = relationship("ProductVariant", lazy="selectin")

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="chk_order_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price"),
        CheckConstraint("line_total >= 0", name="chk_order_items_line_total"),
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
        Index("idx_order_items_variant_id", "variant_id"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id='{self.id}', product_name='{self.product_name}', qty={self.quantity}, line_total={self.line_total})>"


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    changed_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_order_status_history_order_id", "order_id"),
        Index("idx_order_status_history_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OrderStatusHistory(order_id='{self.order_id}', {self.old_status} -> {self.new_status})>"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column(String(128), nullable=False)
    request_hash = Column(String(128), nullable=True)
    response_status = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
        Index("idx_idempotency_lookup", "user_id", "key"),
        Index("idx_idempotency_expires_at", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp

    def __repr__(self) -> str:
        return f"<IdempotencyRecord(key='{self.key}', user_id='{self.user_id}', status={self.response_status})>"
