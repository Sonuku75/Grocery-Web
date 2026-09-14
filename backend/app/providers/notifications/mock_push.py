"""
Mock Push Notification Provider (Module 13)

Deterministic sandbox provider for iOS, Android, and Web push notifications.
"""

import hmac
import hashlib
import uuid
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.security_redaction import safe_str_cmp
from app.providers.notifications.base import DeliveryResult, PushNotificationProvider


class MockPushNotificationProvider(PushNotificationProvider):
    """
    In-memory mock push provider.
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or settings.NOTIFICATION_WEBHOOK_SECRET
        self.sent_messages: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "MOCK_PUSH"

    def clear(self) -> None:
        self.sent_messages.clear()

    async def send_push(
        self,
        device_token: str,
        platform: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        data = data or {}

        # 1. Token validation
        if not device_token or len(device_token.strip()) < 10:
            return DeliveryResult(
                success=False,
                failure_code="INVALID_DEVICE_TOKEN",
                failure_message="Device token is malformed or too short",
                is_transient=False,
            )

        # 2. Magic test triggers
        magic_action = data.get("magic_action")
        if magic_action == "FORCE_PERMANENT_FAIL" or device_token.startswith("invalid_"):
            return DeliveryResult(
                success=False,
                failure_code="UNREGISTERED_DEVICE",
                failure_message="Device token unregistered with APNs/FCM",
                is_transient=False,
            )
        elif magic_action == "FORCE_TRANSIENT_FAIL":
            return DeliveryResult(
                success=False,
                failure_code="FCM_UNAVAILABLE",
                failure_message="Simulated temporary gateway throttling",
                is_transient=True,
            )

        # 3. Successful push dispatch
        msg_id = f"mock_push_{uuid.uuid4().hex[:12]}"
        self.sent_messages.append({
            "id": msg_id,
            "device_token": device_token,
            "platform": platform,
            "title": title,
            "body": body,
            "data": data,
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
