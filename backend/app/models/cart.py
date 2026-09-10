from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint, Index
from app.models.base import Base, TimestampMixin, generate_uuid

class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True)

    __table_args__ = (
        Index("idx_cart_user", "user_id"),
    )

class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    cart_id = Column(String(64), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_cart_item_quantity_positive"),
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        Index("idx_cart_items_cart_id", "cart_id"),
    )
