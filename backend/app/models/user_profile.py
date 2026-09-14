"""
Cartify User Profile Model (Module 15.1)

Stores non-authentication profile extensions while strictly minimizing PII.
No government IDs, biometric data, or sensitive financial information are collected.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class UserProfile(Base, TimestampMixin):
    """
    Extended user profile for personalization.
    Reuses users table for primary auth and contact info (name, email, phone).
    """
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    date_of_birth = Column(Date, nullable=True)
    bio = Column(String(500), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="profile")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        Index("ix_user_profiles_user_id", "user_id"),
    )
