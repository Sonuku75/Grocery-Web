"""
Cartify Pricing Service (Module 9)

Centralized authoritative pricing and order calculation engine:
- Computes subtotal with Decimal precision
- Derives coupon discount via CouponService
- Derives delivery fee via DeliveryFeeService
- Guarantees: total = max(0, subtotal - discount + delivery_fee + tax)
- Fully reusable across Checkout, future Orders, Invoices, and Payments
"""

from decimal import Decimal
from typing import Any, List, NamedTuple, Optional

from app.models.coupon import Coupon
from app.services.coupon_service import CouponService
from app.services.delivery_fee_service import DeliveryFeeService


class PricingBreakdown(NamedTuple):
    subtotal: Decimal
    discount: Decimal
    delivery_fee: Decimal
    tax: Decimal
    total: Decimal


class PricingService:
    @classmethod
    def calculate_totals(
        cls,
        subtotal: Decimal,
        coupon: Optional[Coupon] = None,
        delivery_method: str = "STANDARD",
        tax_rate: Decimal = Decimal("0.00"),
    ) -> PricingBreakdown:
        """
        Calculates authoritative totals for a checkout session or order.
        """
        subtotal_dec = Decimal(str(subtotal)).quantize(Decimal("0.01"))

        if subtotal_dec <= Decimal("0.00"):
            return PricingBreakdown(
                subtotal=Decimal("0.00"),
                discount=Decimal("0.00"),
                delivery_fee=Decimal("0.00"),
                tax=Decimal("0.00"),
                total=Decimal("0.00"),
            )

        # 1. Discount via CouponService
        if coupon:
            discount_dec = CouponService.calculate_discount(coupon, subtotal_dec)
        else:
            discount_dec = Decimal("0.00")

        # 2. Delivery Fee via DeliveryFeeService
        delivery_fee_dec = DeliveryFeeService.calculate_delivery_fee(
            subtotal=subtotal_dec, delivery_method=delivery_method
        )

        # 3. Tax calculation
        tax_dec = (subtotal_dec * tax_rate).quantize(Decimal("0.01"))

        # 4. Final Total
        payable = subtotal_dec - discount_dec + delivery_fee_dec + tax_dec
        total_dec = max(Decimal("0.00"), payable).quantize(Decimal("0.01"))

        return PricingBreakdown(
            subtotal=subtotal_dec,
            discount=discount_dec,
            delivery_fee=delivery_fee_dec,
            tax=tax_dec,
            total=total_dec,
        )
