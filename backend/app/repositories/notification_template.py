"""
Notification Template Repository (Module 13)

Manages templating catalogs with variable allowlists and multi-channel formatting.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    NotificationChannel,
    NotificationTemplate,
    NotificationType,
)


DEFAULT_TEMPLATES: List[Dict[str, Any]] = [
    # ORDER_CREATED
    {
        "key": NotificationType.ORDER_CREATED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Order Placed Successfully",
        "body_template": "Your order #{{order_number}} for {{total_amount}} has been placed.",
        "allowed_variables": ["order_number", "total_amount", "customer_name", "item_count"],
    },
    {
        "key": NotificationType.ORDER_CREATED.value,
        "channel": NotificationChannel.EMAIL.value,
        "subject": "Cartify Order Confirmation: #{{order_number}}",
        "title_template": "Order Confirmed!",
        "body_template": "<p>Hi {{customer_name}},</p><p>Thank you for shopping with Cartify! We have received your order <strong>#{{order_number}}</strong> totaling <strong>{{total_amount}}</strong>.</p>",
        "allowed_variables": ["order_number", "total_amount", "customer_name", "item_count"],
    },
    {
        "key": NotificationType.ORDER_CREATED.value,
        "channel": NotificationChannel.SMS.value,
        "subject": None,
        "title_template": "Cartify Order",
        "body_template": "Order #{{order_number}} placed successfully. Amount: {{total_amount}}. Track your order on Cartify.",
        "allowed_variables": ["order_number", "total_amount"],
    },
    {
        "key": NotificationType.ORDER_CREATED.value,
        "channel": NotificationChannel.PUSH.value,
        "subject": None,
        "title_template": "Order Placed!",
        "body_template": "Your order #{{order_number}} is confirmed.",
        "allowed_variables": ["order_number", "total_amount"],
    },

    # ORDER_CONFIRMED
    {
        "key": NotificationType.ORDER_CONFIRMED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Order Confirmed",
        "body_template": "Your order #{{order_number}} has been confirmed and is being packed.",
        "allowed_variables": ["order_number", "customer_name"],
    },

    # ORDER_SHIPPED
    {
        "key": NotificationType.ORDER_SHIPPED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Order On The Way",
        "body_template": "Your order #{{order_number}} has been packed and dispatched.",
        "allowed_variables": ["order_number", "customer_name"],
    },
    {
        "key": NotificationType.ORDER_SHIPPED.value,
        "channel": NotificationChannel.SMS.value,
        "subject": None,
        "title_template": "Order Dispatched",
        "body_template": "Your Cartify order #{{order_number}} has been dispatched and will arrive shortly.",
        "allowed_variables": ["order_number"],
    },

    # ORDER_DELIVERED
    {
        "key": NotificationType.ORDER_DELIVERED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Order Delivered",
        "body_template": "Your order #{{order_number}} has been successfully delivered. Enjoy your fresh groceries!",
        "allowed_variables": ["order_number", "customer_name"],
    },

    # ORDER_CANCELLED
    {
        "key": NotificationType.ORDER_CANCELLED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Order Cancelled",
        "body_template": "Your order #{{order_number}} has been cancelled. Any payments made will be refunded.",
        "allowed_variables": ["order_number", "reason"],
    },

    # PAYMENT_SUCCESS
    {
        "key": NotificationType.PAYMENT_SUCCESS.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Payment Successful",
        "body_template": "Payment of {{amount}} for order #{{order_number}} was successfully verified.",
        "allowed_variables": ["order_number", "amount", "payment_method"],
    },
    {
        "key": NotificationType.PAYMENT_SUCCESS.value,
        "channel": NotificationChannel.EMAIL.value,
        "subject": "Payment Receipt for Order #{{order_number}}",
        "title_template": "Payment Verified",
        "body_template": "<p>We have successfully processed your payment of <strong>{{amount}}</strong> via {{payment_method}} for order #{{order_number}}.</p>",
        "allowed_variables": ["order_number", "amount", "payment_method", "customer_name"],
    },

    # PAYMENT_FAILED
    {
        "key": NotificationType.PAYMENT_FAILED.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Payment Failed",
        "body_template": "Payment for order #{{order_number}} could not be completed. Please retry.",
        "allowed_variables": ["order_number", "amount", "reason"],
    },

    # REFUND_SUCCESS
    {
        "key": NotificationType.REFUND_SUCCESS.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Refund Processed",
        "body_template": "A refund of {{amount}} for order #{{order_number}} has been initiated.",
        "allowed_variables": ["order_number", "amount"],
    },

    # WELCOME
    {
        "key": NotificationType.WELCOME.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Welcome to Cartify!",
        "body_template": "Hi {{customer_name}}, welcome to Cartify! Fresh groceries and essentials delivered in 15 minutes.",
        "allowed_variables": ["customer_name"],
    },

    # PASSWORD_RESET
    {
        "key": NotificationType.PASSWORD_RESET.value,
        "channel": NotificationChannel.EMAIL.value,
        "subject": "Reset Your Cartify Password",
        "title_template": "Password Reset Request",
        "body_template": "<p>Hi {{customer_name}},</p><p>We received a request to reset your password. Click the link below to set a new password:</p><p><a href=\"{{reset_url}}\">Reset Password</a></p><p>This link expires in {{expiry_minutes}} minutes.</p>",
        "allowed_variables": ["customer_name", "reset_url", "expiry_minutes"],
    },

    # SECURITY_ALERT
    {
        "key": NotificationType.SECURITY_ALERT.value,
        "channel": NotificationChannel.IN_APP.value,
        "subject": None,
        "title_template": "Security Alert",
        "body_template": "Your account security settings or password were changed recently.",
        "allowed_variables": ["customer_name", "event_time"],
    },
    {
        "key": NotificationType.SECURITY_ALERT.value,
        "channel": NotificationChannel.EMAIL.value,
        "subject": "Cartify Security Alert: Account Activity",
        "title_template": "Security Notice",
        "body_template": "<p>Hi {{customer_name}},</p><p>Important account activity was detected on your Cartify profile. If you did not make this change, please contact support immediately.</p>",
        "allowed_variables": ["customer_name", "event_time"],
    },
]


class NotificationTemplateRepository:
    """Repository for notification templates."""

    @staticmethod
    async def get_template(
        db: AsyncSession,
        key: str,
        channel: str,
        locale: str = "en-IN",
    ) -> Optional[NotificationTemplate]:
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.key == key,
            NotificationTemplate.channel == channel,
            NotificationTemplate.locale == locale,
            NotificationTemplate.is_active == True,
        ).order_by(NotificationTemplate.version.desc())
        res = await db.execute(stmt)
        template = res.scalar_one_or_none()
        if not template:
            # Check default templates in-memory
            for d in DEFAULT_TEMPLATES:
                if d["key"] == key and d["channel"] == channel:
                    template = NotificationTemplate(
                        key=d["key"],
                        channel=d["channel"],
                        subject=d["subject"],
                        title_template=d["title_template"],
                        body_template=d["body_template"],
                        locale=locale,
                        version=1,
                        is_active=True,
                        allowed_variables=d["allowed_variables"],
                    )
                    db.add(template)
                    await db.flush()
                    return template
        return template

    @classmethod
    async def get_template_by_code(
        cls,
        db: AsyncSession,
        key: str,
        channel: str,
        locale: str = "en-IN",
    ) -> Optional[NotificationTemplate]:
        return await cls.get_template(db=db, key=key, channel=channel, locale=locale)

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[NotificationTemplate]:
        stmt = (
            select(NotificationTemplate)
            .order_by(NotificationTemplate.key.asc(), NotificationTemplate.channel.asc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        templates = list(res.scalars().all())
        if not templates:
            # Seed default templates
            for d in DEFAULT_TEMPLATES:
                tmpl = NotificationTemplate(
                    key=d["key"],
                    channel=d["channel"],
                    subject=d["subject"],
                    title_template=d["title_template"],
                    body_template=d["body_template"],
                    locale="en-IN",
                    version=1,
                    is_active=True,
                    allowed_variables=d["allowed_variables"],
                )
                db.add(tmpl)
                templates.append(tmpl)
            await db.flush()
        return templates
