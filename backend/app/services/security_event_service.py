"""
Cartify Security Event Service (Module 15.1)

Centralizes immutable security event auditing, PII minimization, and credential scrubbing.
Guarantees that passwords, raw tokens, reset tokens, or auth headers are NEVER persisted.
"""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_security_event import AccountSecurityEvent
from app.repositories.account_security_event import AccountSecurityEventRepository

logger = logging.getLogger("cartify.security_event")

# Sensitive keys to redact unconditionally from any audit metadata
SENSITIVE_KEY_PATTERNS = (
    r"password",
    r"token",
    r"secret",
    r"hash",
    r"otp",
    r"auth",
    r"authorization",
    r"bearer",
    r"cookie",
    r"card",
    r"cvv",
    r"pin",
)


class SecurityEventService:
    @classmethod
    def redact_sensitive_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Recursively scrubs any keys resembling sensitive credentials or tokens.
        """
        if not data or not isinstance(data, dict):
            return None

        scrubbed = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(re.search(pat, k_lower) for pat in SENSITIVE_KEY_PATTERNS):
                scrubbed[k] = "[REDACTED]"
            elif isinstance(v, dict):
                scrubbed[k] = cls.redact_sensitive_dict(v)
            elif isinstance(v, list):
                scrubbed[k] = [
                    cls.redact_sensitive_dict(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                scrubbed[k] = v
        return scrubbed

    @classmethod
    def sanitize_ip(cls, ip_address: Optional[str]) -> Optional[str]:
        """Sanitizes and limits IP address string to 45 characters, stripping control characters."""
        if not ip_address:
            return None
        cleaned = re.sub(r"[\r\n\x00-\x1f\x7f]", "", ip_address).strip()
        return cleaned[:45] if cleaned else None

    @classmethod
    def sanitize_user_agent(cls, user_agent: Optional[str]) -> Optional[str]:
        """Sanitizes and truncates User-Agent string to 512 characters, stripping CRLF log injection."""
        if not user_agent:
            return None
        cleaned = re.sub(r"[\r\n\x00-\x1f\x7f]", "", user_agent).strip()
        return cleaned[:512] if cleaned else None

    @classmethod
    def mask_ip_for_display(cls, ip_address: Optional[str]) -> Optional[str]:
        """
        Masks IP address for customer display to protect privacy (e.g. 192.168.*.*).
        """
        if not ip_address:
            return None
        parts = ip_address.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        # For IPv6, show first 2 segments
        v6_parts = ip_address.split(":")
        if len(v6_parts) > 2:
            return f"{v6_parts[0]}:{v6_parts[1]}:*:*"
        return "Protected IP"

    @classmethod
    async def record_security_event(
        cls,
        db: AsyncSession,
        user_id: str,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AccountSecurityEvent:
        """
        Persists a sanitized security audit event and logs structured output.
        """
        clean_ip = cls.sanitize_ip(ip_address)
        clean_ua = cls.sanitize_user_agent(user_agent)
        scrubbed_meta = cls.redact_sensitive_dict(metadata)

        event = await AccountSecurityEventRepository.create(
            db=db,
            user_id=user_id,
            event_type=event_type,
            ip_address=clean_ip,
            user_agent=clean_ua,
            request_id=request_id,
            metadata_json=scrubbed_meta,
        )

        logger.info(
            f"[SECURITY_EVENT] user={user_id} event={event_type} "
            f"ip={clean_ip} req={request_id}"
        )

        # Emit outbox notification for high-priority security alerts
        if event_type in (
            "PASSWORD_CHANGED",
            "EMAIL_CHANGED",
            "PHONE_CHANGED",
            "ACCOUNT_DELETION_REQUESTED",
            "ALL_SESSIONS_REVOKED",
        ):
            try:
                from app.services.notification_service import NotificationService
                await NotificationService.emit_outbox_event(
                    db=db,
                    event_type="SECURITY_ALERTS",
                    aggregate_type="USER",
                    aggregate_id=user_id,
                    user_id=user_id,
                    payload={
                        "user_id": user_id,
                        "event_type": event_type,
                        "ip_address": clean_ip,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            except Exception as ex:
                logger.warning(f"Could not emit outbox security event: {ex}")

        return event
