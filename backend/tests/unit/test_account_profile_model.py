"""
Cartify Account & Profile Model Unit Tests (Module 15.1)

Verifies database model definitions, relationships, enums, and constraint declarations.
"""

from datetime import date, datetime, timezone
import pytest

from app.models.account_change_request import AccountChangeRequest, ChangeType
from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus
from app.models.account_security_event import AccountSecurityEvent, AccountSecurityEventType
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_session import UserSession


class TestAccountProfileModels:
    def test_user_profile_instantiation(self):
        """UserProfile can be instantiated with valid fields."""
        profile = UserProfile(
            user_id="usr-123",
            date_of_birth=date(1995, 5, 15),
            bio="Organic food enthusiast",
        )
        assert profile.user_id == "usr-123"
        assert profile.date_of_birth == date(1995, 5, 15)
        assert profile.bio == "Organic food enthusiast"

    def test_account_security_event_instantiation(self):
        """AccountSecurityEvent model correctly holds event metadata without credentials."""
        event = AccountSecurityEvent(
            user_id="usr-123",
            event_type=AccountSecurityEventType.LOGIN_SUCCESS,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0 Test Browser",
            request_id="req-abc-123",
            metadata_json={"auth_method": "password"},
        )
        assert event.user_id == "usr-123"
        assert event.event_type == AccountSecurityEventType.LOGIN_SUCCESS
        assert event.metadata_json == {"auth_method": "password"}

    def test_user_session_instantiation(self):
        """UserSession stores SHA-256 session identifier and device info."""
        now = datetime.now(timezone.utc)
        session = UserSession(
            user_id="usr-123",
            session_identifier="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            device_name="Chrome on Windows",
            platform="WINDOWS",
            ip_address="10.0.0.1",
            expires_at=now,
        )
        assert session.user_id == "usr-123"
        assert len(session.session_identifier) == 64
        assert session.platform == "WINDOWS"
        assert session.revoked_at is None

    def test_account_deletion_request_instantiation(self):
        """AccountDeletionRequest initializes with PENDING status and scheduled time."""
        now = datetime.now(timezone.utc)
        req = AccountDeletionRequest(
            user_id="usr-123",
            status=AccountDeletionStatus.PENDING,
            scheduled_at=now,
            reason="Switching service",
        )
        assert req.status == AccountDeletionStatus.PENDING
        assert req.reason == "Switching service"
        assert req.completed_at is None
        assert req.cancelled_at is None

    def test_account_change_request_instantiation(self):
        """AccountChangeRequest tracks staged email/phone changes."""
        now = datetime.now(timezone.utc)
        change_req = AccountChangeRequest(
            user_id="usr-123",
            change_type=ChangeType.EMAIL,
            target_value="newemail@example.com",
            verification_token_hash="hash123",
            expires_at=now,
            is_verified=False,
        )
        assert change_req.change_type == ChangeType.EMAIL
        assert change_req.target_value == "newemail@example.com"
        assert change_req.is_verified is False

    def test_user_relationships_exist(self):
        """User model exposes Module 15.1 relationships."""
        user = User(
            id="usr-123",
            name="Vikram Seth",
            email="vikram@cartify.com",
            password_hash="fakehash",
        )
        assert hasattr(user, "profile")
        assert hasattr(user, "security_events")
        assert hasattr(user, "sessions")
        assert hasattr(user, "deletion_requests")
        assert hasattr(user, "change_requests")
