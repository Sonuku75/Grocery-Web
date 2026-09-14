"""
Notification Provider Factory (Module 13)

Resolves provider adapters dynamically based on configuration.
"""

from typing import Dict
from app.core.config import settings
from app.providers.notifications.base import (
    EmailProvider,
    PushNotificationProvider,
    SMSProvider,
)
from app.providers.notifications.mock_email import MockEmailProvider
from app.providers.notifications.mock_sms import MockSMSProvider
from app.providers.notifications.mock_push import MockPushNotificationProvider

_cached_email_providers: Dict[str, EmailProvider] = {}
_cached_sms_providers: Dict[str, SMSProvider] = {}
_cached_push_providers: Dict[str, PushNotificationProvider] = {}


def get_email_provider(provider_type: str = "") -> EmailProvider:
    provider_name = (provider_type or settings.NOTIFICATION_EMAIL_PROVIDER).lower()
    if provider_name not in _cached_email_providers:
        # Currently default is mock. Production adapters (SendGrid, SES) can be added here
        _cached_email_providers[provider_name] = MockEmailProvider()
    return _cached_email_providers[provider_name]


def get_sms_provider(provider_type: str = "") -> SMSProvider:
    provider_name = (provider_type or settings.NOTIFICATION_SMS_PROVIDER).lower()
    if provider_name not in _cached_sms_providers:
        _cached_sms_providers[provider_name] = MockSMSProvider()
    return _cached_sms_providers[provider_name]


def get_push_provider(provider_type: str = "") -> PushNotificationProvider:
    provider_name = (provider_type or settings.NOTIFICATION_PUSH_PROVIDER).lower()
    if provider_name not in _cached_push_providers:
        _cached_push_providers[provider_name] = MockPushNotificationProvider()
    return _cached_push_providers[provider_name]
