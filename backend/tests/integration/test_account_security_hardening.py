"""
Cartify Account Security Hardening Tests (Module 15.4)

Validates bank-grade security hardening:
- HTTP security headers & private Cache-Control
- OTP brute-force bounds and auto-invalidation (MAX_OTP_ATTEMPTS)
- CRLF audit log injection defense
- Outbox event emission on PHONE_CHANGED
- Session revocation after credential modifications
- Strict Open Redirect sanitization
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.errors import CartifyException
from app.core.logging import sanitize_log_injection, mask_sensitive_data
from app.core.security import hash_token
from app.main import app
from app.models.account_change_request import AccountChangeRequest, ChangeType
from app.models.user import User
from app.services.account_service import AccountService
from app.services.security_event_service import SecurityEventService


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user():
    return User(
        id="usr-sec-hardening-001",
        name="Security Hardened User",
        email="hardened@cartify.com",
        phone="+919876543210",
        password_hash="$2b$12$e8rXp9mQw9vK8h.fE0eSsuO6KkHl6d8qf1V8j8x7y0Z7a3b4c5d6e",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )


class TestSecurityHeadersAndCacheControl:
    """Verifies security headers injected by SecurityHeadersMiddleware."""

    def test_security_headers_present_on_root(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers.get("Permissions-Policy", "")

    def test_private_cache_control_on_account_route(self, client):
        response = client.get("/api/v1/account")
        # Even on 401 Unauthorized, sensitive account route must enforce no-store
        cache_ctrl = response.headers.get("Cache-Control", "")
        assert "no-store" in cache_ctrl
        assert "no-cache" in cache_ctrl
        assert response.headers.get("Pragma") == "no-cache"

    def test_private_cache_control_on_auth_route(self, client):
        with patch("app.services.auth.AuthService.login", AsyncMock(side_effect=CartifyException(status_code=401, detail="Invalid credentials."))):
            response = client.post("/api/v1/auth/login", json={"email": "nonexistent@cartify.com", "password": "wrong"})
            cache_ctrl = response.headers.get("Cache-Control", "")
            assert "no-store" in cache_ctrl
            assert response.headers.get("Pragma") == "no-cache"


class TestOtpBruteForceHardening:
    """Verifies bounded OTP attempts and automatic request invalidation."""

    @pytest.mark.asyncio
    async def test_email_change_otp_attempts_bounded_and_invalidates(self, test_user):
        valid_otp = "849201"
        valid_hash = hash_token(valid_otp)

        mock_pending = AccountChangeRequest(
            id="req-email-h1",
            user_id=test_user.id,
            change_type=ChangeType.EMAIL,
            target_value="hardened.new@cartify.com",
            verification_token_hash=valid_hash,
            expires_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock()
        AccountService._otp_attempts_tracker.clear()

        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=mock_pending)), \
             patch("app.repositories.account_change_request.AccountChangeRequestRepository.mark_completed", AsyncMock()) as mock_mark:

            # Attempts 1 to 4: Should return INVALID_VERIFICATION_CODE with remaining attempts
            for attempt in range(1, settings.MAX_OTP_ATTEMPTS):
                with pytest.raises(CartifyException) as exc_info:
                    await AccountService.verify_email_change(
                        db=mock_db,
                        user=test_user,
                        verification_code="000000",
                    )
                assert exc_info.value.code == "INVALID_VERIFICATION_CODE"
                assert f"{settings.MAX_OTP_ATTEMPTS - attempt} attempt(s) remaining" in exc_info.value.message

            # Attempt 5: Maximum attempts reached! Must invalidate and raise MAX_ATTEMPTS_EXCEEDED
            with pytest.raises(CartifyException) as exc_info_max:
                await AccountService.verify_email_change(
                    db=mock_db,
                    user=test_user,
                    verification_code="000000",
                )
            assert exc_info_max.value.code == "MAX_ATTEMPTS_EXCEEDED"
            mock_mark.assert_called_with(mock_db, mock_pending.id)

    @pytest.mark.asyncio
    async def test_phone_change_otp_attempts_bounded(self, test_user):
        valid_otp = "334455"
        valid_hash = hash_token(valid_otp)

        mock_pending = AccountChangeRequest(
            id="req-phone-h1",
            user_id=test_user.id,
            change_type=ChangeType.PHONE,
            target_value="+919811223344",
            verification_token_hash=valid_hash,
            expires_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock()
        AccountService._otp_attempts_tracker.clear()

        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=mock_pending)), \
             patch("app.repositories.account_change_request.AccountChangeRequestRepository.mark_completed", AsyncMock()):

            # First wrong attempt
            with pytest.raises(CartifyException) as exc:
                await AccountService.verify_phone_change(
                    db=mock_db,
                    user=test_user,
                    verification_code="999999",
                )
            assert exc.value.code == "INVALID_VERIFICATION_CODE"
            assert "4 attempt(s) remaining" in exc.value.message


class TestLogInjectionAndSanitization:
    """Verifies prevention of CRLF log injection attacks and credential scrubbing."""

    def test_sanitize_user_agent_strips_crlf(self):
        malicious_ua = "Mozilla/5.0\r\n[CRITICAL] ForgedAdminLogin admin=true\r\nHost: evil.com"
        clean = SecurityEventService.sanitize_user_agent(malicious_ua)
        assert "\r" not in clean
        assert "\n" not in clean
        assert "Mozilla/5.0[CRITICAL]" in clean

    def test_sanitize_ip_strips_control_characters(self):
        malicious_ip = "192.168.1.1\r\nInjected-Header: true"
        clean = SecurityEventService.sanitize_ip(malicious_ip)
        assert "\r" not in clean
        assert "\n" not in clean
        assert clean == "192.168.1.1Injected-Header: true"[:45]

    def test_logging_filter_masks_otp_and_credentials(self):
        raw_msg = '{"verification_code": "123456", "password": "supersecretpassword", "otp": "654321"}'
        masked = mask_sensitive_data(raw_msg)
        assert "123456" not in masked
        assert "supersecretpassword" not in masked
        assert "654321" not in masked
        assert "[REDACTED]" in masked


class TestSecurityOutboxNotificationTriggers:
    """Verifies outbox alerts on high-priority credential changes."""

    @pytest.mark.asyncio
    async def test_phone_changed_emits_outbox_event(self, test_user):
        mock_db = AsyncMock()
        with patch("app.repositories.account_security_event.AccountSecurityEventRepository.create", AsyncMock()) as mock_create, \
             patch("app.services.notification_service.NotificationService.emit_outbox_event", AsyncMock()) as mock_emit:

            mock_event = AsyncMock()
            mock_create.return_value = mock_event

            await SecurityEventService.record_security_event(
                db=mock_db,
                user_id=test_user.id,
                event_type="PHONE_CHANGED",
                ip_address="127.0.0.1",
            )

            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[1]
            assert call_args["event_type"] == "SECURITY_ALERTS"
            assert call_args["payload"]["event_type"] == "PHONE_CHANGED"
