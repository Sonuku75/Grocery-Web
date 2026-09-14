"""
Cartify Account Security Event Model (Module 15.1)

Audit trail foundation for account-sensitive operations and authentication events.
Strictly forbids storage of passwords, tokens, reset tokens, or raw credentials.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class AccountSecurityEventType(str, Enum):
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    EMAIL_CHANGE_REQUESTED = "EMAIL_CHANGE_REQUESTED"
    EMAIL_CHANGED = "EMAIL_CHANGED"
    PHONE_CHANGE_REQUESTED = "PHONE_CHANGE_REQUESTED"
    PHONE_CHANGED = "PHONE_CHANGED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    SESSION_REVOKED = "SESSION_REVOKED"
    ALL_SESSIONS_REVOKED = "ALL_SESSIONS_REVOKED"
    ACCOUNT_DELETION_REQUESTED = "ACCOUNT_DELETION_REQUESTED"
    ACCOUNT_DELETION_CANCELLED = "ACCOUNT_DELETION_CANCELLED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    PROFILE_UPDATED = "PROFILE_UPDATED"


class AccountSecurityEvent(Base):
    """
    Immutable security and audit log for account lifecycle events.
    """
    __tablename__ = "account_security_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    request_id = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationship back to User
    user = relationship("User", back_populates="security_events")

    __table_args__ = (
        Index("ix_account_security_events_user_created", "user_id", "created_at"),
        Index("ix_account_security_events_event_type", "event_type"),
    )
