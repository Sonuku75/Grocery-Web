"""
Cartify Review Model (Module 14)

Database model for customer reviews and ratings:
- Strict ratings between 1 and 5 stars
- Moderation lifecycle: PENDING -> PUBLISHED, REJECTED, HIDDEN, DELETED
- One review per purchased order line item enforced via database uniqueness
- Authoritative verified-purchase flags and helpful vote counts
- Soft-deletion support via deleted_at
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    HIDDEN = "HIDDEN"
    DELETED = "DELETED"


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

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
    order_id = Column(
        String(36),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_item_id = Column(
        String(36),
        ForeignKey("order_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    rating = Column(Integer, nullable=False)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(
        String(32),
        default=ReviewStatus.PUBLISHED.value,
        nullable=False,
        index=True,
    )
    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="reviews", lazy="selectin")
    product = relationship("Product", back_populates="reviews", lazy="selectin")
    order = relationship("Order", back_populates="reviews", lazy="selectin")
    order_item = relationship("OrderItem", back_populates="review", lazy="selectin")
    helpful_votes = relationship(
        "ReviewHelpfulVote",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reports = relationship(
        "ReviewReport",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_reviews_rating_range"),
        CheckConstraint("helpful_count >= 0", name="chk_reviews_helpful_count_non_negative"),
        UniqueConstraint("order_item_id", name="uq_reviews_order_item_id"),
        UniqueConstraint("user_id", "product_id", "order_id", name="uq_reviews_user_product_order"),
        Index("idx_reviews_product_status", "product_id", "status"),
        Index("idx_reviews_product_rating", "product_id", "rating"),
        Index("idx_reviews_product_created", "product_id", "created_at"),
        Index("idx_reviews_user_created", "user_id", "created_at"),
        Index("idx_reviews_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Review(id='{self.id}', product_id='{self.product_id}', rating={self.rating}, status='{self.status}')>"
