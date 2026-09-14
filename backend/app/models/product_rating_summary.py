"""
Cartify Product Rating Summary Model (Module 14)

Derived, transactional rating aggregation per product:
- Stores total reviews, authoritative average rating (Decimal), and star counts (1-5)
- Rebuilt from database reviews source of truth
- Provides instant rating queries for product catalog and details without expensive GROUP BYs
"""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProductRatingSummary(Base):
    __tablename__ = "product_rating_summaries"

    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    total_reviews = Column(Integer, default=0, nullable=False)
    average_rating = Column(Numeric(3, 2), default=Decimal("0.00"), nullable=False)
    rating_1_count = Column(Integer, default=0, nullable=False)
    rating_2_count = Column(Integer, default=0, nullable=False)
    rating_3_count = Column(Integer, default=0, nullable=False)
    rating_4_count = Column(Integer, default=0, nullable=False)
    rating_5_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="rating_summary")

    __table_args__ = (
        CheckConstraint("total_reviews >= 0", name="chk_rating_summary_total_reviews"),
        CheckConstraint("average_rating >= 0 AND average_rating <= 5", name="chk_rating_summary_avg_range"),
        CheckConstraint(
            "rating_1_count >= 0 AND rating_2_count >= 0 AND rating_3_count >= 0 AND rating_4_count >= 0 AND rating_5_count >= 0",
            name="chk_rating_summary_counts_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return f"<ProductRatingSummary(product_id='{self.product_id}', avg={self.average_rating}, total={self.total_reviews})>"
