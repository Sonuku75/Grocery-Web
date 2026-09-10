from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    JSON,
    text,
)
from app.models.base import Base, TimestampMixin, generate_uuid

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    # Idempotency token to guarantee client retries never double-order
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    
    status = Column(String(32), default="order_placed", nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0.0, nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=0.0, nullable=False)
    tax = Column(Numeric(10, 2), default=0.0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    
    delivery_address = Column(JSON, nullable=False)
    delivery_slot = Column(String(128), default="15 Minutes", nullable=False)
    payment_method = Column(String(64), default="card", nullable=False)
    payment_status = Column(String(32), default="pending", nullable=False)

    __table_args__ = (
        Index("idx_order_user_created", "user_id", "created_at"),
        Index("idx_order_keyset", "created_at", "id"),
    )

class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    
    # Historical denormalized snapshots of product details at time of purchase
    product_name = Column(String(255), nullable=False)
    product_image = Column(String(1024), nullable=False)
    unit = Column(String(64), default="1 unit", nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
    )
