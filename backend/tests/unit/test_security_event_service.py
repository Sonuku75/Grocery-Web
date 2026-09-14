"""
Cartify Security Event Service Unit Tests (Module 15.1)

Tests security event auditing, credential scrubbing, PII minimization, and alert dispatch.
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.models.account_security_event import AccountSecurityEvent
from app.services.security_event_service import SecurityEventService


class TestSecurityEventService:
    def test_redact_sensitive_dict_scrubs_passwords_and_tokens(self):
        """Recursively redacts passwords, tokens, hashes, and secrets from audit metadata."""
        raw_meta = {
            "user_id": "usr-1",
            "password": "supersecretpassword",
            "access_token": "eyJhbGciOi...",
            "refresh_token_hash": "a1b2c3...",
            "auth_header": "Bearer xyz",
            "card_number": "4111222233334444",
            "nested": {
                "user_password": "nestedpassword",
                "safe_field": "12345",
            },
        }

        scrubbed = SecurityEventService.redact_sensitive_dict(raw_meta)
        assert scrubbed["user_id"] == "usr-1"
        assert scrubbed["password"] == "[REDACTED]"
        assert scrubbed["access_token"] == "[REDACTED]"
        assert scrubbed["refresh_token_hash"] == "[REDACTED]"
        assert scrubbed["auth_header"] == "[REDACTED]"
        assert scrubbed["card_number"] == "[REDACTED]"
        assert scrubbed["nested"]["user_password"] == "[REDACTED]"
        assert scrubbed["nested"]["safe_field"] == "12345"

    def test_sanitize_ip_and_user_agent(self):
        """Sanitizes whitespace and truncates oversized strings."""
        assert SecurityEventService.sanitize_ip("   192.168.1.1   ") == "192.168.1.1"
        assert SecurityEventService.sanitize_ip(None) is None

        long_ua = "A" * 1000
        clean_ua = SecurityEventService.sanitize_user_agent(long_ua)
        assert len(clean_ua) == 512

    def test_mask_ip_for_display(self):
        """Masks IP octets for safe client-facing privacy display."""
        assert SecurityEventService.mask_ip_for_display("192.168.10.45") == "192.168.*.*"
        assert SecurityEventService.mask_ip_for_display("2001:db8:85a3:8d3:1319:8a2e:370:7348") == "2001:db8:*:*"
        assert SecurityEventService.mask_ip_for_display(None) is None

    @pytest.mark.asyncio
    async def test_record_security_event_persists_and_emits_outbox(self):
        """Recording critical security events triggers outbox notification dispatch."""
        mock_db = AsyncMock()
        mock_event = AccountSecurityEvent(
            id="evt-1",
            user_id="usr-1",
            event_type="PASSWORD_CHANGED",
        )

        with patch("app.repositories.account_security_event.AccountSecurityEventRepository.create", AsyncMock(return_value=mock_event)), \
             patch("app.services.notification_service.NotificationService.emit_outbox_event", AsyncMock()) as mock_outbox:

            result = await SecurityEventService.record_security_event(
                db=mock_db,
                user_id="usr-1",
                event_type="PASSWORD_CHANGED",
                ip_address="192.168.1.5",
                user_agent="Test Browser",
                metadata={"reason": "routine_update", "password": "should_be_scrubbed"},
            )

            assert result.event_type == "PASSWORD_CHANGED"
            mock_outbox.assert_called_once()
