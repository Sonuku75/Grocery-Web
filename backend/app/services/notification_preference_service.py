"""
Notification Preference Service (Module 13)

Enforces user preference matrices and non-disableable security alert protections.
"""

import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError
from app.models.notification import NotificationChannel
from app.models.notification_preference import NotificationCategory
from app.repositories.notification_preference import NotificationPreferenceRepository
from app.schemas.notification_preference import (
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    UpdateNotificationPreferenceRequest,
)

logger = logging.getLogger("cartify.notification_preferences")

# All active categories and channels supported in preference management
ALL_CATEGORIES = [
    NotificationCategory.ORDER_UPDATES.value,
    NotificationCategory.PAYMENT_UPDATES.value,
    NotificationCategory.PROMOTIONS.value,
    NotificationCategory.SECURITY_ALERTS.value,
]

ALL_CHANNELS = [
    NotificationChannel.IN_APP.value,
    NotificationChannel.EMAIL.value,
    NotificationChannel.SMS.value,
    NotificationChannel.PUSH.value,
]


class NotificationPreferenceService:
    """Business logic for notification preferences."""

    @classmethod
    async def get_user_preferences(
        cls, db: AsyncSession, user_id: str
    ) -> NotificationPreferencesResponse:
        """
        Retrieve full matrix of categories x channels for the user,
        defaulting to active unless explicitly opted out (except security alerts which are mandatory).
        """
        existing_prefs = await NotificationPreferenceRepository.get_user_preferences(db, user_id)
        pref_map = {
            (p.notification_type, p.channel): p.is_enabled
            for p in existing_prefs
        }

        items: List[NotificationPreferenceItem] = []
        for cat in ALL_CATEGORIES:
            is_mandatory = (cat == NotificationCategory.SECURITY_ALERTS.value)
            for ch in ALL_CHANNELS:
                if is_mandatory:
                    # Security alerts are always enabled and mandatory
                    enabled = True
                else:
                    # Default: True unless explicitly set to False in DB
                    enabled = pref_map.get((cat, ch), True)

                items.append(
                    NotificationPreferenceItem(
                        category=cat,
                        channel=ch,
                        isEnabled=enabled,
                        isMandatory=is_mandatory,
                    )
                )

        return NotificationPreferencesResponse(preferences=items)

    @classmethod
    async def update_preference(
        cls,
        db: AsyncSession,
        user_id: str,
        request: UpdateNotificationPreferenceRequest,
    ) -> NotificationPreferenceItem:
        """
        Update or create a notification preference for a specific category and channel.
        Rejects any attempt to disable security alerts.
        """
        cat = request.category.upper()
        ch = request.channel.upper()

        if cat not in ALL_CATEGORIES:
            raise BadRequestError(
                f"Invalid notification category '{request.category}'. Valid: {ALL_CATEGORIES}"
            )
        if ch not in ALL_CHANNELS:
            raise BadRequestError(
                f"Invalid notification channel '{request.channel}'. Valid: {ALL_CHANNELS}"
            )

        if cat == NotificationCategory.SECURITY_ALERTS.value:
            if not request.is_enabled:
                raise BadRequestError("Security alerts are mandatory and cannot be disabled.")
            return NotificationPreferenceItem(
                category=cat,
                channel=ch,
                isEnabled=True,
                isMandatory=True,
            )

        pref = await NotificationPreferenceRepository.set_preference(
            db=db,
            user_id=user_id,
            notification_type=cat,
            channel=ch,
            is_enabled=request.is_enabled,
        )

        return NotificationPreferenceItem(
            category=pref.notification_type,
            channel=pref.channel,
            isEnabled=pref.is_enabled,
            isMandatory=False,
        )

    @classmethod
    async def is_channel_enabled(
        cls,
        db: AsyncSession,
        user_id: str,
        category: str,
        channel: str,
    ) -> bool:
        """
        Authoritative check if delivery on the specified channel is enabled.
        Always returns True for SECURITY_ALERTS.
        """
        if category.upper() == NotificationCategory.SECURITY_ALERTS.value:
            return True

        return await NotificationPreferenceRepository.is_channel_enabled(
            db=db,
            user_id=user_id,
            notification_type=category.upper(),
            channel=channel.upper(),
            default=True,
        )
