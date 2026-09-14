"""
Mock SMS Provider (Module 13)

Deterministic sandbox provider for SMS delivery testing.
Validates Indian mobile formats (+91, 10-digit formats).
"""

import hmac
import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.security_redaction import safe_str_cmp
from app.providers.notifications.base import DeliveryResult, SMSProvider


class MockSMSProvider(SMSProvider):
    """
    In-memory mock SMS provider.
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or settings.NOTIFICATION_WEBHOOK_SECRET
        self.sent_messages: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "MOCK_SMS"

    def clear(self) -> None:
        self.sent_messages.clear()

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """
        Validates standard mobile phone format. Supports Indian 10-digit mobile format:
        Optional +91 or 91, followed by 10 digits starting with 6-9.
        """
        if not phone:
            return False
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10 and digits[0] in "6789":
            return True
        if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
            return True
        return False

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        metadata = metadata or {}

        # 1. Phone validation
        if not self.is_valid_phone(phone_number):
            return DeliveryResult(
                success=False,
                failure_code="INVALID_PHONE_NUMBER",
                failure_message=f"Phone number failed validation: {phone_number}",
                is_transient=False,
            )

        # 2. Magic test triggers
        magic_action = metadata.get("magic_action")
        if magic_action == "FORCE_PERMANENT_FAIL":
            return DeliveryResult(
                success=False,
                failure_code="UNSUBSCRIBED_RECIPIENT",
                failure_message="Simulated DND or unsubscribed number",
                is_transient=False,
            )
        elif magic_action == "FORCE_TRANSIENT_FAIL":
            return DeliveryResult(
                success=False,
                failure_code="TELCO_CONGESTION",
                failure_message="Simulated telecom network congestion",
                is_transient=True,
            )

        # 3. Successful SMS dispatch
        msg_id = f"mock_sms_{uuid.uuid4().hex[:12]}"
        self.sent_messages.append({
            "id": msg_id,
            "to": phone_number,
            "message": message,
            "template_id": template_id,
            "metadata": metadata,
        })

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
