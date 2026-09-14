"""
Notification Provider Base Interfaces (Module 13)

Abstract contracts defining operations for external notification gateways:
- EmailProvider
- SMSProvider
- PushNotificationProvider
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class DeliveryResult:
    """Standardized delivery result returned by all channel providers."""
    success: bool
    provider_message_id: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    is_transient: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmailProvider(ABC):
    """Abstract interface for transactional email providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'MOCK_EMAIL', 'SENDGRID', 'AWS_SES')."""
        pass

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """Dispatches an email message asynchronously."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """Verifies inbound delivery receipt webhook signature."""
        pass


class SMSProvider(ABC):
    """Abstract interface for transactional SMS providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'MOCK_SMS', 'TWILIO', 'MSG91')."""
        pass

    @abstractmethod
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """Dispatches an SMS message asynchronously."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """Verifies inbound SMS delivery receipt webhook signature."""
        pass


class PushNotificationProvider(ABC):
    """Abstract interface for mobile and web push notification providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'MOCK_PUSH', 'FCM', 'APNS')."""
        pass

    @abstractmethod
    async def send_push(
        self,
        device_token: str,
        platform: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """Dispatches a push notification to a specific device."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """Verifies inbound push receipt webhook signature."""
        pass
