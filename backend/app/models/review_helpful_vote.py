"""
Cartify Review Helpful Vote Model (Module 14)

Tracks customer helpful votes on reviews:
- Unique constraint (review_id, user_id) prevents duplicate votes per user
- Server atomically increments / decrements helpful_count on Review model
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class ReviewHelpfulVote(Base):
    __tablename__ = "review_helpful_votes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    review_id = Column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    review = relationship("Review", back_populates="helpful_votes")
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_helpful_votes_review_user"),
        Index("idx_helpful_votes_review_id", "review_id"),
        Index("idx_helpful_votes_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<ReviewHelpfulVote(id='{self.id}', review_id='{self.review_id}', user_id='{self.user_id}')>"
