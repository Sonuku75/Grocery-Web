"""
Cartify Category Model (Module 3)

Self-referencing hierarchical taxonomy for categories and subcategories:
- parent_id = NULL indicates a top-level category
- parent_id = category_id indicates a subcategory
- Self-referencing parent/children relationships with cascade
- Composite indexes supporting high-frequency customer browse queries
"""

from typing import List, Optional
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(64), nullable=True, default="Compass")
    image_url = Column(String(1024), nullable=True)
    parent_id = Column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    # Self-referencing relationships
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Category.sort_order.asc(), Category.name.asc()",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_categories_active_sort", "is_active", "sort_order", "name"),
        Index("idx_categories_parent_active", "parent_id", "is_active", "sort_order"),
    )

    # Compatibility properties for frontend camelCase / legacy fields
    @property
    def imageUrl(self) -> Optional[str]:
        return self.image_url

    @property
    def parentId(self) -> Optional[str]:
        return self.parent_id

    @property
    def isActive(self) -> bool:
        return self.is_active

    @property
    def sortOrder(self) -> int:
        return self.sort_order

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}', parent_id={self.parent_id})>"

