"""
Cartify Session Service Unit Tests (Module 15.1)

Tests session creation, cryptographic token hashing, active session listings, and revocation.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.security import hash_token
from app.models.user_session import UserSession
from app.services.session_service import SessionService


class TestSessionService:
    @pytest.mark.asyncio
    async def test_create_session_stores_hash_and_returns_raw_token(self):
        """Creates a session, storing the SHA-256 hash while returning the raw token."""
        mock_db = AsyncMock()
        mock_session = UserSession(
            id="sess-123",
            user_id="usr-123",
            session_identifier="abc",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        with patch("app.repositories.user_session.UserSessionRepository.create", AsyncMock(return_value=mock_session)) as mock_create:
            session, raw_token = await SessionService.create_session(
                db=mock_db,
                user_id="usr-123",
                device_name="Safari on iPhone",
                platform="IOS",
                ip_address="10.10.10.10",
                user_agent="Mobile Safari",
            )

            assert session.id == "sess-123"
            assert len(raw_token) > 20
            # Ensure the stored identifier is the hash of the raw token
            args = mock_create.call_args[1]
            assert args["session_identifier"] == hash_token(raw_token)
            assert args["platform"] == "IOS"

    @pytest.mark.asyncio
    async def test_get_active_sessions_identifies_current_session(self):
        """Marks is_current=True for the session matching the presented raw token."""
        mock_db = AsyncMock()
        raw_current_token = "current_client_token_xyz"
        current_hash = hash_token(raw_current_token)

        s1 = UserSession(
            id="sess-1",
            user_id="usr-123",
            session_identifier=current_hash,
            device_name="Current Browser",
            platform="WEB",
            ip_address="192.168.1.10",
            last_seen_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        s2 = UserSession(
            id="sess-2",
            user_id="usr-123",
            session_identifier="other_hash_abc",
            device_name="Android Phone",
            platform="ANDROID",
            ip_address="10.0.0.1",
            last_seen_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        with patch("app.repositories.user_session.UserSessionRepository.get_active_by_user_id", AsyncMock(return_value=[s1, s2])):
            results = await SessionService.get_active_sessions(
                db=mock_db,
                user_id="usr-123",
                current_token=raw_current_token,
            )

            assert len(results) == 2
            assert results[0].id == "sess-1"
            assert results[0].is_current is True
            assert results[0].ip_address == "192.168.*.*"

            assert results[1].id == "sess-2"
            assert results[1].is_current is False

    @pytest.mark.asyncio
    async def test_revoke_session_records_security_event(self):
        """Revoking a session triggers the SESSION_REVOKED security event."""
        mock_db = AsyncMock()
        mock_session = UserSession(
            id="sess-1",
            user_id="usr-123",
            device_name="Old Tablet",
        )

        with patch("app.repositories.user_session.UserSessionRepository.get_by_id", AsyncMock(return_value=mock_session)), \
             patch("app.repositories.user_session.UserSessionRepository.revoke", AsyncMock(return_value=True)), \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event:

            revoked = await SessionService.revoke_session(
                db=mock_db,
                session_id="sess-1",
                user_id="usr-123",
            )

            assert revoked is True
            mock_sec_event.assert_called_once()
            call_kwargs = mock_sec_event.call_args[1]
            assert call_kwargs["event_type"] == "SESSION_REVOKED"
            assert call_kwargs["user_id"] == "usr-123"
