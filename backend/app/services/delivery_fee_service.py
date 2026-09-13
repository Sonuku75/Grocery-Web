"""
Cartify Delivery Fee Service (Module 9)

Centralized, authoritative server-side delivery fee calculation abstraction:
- Decoupled from controller and frontend components
- Configurable free delivery threshold (default ₹499.00) and standard fee (₹40.00)
- High-precision Decimal arithmetic
"""

from decimal import Decimal
from app.core.config import settings


class DeliveryFeeService:
    @classmethod
    def calculate_delivery_fee(
        cls, subtotal: Decimal, delivery_method: str = "STANDARD"
    ) -> Decimal:
        """
        Calculates the authoritative delivery fee based on cart subtotal and delivery method.
        Free delivery rule: subtotal >= settings.FREE_DELIVERY_THRESHOLD -> ₹0.00
        Otherwise: settings.STANDARD_DELIVERY_FEE
        """
        subtotal_dec = Decimal(str(subtotal))
        if subtotal_dec <= Decimal("0.00"):
            return Decimal("0.00")

        free_threshold = Decimal(str(settings.FREE_DELIVERY_THRESHOLD))
        if subtotal_dec >= free_threshold:
            return Decimal("0.00")

        standard_fee = Decimal(str(settings.STANDARD_DELIVERY_FEE)).quantize(Decimal("0.01"))
        return standard_fee
