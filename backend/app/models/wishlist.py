"""
Cartify WishlistItem Model (Module 6)

Stores product-level wishlist favorites per customer:
- Scoped to user_id (ForeignKey to users.id with ON DELETE CASCADE)
- References product_id (ForeignKey to products.id with ON DELETE CASCADE)
- Enforces database-level uniqueness via uq_wishlist_user_product (user_id, product_id)
- Composite keyset pagination index on (user_id, created_at DESC, id DESC)
- Eager relationship loading for high-performance catalog rendering
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
        Index("idx_wishlist_keyset", "user_id", "created_at", "id"),
    )
