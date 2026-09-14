"""
Base Payment Provider Interface (Module 12)

Abstract contract defining operations required by all external payment gateways
(e.g., Razorpay, Stripe, Mock/Sandbox). Enforces provider-agnostic business logic.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional


class PaymentProvider(ABC):
    """
    Abstract interface for payment gateway adapters.
    All implementations must handle amounts cleanly and perform constant-time cryptographic checks.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the identifier name of this provider (e.g., 'MOCK', 'RAZORPAY')."""
        pass

    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates an upstream gateway order or transaction session.
        Returns a dictionary containing at least 'provider_order_id' and 'metadata'.
        """
        pass

    @abstractmethod
    async def fetch_payment(self, provider_payment_id: str) -> Dict[str, Any]:
        """
        Retrieves payment status and captured amount directly from the provider.
        """
        pass

    @abstractmethod
    def verify_signature(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verifies customer-submitted payment completion signature using constant-time comparison.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """
        Verifies inbound webhook signature using raw body bytes and constant-time comparison.
        """
        pass

    @abstractmethod
    async def initiate_refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiates a full or partial refund with the gateway.
        Returns a dictionary containing 'provider_refund_id' and 'status'.
        """
        pass

    @abstractmethod
    async def fetch_refund(self, provider_refund_id: str) -> Dict[str, Any]:
        """
        Fetches the current status of an initiated refund from the gateway.
        """
        pass
