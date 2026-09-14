"""
Cartify Account Deletion Request Model (Module 15.1)

Tracks user requests for account deletion through a non-destructive lifecycle.
Preserves historical business records (orders, transactions, reviews) while
supporting privacy rights and grace period cancellation.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class AccountDeletionStatus(str, Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class AccountDeletionRequest(Base, TimestampMixin):
    """
    Account deletion request record.
    """
    __tablename__ = "account_deletion_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        default=AccountDeletionStatus.PENDING,
        nullable=False,
    )
    reason = Column(String(255), nullable=True)
    requested_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="deletion_requests")

    __table_args__ = (
        Index("ix_account_deletion_user_status", "user_id", "status"),
    )
