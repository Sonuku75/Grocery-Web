"""
Notification Service (Module 13)

Central service orchestrating:
- In-app customer notification center queries, read status updates, and counters
- Multi-channel delivery dispatch (In-App, Email, SMS, Push)
- Push device token registration and security masking
- Transactional Outbox event emission and background batch processing
- Retry mechanism with exponential backoff and dead-letter handling
- Inbound provider delivery receipt webhook verification and status synchronization
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import BadRequestError, NotFoundError
from app.core.security_redaction import mask_device_token, safe_str_cmp
from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.models.notification_outbox import NotificationOutboxEvent, OutboxStatus
from app.models.notification_preference import NotificationCategory
from app.models.user import User
from app.models.user_device import UserDevice
from app.providers.notifications.factory import (
    get_email_provider,
    get_push_provider,
    get_sms_provider,
)
from app.repositories.notification import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.repositories.notification_outbox import NotificationOutboxRepository
from app.repositories.notification_preference import NotificationPreferenceRepository
from app.repositories.notification_template import NotificationTemplateRepository
from app.repositories.notification_webhook import NotificationWebhookRepository
from app.repositories.user_device import UserDeviceRepository
from app.schemas.device import (
    DeviceListResponse,
    DeviceResponse,
    RegisterDeviceRequest,
)
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.notification_template_service import NotificationTemplateService

logger = logging.getLogger("cartify.notifications")


class NotificationService:
    """Core domain logic for notifications and device management."""

    # --------------------------------------------------------------------------
    # In-App Customer Notification Center Operations
    # --------------------------------------------------------------------------

    @classmethod
    async def get_user_notifications(
        cls,
        db: AsyncSession,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> NotificationListResponse:
        """
        Retrieves paginated notifications for the customer with cursor pagination.
        Strictly filtered by user_id to prevent horizontal privilege escalation (IDOR).
        """
        items, total_count, unread_count, next_cursor = (
            await NotificationRepository.list_for_user(
                db=db,
                user_id=user_id,
                unread_only=unread_only,
                notification_type=notification_type,
                limit=limit,
                cursor=cursor,
            )
        )

        response_items = [NotificationResponse.model_validate(item) for item in items]
        return NotificationListResponse(
            items=response_items,
            total=total_count,
            unreadCount=unread_count,
            nextCursor=next_cursor,
        )

    @classmethod
    async def get_unread_count(cls, db: AsyncSession, user_id: str) -> UnreadCountResponse:
        """Fetch total count of unread notifications for the customer."""
        count = await NotificationRepository.count_unread(db, user_id)
        return UnreadCountResponse(unreadCount=count)

    @classmethod
    async def mark_as_read(
        cls, db: AsyncSession, notification_id: str, user_id: str
    ) -> NotificationResponse:
        """
        Marks an individual notification as read.
        Enforces IDOR check: returns NotFoundError if notification does not belong to user_id.
        """
        notification = await NotificationRepository.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=user_id,
        )
        if not notification:
            raise NotFoundError("Notification", notification_id)

        return NotificationResponse.model_validate(notification)

    @classmethod
    async def mark_all_as_read(cls, db: AsyncSession, user_id: str) -> int:
        """Marks all unread notifications for the user as read."""
        return await NotificationRepository.mark_all_as_read(db, user_id)

    @classmethod
    async def delete_notification(
        cls, db: AsyncSession, notification_id: str, user_id: str
    ) -> bool:
        """Deletes a customer notification with strict IDOR verification."""
        deleted = await NotificationRepository.delete_notification(
            db=db,
            notification_id=notification_id,
            user_id=user_id,
        )
        if not deleted:
            raise NotFoundError("Notification", notification_id)
        return True

    # --------------------------------------------------------------------------
    # Push Notification Device Registration (Web, Android, iOS)
    # --------------------------------------------------------------------------

    @classmethod
    async def register_device(
        cls,
        db: AsyncSession,
        user_id: str,
        request: RegisterDeviceRequest,
    ) -> DeviceResponse:
        """
        Registers or reactivates a push notification token.
        Token is stored encrypted/authoritatively in DB and masked for client responses.
        """
        device = await UserDeviceRepository.register_device(
            db=db,
            user_id=user_id,
            platform=request.platform,
            device_token=request.device_token,
            app_version=request.app_version,
        )

        return DeviceResponse(
            id=device.id,
            platform=device.platform,
            maskedToken=mask_device_token(device.device_token),
            appVersion=device.app_version,
            isActive=device.is_active,
            lastSeenAt=device.last_seen_at,
            createdAt=device.created_at,
        )

    @classmethod
    async def list_user_devices(
        cls, db: AsyncSession, user_id: str
    ) -> DeviceListResponse:
        """Lists active and registered devices for a customer with masked tokens."""
        devices = await UserDeviceRepository.list_for_user(db, user_id)
        return DeviceListResponse(
            items=[
                DeviceResponse(
                    id=d.id,
                    platform=d.platform,
                    maskedToken=mask_device_token(d.device_token),
                    appVersion=d.app_version,
                    isActive=d.is_active,
                    lastSeenAt=d.last_seen_at,
                    createdAt=d.created_at,
                )
                for d in devices
            ]
        )

    @classmethod
    async def deactivate_device(
        cls, db: AsyncSession, device_id: str, user_id: str
    ) -> bool:
        """Deactivates a registered push device on logout or app removal."""
        deactivated = await UserDeviceRepository.deactivate_device(
            db=db, device_id=device_id, user_id=user_id
        )
        if not deactivated:
            raise NotFoundError("Device", device_id)
        return True

    # --------------------------------------------------------------------------
    # Transactional Outbox Event Emission
    # --------------------------------------------------------------------------

    @classmethod
    async def emit_outbox_event(
        cls,
        db: AsyncSession,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> NotificationOutboxEvent:
        """
        Appends an event to the transactional outbox table within the caller's active database transaction.
        Guarantees zero dual-write anomalies and 100% atomic consistency between domain mutation and notification.
        """
        resolved_key = idempotency_key or f"{event_type}:{aggregate_id}"
        resolved_user_id = user_id or payload.get("user_id") or ""

        event = await NotificationOutboxRepository.create_event(
            db=db,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            user_id=resolved_user_id,
            payload=payload,
            idempotency_key=resolved_key,
        )
        return event

    # --------------------------------------------------------------------------
    # Outbox Dispatching & Multi-Channel Delivery
    # --------------------------------------------------------------------------

    @classmethod
    def _map_event_to_category(cls, event_type: str) -> str:
        """Maps an event_type to its notification preference category."""
        ev = event_type.upper()
        if ev.startswith("ORDER_"):
            return NotificationCategory.ORDER_UPDATES.value
        if ev.startswith("PAYMENT_") or ev.startswith("REFUND_"):
            return NotificationCategory.PAYMENT_UPDATES.value
        if ev in ("SECURITY_ALERTS", "PASSWORD_RESET", "LOGIN_ALERT"):
            return NotificationCategory.SECURITY_ALERTS.value
        if ev.startswith("PROMO") or ev.startswith("OFFER") or ev.startswith("COUPON"):
            return NotificationCategory.PROMOTIONS.value
        return NotificationCategory.ORDER_UPDATES.value

    @classmethod
    async def dispatch_event(
        cls, db: AsyncSession, event: NotificationOutboxEvent
    ) -> bool:
        """
        Dispatches an outbox event to all applicable channels based on preferences.
        Returns True if all attempted deliveries succeeded or were handled.
        Returns False if a transient failure occurred and should be retried.
        """
        user_id = event.user_id
        category = cls._map_event_to_category(event.event_type)
        payload = event.payload or {}

        # Look up recipient user if user_id is set
        recipient_user: Optional[User] = None
        if user_id:
            user_stmt = select(User).where(User.id == user_id)
            user_res = await db.execute(user_stmt)
            recipient_user = user_res.scalar_one_or_none()

        recipient_email = payload.get("email") or (recipient_user.email if recipient_user else None)
        recipient_phone = payload.get("phone") or (recipient_user.phone if recipient_user else None)

        transient_error = False

        # Channel 1: In-App Notification
        in_app_enabled = (
            await NotificationPreferenceService.is_channel_enabled(
                db, user_id, category, NotificationChannel.IN_APP.value
            )
            if user_id
            else False
        )
        created_notification_id: Optional[str] = None
        if in_app_enabled and user_id:
            try:
                rendered = await NotificationTemplateService.get_rendered_template(
                    db, event.event_type, NotificationChannel.IN_APP, payload
                )
                notif = await NotificationRepository.create_notification(
                    db=db,
                    user_id=user_id,
                    type=event.event_type,
                    title=rendered["title"],
                    body=rendered["body"],
                    data=payload,
                    priority=NotificationPriority.HIGH.value
                    if category == NotificationCategory.SECURITY_ALERTS.value
                    else NotificationPriority.MEDIUM.value,
                    reference_key=f"outbox_{event.id}",
                )
                created_notification_id = notif.id

                # Record in-app delivery
                delivery = await NotificationDeliveryRepository.create_delivery(
                    db=db,
                    notification_id=notif.id,
                    user_id=user_id,
                    channel=NotificationChannel.IN_APP.value,
                    provider="SYSTEM_IN_APP",
                    status=DeliveryStatus.DELIVERED.value,
                )
                await NotificationDeliveryRepository.update_delivery_status(
                    db=db,
                    delivery_id=delivery.id,
                    status=DeliveryStatus.DELIVERED.value,
                    delivered_at=datetime.now(timezone.utc),
                )
            except Exception as e:
                logger.error("Failed to create in-app notification: %s", str(e))

        fallback_notification_id = created_notification_id or event.id

        # Channel 2: Email
        email_enabled = (
            await NotificationPreferenceService.is_channel_enabled(
                db, user_id, category, NotificationChannel.EMAIL.value
            )
            if user_id
            else bool(recipient_email)
        )
        if email_enabled and recipient_email:
            try:
                provider = get_email_provider()
                rendered = await NotificationTemplateService.get_rendered_template(
                    db, event.event_type, NotificationChannel.EMAIL, payload
                )
                delivery = await NotificationDeliveryRepository.create_delivery(
                    db=db,
                    notification_id=fallback_notification_id,
                    user_id=user_id or "ANONYMOUS",
                    channel=NotificationChannel.EMAIL.value,
                    provider=provider.provider_name,
                    status=DeliveryStatus.PENDING.value,
                )
                result = await provider.send_email(
                    to_email=recipient_email,
                    subject=rendered["title"],
                    body_html=rendered.get("html_content") or rendered["body"],
                    body_text=rendered["body"],
                    metadata={"outbox_id": event.id, "delivery_id": delivery.id},
                )
                if result.success:
                    await NotificationDeliveryRepository.update_delivery_status(
                        db=db,
                        delivery_id=delivery.id,
                        status=DeliveryStatus.DELIVERED.value,
                        provider_message_id=result.provider_message_id,
                    )
                else:
                    await NotificationDeliveryRepository.update_delivery_status(
                        db=db,
                        delivery_id=delivery.id,
                        status=DeliveryStatus.FAILED.value,
                        failure_code=result.failure_code,
                        failure_message=result.failure_message,
                    )
                    if result.is_transient:
                        transient_error = True
            except Exception as e:
                logger.error("Email dispatch failed for event %s: %s", event.id, str(e))
                transient_error = True

        # Channel 3: SMS
        sms_enabled = (
            await NotificationPreferenceService.is_channel_enabled(
                db, user_id, category, NotificationChannel.SMS.value
            )
            if user_id
            else bool(recipient_phone)
        )
        if sms_enabled and recipient_phone:
            try:
                sms_provider = get_sms_provider()
                rendered = await NotificationTemplateService.get_rendered_template(
                    db, event.event_type, NotificationChannel.SMS, payload
                )
                delivery = await NotificationDeliveryRepository.create_delivery(
                    db=db,
                    notification_id=fallback_notification_id,
                    user_id=user_id or "ANONYMOUS",
                    channel=NotificationChannel.SMS.value,
                    provider=sms_provider.provider_name,
                    status=DeliveryStatus.PENDING.value,
                )
                sms_result = await sms_provider.send_sms(
                    phone_number=recipient_phone,
                    message=rendered["body"],
                    metadata={"outbox_id": event.id, "delivery_id": delivery.id},
                )
                if sms_result.success:
                    await NotificationDeliveryRepository.update_delivery_status(
                        db=db,
                        delivery_id=delivery.id,
                        status=DeliveryStatus.DELIVERED.value,
                        provider_message_id=sms_result.provider_message_id,
                    )
                else:
                    await NotificationDeliveryRepository.update_delivery_status(
                        db=db,
                        delivery_id=delivery.id,
                        status=DeliveryStatus.FAILED.value,
                        failure_code=sms_result.failure_code,
                        failure_message=sms_result.failure_message,
                    )
                    if sms_result.is_transient:
                        transient_error = True
            except Exception as e:
                logger.error("SMS dispatch failed for event %s: %s", event.id, str(e))
                transient_error = True

        # Channel 4: Push Notifications
        push_enabled = (
            await NotificationPreferenceService.is_channel_enabled(
                db, user_id, category, NotificationChannel.PUSH.value
            )
            if user_id
            else False
        )
        if push_enabled and user_id:
            try:
                active_devices = await UserDeviceRepository.get_active_devices_for_user(db, user_id)
                if active_devices:
                    push_provider = get_push_provider()
                    rendered = await NotificationTemplateService.get_rendered_template(
                        db, event.event_type, NotificationChannel.PUSH, payload
                    )
                    for dev in active_devices:
                        delivery = await NotificationDeliveryRepository.create_delivery(
                            db=db,
                            notification_id=fallback_notification_id,
                            user_id=user_id,
                            channel=NotificationChannel.PUSH.value,
                            provider=push_provider.provider_name,
                            status=DeliveryStatus.PENDING.value,
                        )
                        push_res = await push_provider.send_push(
                            device_token=dev.device_token,
                            platform=dev.platform,
                            title=rendered["title"],
                            body=rendered["body"],
                            data=payload,
                        )
                        if push_res.success:
                            await NotificationDeliveryRepository.update_delivery_status(
                                db=db,
                                delivery_id=delivery.id,
                                status=DeliveryStatus.DELIVERED.value,
                                provider_message_id=push_res.provider_message_id,
                            )
                        else:
                            await NotificationDeliveryRepository.update_delivery_status(
                                db=db,
                                delivery_id=delivery.id,
                                status=DeliveryStatus.FAILED.value,
                                failure_code=push_res.failure_code,
                                failure_message=push_res.failure_message,
                            )
                            # Handle invalidated/unregistered tokens
                            if push_res.failure_code in ("INVALID_TOKEN", "UNREGISTERED"):
                                dev.is_active = False
                                await db.flush()
                            elif push_res.is_transient:
                                transient_error = True
            except Exception as e:
                logger.error("Push dispatch failed for event %s: %s", event.id, str(e))
                transient_error = True

        return not transient_error

    @classmethod
    async def process_outbox_batch(
        cls, db: AsyncSession, limit: int = 50
    ) -> int:
        """
        Claims and dispatches a batch of pending outbox events.
        Applies exponential backoff on transient errors and transitions completed events.
        """
        events = await NotificationOutboxRepository.claim_pending_events(db, limit=limit)
        processed_count = 0

        for event in events:
            try:
                success = await cls.dispatch_event(db, event)
                if success:
                    await NotificationOutboxRepository.mark_processed(db, event.id)
                    processed_count += 1
                else:
                    await NotificationOutboxRepository.mark_failed_or_retry(
                        db=db,
                        event_id=event.id,
                        error_message="One or more notification channels experienced a transient error",
                    )
            except Exception as exc:
                logger.exception("Failed processing outbox event %s", event.id)
                await NotificationOutboxRepository.mark_failed_or_retry(
                    db=db,
                    event_id=event.id,
                    error_message=str(exc),
                )

        return processed_count

    # --------------------------------------------------------------------------
    # Inbound Delivery Webhook Processing
    # --------------------------------------------------------------------------

    @classmethod
    async def process_delivery_webhook(
        cls,
        db: AsyncSession,
        provider: str,
        payload_bytes: bytes,
        signature_header: str,
        payload_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Authenticates and processes delivery status receipt webhooks from external gateways.
        Verifies constant-time HMAC signature and logs delivery update idempotently.
        """
        # 1. HMAC Signature Verification
        secret = settings.NOTIFICATION_WEBHOOK_SECRET
        expected_sig = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()

        # Check signature constant-time
        if not safe_str_cmp(expected_sig, signature_header):
            # Check prefix stripped or hex variant
            alt_sig = signature_header.replace("sha256=", "").strip()
            if not safe_str_cmp(expected_sig, alt_sig):
                logger.warning("Webhook signature verification failed for provider %s", provider)
                raise BadRequestError("Invalid webhook signature.")

        event_id = payload_json.get("event_id") or payload_json.get("id") or hashlib.md5(payload_bytes).hexdigest()
        event_type = payload_json.get("event_type") or payload_json.get("type") or "delivery_receipt"

        # 2. Record raw event idempotently
        webhook_log = await NotificationWebhookRepository.create_event(
            db=db,
            provider=provider.upper(),
            event_id=event_id,
            event_type=event_type,
            payload=payload_json,
        )

        # 3. Update matching delivery if provider_message_id is supplied
        provider_message_id = (
            payload_json.get("provider_message_id")
            or payload_json.get("message_id")
            or payload_json.get("sms_id")
        )
        if provider_message_id:
            delivery = await NotificationDeliveryRepository.get_by_provider_message_id(
                db=db, provider=provider.upper(), provider_message_id=provider_message_id
            )
            if delivery:
                status_raw = (payload_json.get("status") or "").upper()
                new_status = DeliveryStatus.DELIVERED.value
                if "FAIL" in status_raw or "BOUNCE" in status_raw:
                    new_status = DeliveryStatus.FAILED.value
                elif "SENT" in status_raw:
                    new_status = DeliveryStatus.SENT.value

                await NotificationDeliveryRepository.update_delivery_status(
                    db=db,
                    delivery_id=delivery.id,
                    status=new_status,
                    failure_code=payload_json.get("failure_code"),
                    failure_message=payload_json.get("failure_message") or payload_json.get("reason"),
                )

        return {"success": True, "event_id": webhook_log.provider_event_id}
