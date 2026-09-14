"""
Cartify Review Report Model (Module 14)

Foundation for review moderation and customer abuse reporting:
- Reasons: SPAM, OFFENSIVE, FAKE_REVIEW, MISLEADING, PERSONAL_INFORMATION, OTHER
- Statuses: PENDING, REVIEWED, DISMISSED, ACTION_TAKEN
- Unique constraint (review_id, user_id) throttles abusive repeated reporting by a single user
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class ReportReason(str, Enum):
    SPAM = "SPAM"
    OFFENSIVE = "OFFENSIVE"
    FAKE_REVIEW = "FAKE_REVIEW"
    MISLEADING = "MISLEADING"
    PERSONAL_INFORMATION = "PERSONAL_INFORMATION"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"
    ACTION_TAKEN = "ACTION_TAKEN"


class ReviewReport(Base, TimestampMixin):
    __tablename__ = "review_reports"

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
    reason = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(
        String(32),
        default=ReportStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Relationships
    review = relationship("Review", back_populates="reports")
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_reports_review_user"),
        Index("idx_review_reports_review_id", "review_id"),
        Index("idx_review_reports_user_id", "user_id"),
        Index("idx_review_reports_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ReviewReport(id='{self.id}', review_id='{self.review_id}', reason='{self.reason}', status='{self.status}')>"
