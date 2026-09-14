"""
Cartify User Session Model (Module 15.1)

Persists active user sessions for device management and session revocation.
Never stores raw session tokens or secrets — only cryptographic SHA-256 hashes.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class UserSession(Base):
    """
    Active customer session record for multi-device visibility and granular revocation.
    """
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_identifier = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    device_name = Column(String(100), nullable=True)
    platform = Column(String(30), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    last_seen_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_user_sessions_lookup", "user_id", "revoked_at", "expires_at"),
        Index("ix_user_sessions_identifier", "session_identifier"),
    )
