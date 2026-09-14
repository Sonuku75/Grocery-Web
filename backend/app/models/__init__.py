"""
Cartify Models Registry (Module 4)

Exports all database models for declarative mapping and Alembic migrations.
"""

from app.db.base import Base, BaseRecord, TimestampMixin, generate_uuid
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.address import Address
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_image import ProductImage
from app.models.wishlist import WishlistItem
from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon, CouponUsage, DiscountType
from app.models.checkout import CheckoutSession, CheckoutStatus
from app.models.order import (
    FulfillmentStatus,
    IdempotencyRecord,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentProviderType,
    PaymentRefund,
    PaymentStatus as PaymentTransactionStatus,
    PaymentStatusHistory,
    PaymentWebhookEvent,
    RefundStatus,
    WebhookProcessingStatus,
)
from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)
from app.models.notification_preference import (
    NotificationCategory,
    NotificationPreference,
)
from app.models.user_device import (
    DevicePlatform,
    UserDevice,
)
from app.models.notification_outbox import (
    NotificationOutboxEvent,
    OutboxStatus,
)
from app.models.notification_webhook_event import (
    NotificationWebhookEvent,
)
from app.models.review import (
    Review,
    ReviewStatus,
)
from app.models.review_helpful_vote import (
    ReviewHelpfulVote,
)
from app.models.review_report import (
    ReportReason,
    ReportStatus,
    ReviewReport,
)
from app.models.product_rating_summary import (
    ProductRatingSummary,
)

__all__ = [
    "Base",
    "BaseRecord",
    "TimestampMixin",
    "generate_uuid",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "Address",
    "Category",
    "Product",
    "ProductVariant",
    "ProductImage",
    "WishlistItem",
    "Cart",
    "CartItem",
    "Coupon",
    "CouponUsage",
    "DiscountType",
    "CheckoutSession",
    "CheckoutStatus",
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "IdempotencyRecord",
    "OrderStatus",
    "PaymentStatus",
    "FulfillmentStatus",
    "Inventory",
    "InventoryTransaction",
    "InventoryTransactionType",
    "Payment",
    "PaymentMethod",
    "PaymentProviderType",
    "PaymentRefund",
    "PaymentTransactionStatus",
    "PaymentStatusHistory",
    "PaymentWebhookEvent",
    "RefundStatus",
    "WebhookProcessingStatus",
    "Notification",
    "NotificationDelivery",
    "NotificationTemplate",
    "NotificationType",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationChannel",
    "DeliveryStatus",
    "NotificationPreference",
    "NotificationCategory",
    "UserDevice",
    "DevicePlatform",
    "NotificationOutboxEvent",
    "OutboxStatus",
    "NotificationWebhookEvent",
    "Review",
    "ReviewStatus",
    "ReviewHelpfulVote",
    "ReviewReport",
    "ReportReason",
    "ReportStatus",
    "ProductRatingSummary",
]
