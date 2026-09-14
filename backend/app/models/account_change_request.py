"""
Cartify Account Change Request Model (Module 15.1)

Staged verification for sensitive account attribute changes (email, phone).
Prevents immediate unverified client overwrites and protects against account takeover.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class ChangeType(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"


class AccountChangeRequest(Base):
    """
    Pending verification record for email/phone updates.
    """
    __tablename__ = "account_change_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_type = Column(String(20), nullable=False)
    target_value = Column(String(255), nullable=False)
    verification_token_hash = Column(String(64), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship back to User
    user = relationship("User", back_populates="change_requests")

    __table_args__ = (
        Index("ix_account_change_user_type", "user_id", "change_type", "is_verified"),
    )
