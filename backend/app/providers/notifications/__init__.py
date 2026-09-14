"""
Notification Providers Module (Module 13)
"""

from app.providers.notifications.base import (
    DeliveryResult,
    EmailProvider,
    PushNotificationProvider,
    SMSProvider,
)
from app.providers.notifications.mock_email import MockEmailProvider
from app.providers.notifications.mock_sms import MockSMSProvider
from app.providers.notifications.mock_push import MockPushNotificationProvider
from app.providers.notifications.factory import (
    get_email_provider,
    get_push_provider,
    get_sms_provider,
)

__all__ = [
    "DeliveryResult",
    "EmailProvider",
    "SMSProvider",
    "PushNotificationProvider",
    "MockEmailProvider",
    "MockSMSProvider",
    "MockPushNotificationProvider",
    "get_email_provider",
    "get_sms_provider",
    "get_push_provider",
]
