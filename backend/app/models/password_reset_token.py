"""
Cartify Password Reset Token Model (Module 1)

Persists single-use cryptographically hashed reset tokens with strict 15-minute expiration.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("idx_pwd_reset_tokens_user", "user_id"),
        Index("idx_pwd_reset_tokens_hash", "token_hash"),
    )
