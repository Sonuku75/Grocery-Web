"""
Cartify Refresh Token Model (Module 1)

Persists cryptographically hashed refresh tokens for multi-platform session management,
token rotation, and token family reuse detection.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    family_id = Column(String(36), index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_family", "family_id"),
        Index("idx_refresh_tokens_user", "user_id"),
        Index("idx_refresh_tokens_hash", "token_hash"),
    )
