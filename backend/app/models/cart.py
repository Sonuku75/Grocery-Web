"""
Cartify Cart & CartItem Models (Module 7)

Database models for persistent shopping carts:
- One active cart per user enforced via UNIQUE(user_id)
- Unique variant per cart enforced via UNIQUE(cart_id, variant_id)
- Bounded quantity constraint (1 <= quantity <= 99)
- References Product and ProductVariant models with ON DELETE CASCADE
- Eager loading via selectinload to eliminate N+1 queries
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    coupon_id = Column(
        String(36),
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="cart")
    coupon = relationship("Coupon", back_populates="carts", lazy="selectin")
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.created_at.asc()",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_carts_user_id"),
        Index("idx_carts_user_id", "user_id"),
        Index("idx_carts_coupon_id", "coupon_id"),
    )


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cart_id = Column(
        String(36),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id = Column(
        String(36),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, default=1, nullable=False)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", lazy="selectin")
    variant = relationship("ProductVariant", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
        CheckConstraint("quantity >= 1 AND quantity <= 99", name="chk_cart_item_quantity_range"),
        Index("idx_cart_items_cart_id", "cart_id"),
        Index("idx_cart_items_variant_id", "variant_id"),
        Index("idx_cart_items_product_id", "product_id"),
    )
