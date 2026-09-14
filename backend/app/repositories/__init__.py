"""
Cartify Repositories Package (Module 2)
"""
from app.repositories.user import UserRepository
from app.repositories.address import AddressRepository
from app.repositories.category import CategoryRepository
from app.repositories.cart import CartRepository
from app.repositories.coupon import CouponRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.order import OrderRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.notification import (
    NotificationRepository,
    NotificationDeliveryRepository,
)
from app.repositories.notification_preference import NotificationPreferenceRepository
from app.repositories.user_device import UserDeviceRepository
from app.repositories.notification_outbox import NotificationOutboxRepository
from app.repositories.notification_template import NotificationTemplateRepository
from app.repositories.notification_webhook import NotificationWebhookRepository
from app.repositories.review import ReviewRepository
from app.repositories.review_helpful_vote import ReviewHelpfulVoteRepository
from app.repositories.review_report import ReviewReportRepository
from app.repositories.product_rating_summary import ProductRatingSummaryRepository

__all__ = [
    "UserRepository",
    "AddressRepository",
    "CategoryRepository",
    "CartRepository",
    "CouponRepository",
    "CheckoutRepository",
    "OrderRepository",
    "InventoryRepository",
    "NotificationRepository",
    "NotificationDeliveryRepository",
    "NotificationPreferenceRepository",
    "UserDeviceRepository",
    "NotificationOutboxRepository",
    "NotificationTemplateRepository",
    "NotificationWebhookRepository",
    "ReviewRepository",
    "ReviewHelpfulVoteRepository",
    "ReviewReportRepository",
    "ProductRatingSummaryRepository",
]


