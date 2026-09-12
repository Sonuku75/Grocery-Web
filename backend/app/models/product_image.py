"""
Cartify Product Image Model (Module 4)

Product image gallery asset:
- Multiple images per product
- Strict ordering support (sort_order)
- Alt text for SEO and accessibility
- Single primary image per product maintained atomically by service
- URL-based storage (PostgreSQL never stores image binaries)
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url = Column(String(1024), nullable=False)
    alt_text = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    product = relationship("Product", back_populates="images")

    __table_args__ = (
        Index("idx_prod_images_prod_sort", "product_id", "sort_order"),
        Index("idx_prod_images_prod_primary", "product_id", "is_primary"),
    )

    # Frontend camelCase compatibility properties
    @property
    def productId(self) -> str:
        return self.product_id

    @property
    def imageUrl(self) -> str:
        return self.image_url

    @property
    def altText(self) -> Optional[str]:
        return self.alt_text

    @property
    def sortOrder(self) -> int:
        return self.sort_order

    @property
    def isPrimary(self) -> bool:
        return self.is_primary

    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id='{self.product_id}', is_primary={self.is_primary})>"
