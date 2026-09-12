"""
Cartify Product Model (Module 4)

Top-level product catalog model:
- References category hierarchy (categories.id) with ON DELETE RESTRICT
- Contains common product metadata (name, slug, brand, description, short_description)
- Primary thumbnail (image_url) for rapid catalog rendering
- Status flags (is_active, is_featured)
- Has many product variants and product images
- Keyset pagination index on (is_active, created_at, id)
"""

from typing import Optional, List
from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(
        String(36),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    brand = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    image_url = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    category = relationship("Category", lazy="selectin")
    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.sort_order.asc(), ProductVariant.price.asc()",
        lazy="selectin",
    )
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order.asc()",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_products_cat_active_featured", "category_id", "is_active", "is_featured"),
        Index("idx_products_brand_active", "brand", "is_active"),
        Index("idx_products_keyset", "is_active", "created_at", "id"),
    )

    # Frontend camelCase compatibility properties
    @property
    def categoryId(self) -> str:
        return self.category_id

    @property
    def shortDescription(self) -> Optional[str]:
        return self.short_description

    @property
    def imageUrl(self) -> Optional[str]:
        return self.image_url

    @property
    def isActive(self) -> bool:
        return self.is_active

    @property
    def isFeatured(self) -> bool:
        return self.is_featured

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', slug='{self.slug}', brand='{self.brand}')>"
