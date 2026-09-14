"""
Mock Payment Provider (Module 12)

Deterministic sandbox implementation of PaymentProvider for local development,
integration tests, and automated CI pipelines without external network calls.
"""

import hashlib
import hmac
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from app.core.security_redaction import safe_str_cmp
from app.providers.base import PaymentProvider


MOCK_SECRET_KEY = "cartify_mock_provider_secret_2026"
MOCK_WEBHOOK_SECRET = "cartify_mock_webhook_secret_2026"


class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for zero-dependency local testing.
    Supports failure simulation when provider_payment_id starts with 'pay_fail_'.
    """

    @property
    def provider_name(self) -> str:
        return "MOCK"

    @staticmethod
    def generate_mock_signature(order_id: str, payment_id: str) -> str:
        """Helper to generate a valid mock signature for tests."""
        message = f"{order_id}|{payment_id}".encode("utf-8")
        return hmac.new(
            MOCK_SECRET_KEY.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def generate_mock_webhook_signature(payload_bytes: bytes) -> str:
        """Helper to generate a valid mock webhook signature for tests."""
        return hmac.new(
            MOCK_WEBHOOK_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        unique_suffix = uuid.uuid4().hex[:16]
        provider_order_id = f"mock_order_{unique_suffix}"
        return {
            "provider_order_id": provider_order_id,
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
            "metadata": {
                "sandbox": True,
                "provider": "MOCK",
            },
        }

    async def fetch_payment(self, provider_payment_id: str) -> Dict[str, Any]:
        if provider_payment_id.startswith("pay_fail_"):
            return {
                "provider_payment_id": provider_payment_id,
                "status": "failed",
                "failure_code": "MOCK_PAYMENT_FAILED",
                "failure_message": "Mock payment declined by simulator.",
                "amount": Decimal("0.00"),
                "currency": "INR",
            }

        return {
            "provider_payment_id": provider_payment_id,
            "status": "captured",
            "amount": Decimal("100.00"),
            "currency": "INR",
            "method": "upi",
        }

    def verify_signature(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> bool:
        if not signature or not provider_order_id or not provider_payment_id:
            return False

        # Reject explicitly simulated failure tokens
        if provider_payment_id.startswith("pay_fail_") or signature == "mock_invalid_signature":
            return False

        # Fast path test bypass
        if safe_str_cmp(signature, "mock_valid_signature"):
            return True

        expected_sig = self.generate_mock_signature(provider_order_id, provider_payment_id)
        return safe_str_cmp(signature, expected_sig)

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        if not signature_header:
            return False

        if safe_str_cmp(signature_header, "mock_webhook_sig"):
            return True

        expected_sig = self.generate_mock_webhook_signature(payload_bytes)
        return safe_str_cmp(signature_header, expected_sig)

    async def initiate_refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if provider_payment_id.startswith("pay_refund_fail_"):
            return {
                "provider_refund_id": None,
                "status": "failed",
                "failure_message": "Simulated mock refund failure",
            }

        provider_refund_id = f"mock_rfnd_{uuid.uuid4().hex[:16]}"
        return {
            "provider_refund_id": provider_refund_id,
            "amount": amount,
            "currency": currency,
            "status": "processed",
            "notes": notes or {},
        }

    async def fetch_refund(self, provider_refund_id: str) -> Dict[str, Any]:
        return {
            "provider_refund_id": provider_refund_id,
            "status": "processed",
        }
