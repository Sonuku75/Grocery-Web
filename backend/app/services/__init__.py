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
from app.services.inventory_service import InventoryService
from app.services.notification_service import NotificationService
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.notification_template_service import NotificationTemplateService
from app.services.review_service import ReviewService
from app.services.review_eligibility_service import ReviewEligibilityService
from app.services.review_moderation_service import ReviewModerationService
from app.services.review_aggregation_service import ReviewAggregationService
from app.services.security_event_service import SecurityEventService
from app.services.profile_service import ProfileService
from app.services.session_service import SessionService
from app.services.account_deletion_service import AccountDeletionService
from app.services.account_service import AccountService

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
    "InventoryService",
    "NotificationService",
    "NotificationPreferenceService",
    "NotificationTemplateService",
    "ReviewService",
    "ReviewEligibilityService",
    "ReviewModerationService",
    "ReviewAggregationService",
    "SecurityEventService",
    "ProfileService",
    "SessionService",
    "AccountDeletionService",
    "AccountService",
]


