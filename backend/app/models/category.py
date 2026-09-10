from sqlalchemy import Boolean, Column, Integer, String, Text, Index
from app.models.base import Base, TimestampMixin

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id = Column(String(64), primary_key=True)
    slug = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(64), nullable=False, default="Compass")
    image_url = Column(String(1024), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_categories_active_sort", "is_active", "sort_order"),
    )
