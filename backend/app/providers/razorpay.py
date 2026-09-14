"""
Razorpay Payment Provider Adapter (Module 12)

Production-grade adapter for Razorpay API:
- HMAC-SHA256 signature verification for payment callback and webhooks
- Paired currency conversion (rupees to paise subunits)
- Constant-time verification against timing attacks
- Safe error handling without leaking secrets or credentials
"""

import hashlib
import hmac
from decimal import Decimal
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.core.security_redaction import safe_str_cmp
from app.providers.base import PaymentProvider


class PaymentGatewayError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=502, error_code="PAYMENT_GATEWAY_ERROR", details=details)


class RazorpayPaymentProvider(PaymentProvider):
    """
    Adapter integrating Razorpay Orders, Payments, Webhooks, and Refunds APIs.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"

    @property
    def provider_name(self) -> str:
        return "RAZORPAY"

    def _ensure_credentials(self) -> None:
        if not self.key_id or not self.key_secret:
            raise PaymentGatewayError("Razorpay credentials are not configured on the server.")

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._ensure_credentials()
        # Convert INR amount to paise integer subunit
        amount_paise = int(round(amount * 100))

        payload = {
            "amount": amount_paise,
            "currency": currency.upper(),
            "receipt": receipt,
            "notes": notes or {},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/orders",
                    auth=(self.key_id, self.key_secret),
                    json=payload,
                )
                if response.status_code not in (200, 201):
                    raise PaymentGatewayError(
                        f"Razorpay order creation failed: {response.status_code}",
                        details={"response": response.text},
                    )
                data = response.json()
                return {
                    "provider_order_id": data["id"],
                    "amount": amount,
                    "currency": data["currency"],
                    "receipt": data.get("receipt"),
                    "metadata": {"razorpay_order": data},
                }
            except httpx.RequestError as exc:
                raise PaymentGatewayError(f"Razorpay gateway unreachable: {str(exc)}")

    async def fetch_payment(self, provider_payment_id: str) -> Dict[str, Any]:
        self._ensure_credentials()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/payments/{provider_payment_id}",
                    auth=(self.key_id, self.key_secret),
                )
                if response.status_code != 200:
                    raise PaymentGatewayError(
                        f"Failed to fetch Razorpay payment: {response.status_code}",
                        details={"response": response.text},
                    )
                data = response.json()
                amount_inr = Decimal(str(data.get("amount", 0))) / Decimal("100")
                return {
                    "provider_payment_id": data["id"],
                    "status": data.get("status"),
                    "amount": amount_inr,
                    "currency": data.get("currency", "INR"),
                    "method": data.get("method"),
                    "metadata": data,
                }
            except httpx.RequestError as exc:
                raise PaymentGatewayError(f"Razorpay payment fetch error: {str(exc)}")

    def verify_signature(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> bool:
        if not self.key_secret or not signature or not provider_order_id or not provider_payment_id:
            return False

        message = f"{provider_order_id}|{provider_payment_id}".encode("utf-8")
        expected_sig = hmac.new(
            self.key_secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()

        return safe_str_cmp(signature, expected_sig)

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        if not self.webhook_secret or not signature_header or not payload_bytes:
            return False

        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return safe_str_cmp(signature_header, expected_sig)

    async def initiate_refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._ensure_credentials()
        amount_paise = int(round(amount * 100))
        payload = {
            "amount": amount_paise,
            "notes": notes or {},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/payments/{provider_payment_id}/refund",
                    auth=(self.key_id, self.key_secret),
                    json=payload,
                )
                if response.status_code not in (200, 201):
                    raise PaymentGatewayError(
                        f"Razorpay refund initiation failed: {response.status_code}",
                        details={"response": response.text},
                    )
                data = response.json()
                return {
                    "provider_refund_id": data["id"],
                    "amount": amount,
                    "currency": currency,
                    "status": "processed" if data.get("status") == "processed" else "pending",
                    "notes": notes or {},
                }
            except httpx.RequestError as exc:
                raise PaymentGatewayError(f"Razorpay refund request error: {str(exc)}")

    async def fetch_refund(self, provider_refund_id: str) -> Dict[str, Any]:
        self._ensure_credentials()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/refunds/{provider_refund_id}",
                    auth=(self.key_id, self.key_secret),
                )
                if response.status_code != 200:
                    raise PaymentGatewayError(f"Failed to fetch refund: {response.status_code}")
                data = response.json()
                return {
                    "provider_refund_id": data["id"],
                    "status": data.get("status"),
                }
            except httpx.RequestError as exc:
                raise PaymentGatewayError(f"Razorpay refund fetch error: {str(exc)}")
