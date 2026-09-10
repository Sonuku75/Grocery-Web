from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    text,
)
from app.models.base import Base, TimestampMixin

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True)
    slug = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    brand = Column(String(128), nullable=False)
    category_id = Column(String(64), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    description = Column(Text, nullable=False)
    specifications = Column(JSON, default=dict, nullable=False)
    
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Integer, default=0, nullable=False)
    unit = Column(String(64), default="1 unit", nullable=False)
    
    # Check constraint: Stock must NEVER be negative (database-level guard against overselling)
    stock = Column(Integer, default=0, nullable=False)
    rating = Column(Numeric(3, 2), default=5.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    
    images = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    
    is_popular = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_deal = Column(Boolean, default=False, nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("stock >= 0", name="chk_products_stock_non_negative"),
        CheckConstraint("price >= 0", name="chk_products_price_non_negative"),
        
        # Composite Indexes aligned to exact query patterns
        Index("idx_product_cat_active_price", "category_id", "is_active", "price"),
        Index("idx_product_popular_active", "is_popular", "is_active"),
        Index("idx_product_deal_active_discount", "is_deal", "is_active", "discount_percent"),
        Index("idx_product_brand_active", "brand", "is_active"),
        
        # Keyset pagination index on (created_at DESC, id DESC)
        Index("idx_product_keyset", "created_at", "id"),
    )
