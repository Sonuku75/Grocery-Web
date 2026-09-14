"""
Mock Email Provider (Module 13)

Deterministic sandbox provider for local testing and automated verification.
Supports failure injection, transient simulation, and message inspection.
"""

import hmac
import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.security_redaction import safe_str_cmp
from app.providers.notifications.base import DeliveryResult, EmailProvider


class MockEmailProvider(EmailProvider):
    """
    In-memory mock email provider. Never contacts external networks.
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or settings.NOTIFICATION_WEBHOOK_SECRET
        self.sent_messages: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "MOCK_EMAIL"

    def clear(self) -> None:
        """Clears sent messages history for test isolation."""
        self.sent_messages.clear()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        metadata = metadata or {}

        # 1. Check permanent recipient error
        if not to_email or "@" not in to_email or "." not in to_email:
            return DeliveryResult(
                success=False,
                failure_code="INVALID_RECIPIENT",
                failure_message=f"Invalid email address: {to_email}",
                is_transient=False,
            )

        # 2. Magic test triggers
        magic_action = metadata.get("magic_action")
        if "FORCE_PERMANENT_FAIL" in to_email or magic_action == "FORCE_PERMANENT_FAIL":
            return DeliveryResult(
                success=False,
                failure_code="RECIPIENT_BLOCKED",
                failure_message="Simulated permanent recipient bounce",
                is_transient=False,
            )
        elif "FORCE_TRANSIENT_FAIL" in to_email or magic_action == "FORCE_TRANSIENT_FAIL":
            return DeliveryResult(
                success=False,
                failure_code="GATEWAY_TIMEOUT",
                failure_message="Simulated temporary SMTP connection timeout",
                is_transient=True,
            )

        # 3. Successful delivery simulation
        msg_id = f"mock_email_{uuid.uuid4().hex[:12]}"
        record = {
            "id": msg_id,
            "to": to_email,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "metadata": metadata,
        }
        self.sent_messages.append(record)

        return DeliveryResult(
            success=True,
            provider_message_id=msg_id,
            metadata={"simulated_at": "now"},
        )

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        if not self.webhook_secret or not signature_header:
            return False
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return safe_str_cmp(expected, signature_header)
