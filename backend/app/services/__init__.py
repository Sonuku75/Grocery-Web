"""
Cartify Services Registry (Module 2)
"""

from app.services.auth import AuthService
from app.services.user import UserService
from app.services.address import AddressService
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService
from app.services.delivery_fee_service import DeliveryFeeService
from app.services.pricing_service import PricingService
from app.services.checkout_service import CheckoutService
from app.services.order_service import OrderService

__all__ = [
    "AuthService",
    "UserService",
    "AddressService",
    "CartService",
    "CouponService",
    "DeliveryFeeService",
    "PricingService",
    "CheckoutService",
    "OrderService",
]

