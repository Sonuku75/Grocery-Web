"""
Cartify Inventory & Inventory Transaction Models (Module 11)

Variant-level stock management, reservations, low-stock detection, and audit transactions:
- Strict single inventory row per ProductVariant with foreign key and unique constraint
- Server-side check constraints:
  - quantity >= 0
  - reserved_quantity >= 0
  - low_stock_threshold >= 0
  - reserved_quantity <= quantity
- Computed authoritative available_quantity = quantity - reserved_quantity
- Immutable transaction audit log tracking every inventory mutation with actor and references
"""

from datetime import datetime, timezone
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
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class InventoryTransactionType(str, Enum):
    INITIAL = "INITIAL"
    RESTOCK = "RESTOCK"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGE = "DAMAGE"
    RETURN = "RETURN"
    RESERVATION = "RESERVATION"
    RELEASE = "RELEASE"
    CANCELLATION = "CANCELLATION"


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    variant_id = Column(
        String(36),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    variant = relationship("ProductVariant", back_populates="inventory")
    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
        order_by="desc(InventoryTransaction.created_at)",
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="chk_inventory_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_inventory_reserved_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="chk_inventory_low_stock_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="chk_inventory_reserved_le_quantity"),
        Index("idx_inventory_variant_active", "variant_id", "is_active"),
        Index("idx_inventory_qty_reserved", "quantity", "reserved_quantity"),
    )

    @property
    def available_quantity(self) -> int:
        """Authoritative available stock for purchase."""
        return max(0, (self.quantity or 0) - (self.reserved_quantity or 0))

    @property
    def is_low_stock(self) -> bool:
        """True if available stock has reached or fallen below low_stock_threshold."""
        return self.available_quantity <= (self.low_stock_threshold or 0)

    @property
    def is_out_of_stock(self) -> bool:
        """True if no units are available or inventory is inactive."""
        return not self.is_active or self.available_quantity <= 0

    @property
    def is_available(self) -> bool:
        """True if inventory is active and has available units."""
        return self.is_active and self.available_quantity > 0


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inventory_id = Column(
        String(36),
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id = Column(
        String(36),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(String(32), nullable=False, index=True)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(64), nullable=True)
    reason = Column(String(255), nullable=True)
    created_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")
    variant = relationship("ProductVariant")
    created_by = relationship("User")

    __table_args__ = (
        Index("idx_inv_trans_variant_created", "variant_id", "created_at"),
        Index("idx_inv_trans_ref", "reference_type", "reference_id"),
        Index("idx_inv_trans_type", "transaction_type"),
    )
