"""
Cartify Product Variant Model (Module 4)

Purchasable configuration of a product:
- Unique SKU (uppercase-normalized, non-empty, indexed)
- Unit representation (unit_value e.g. 500, unit_type e.g. "ml", "kg", "g", "litre", "pack")
- Authoritative INR pricing (price, mrp stored as Numeric(10, 2))
- Check constraint enforcing price >= 0, mrp >= 0, price <= mrp
- Authoritative backend discount_percentage
- Explicitly excludes inventory fields (stock_quantity deferred to Module 11)
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    unit_value = Column(Numeric(10, 2), nullable=False)
    unit_type = Column(String(32), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory = relationship("Inventory", back_populates="variant", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_variant_price_non_negative"),
        CheckConstraint("mrp >= 0", name="chk_variant_mrp_non_negative"),
        CheckConstraint("price <= mrp", name="chk_variant_price_le_mrp"),
        Index("idx_variants_prod_active_sort", "product_id", "is_active", "sort_order"),
    )

    # Frontend camelCase compatibility properties
    @property
    def productId(self) -> str:
        return self.product_id

    @property
    def unitValue(self) -> float:
        return float(self.unit_value) if self.unit_value is not None else 0.0

    @property
    def unitType(self) -> str:
        return self.unit_type

    @property
    def discountPercentage(self) -> int:
        return self.discount_percentage

    @property
    def isActive(self) -> bool:
        return self.is_active

    @property
    def sortOrder(self) -> int:
        return self.sort_order

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, sku='{self.sku}', name='{self.name}', price={self.price})>"
