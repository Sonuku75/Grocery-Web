"""
Payment Provider Factory (Module 12)

Dynamic registry and instantiation for payment gateway providers.
"""

from typing import Optional
from app.core.config import settings
from app.core.errors import ValidationError
from app.providers.base import PaymentProvider
from app.providers.mock import MockPaymentProvider
from app.providers.razorpay import RazorpayPaymentProvider

_mock_instance = MockPaymentProvider()


def get_payment_provider(provider_type: Optional[str] = None) -> PaymentProvider:
    """
    Returns an instance of the requested PaymentProvider or the system default.
    """
    selected = (provider_type or settings.PAYMENT_PROVIDER_DEFAULT or "mock").strip().lower()

    if selected in {"mock", "sandbox"}:
        return _mock_instance
    elif selected == "razorpay":
        return RazorpayPaymentProvider()
    else:
        raise ValidationError(f"Unsupported payment provider: '{provider_type}'")
