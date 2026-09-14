"""
Notification Preference Repository (Module 13)

Manages multi-channel user communication preferences and security rules.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationChannel
from app.models.notification_preference import (
    NotificationCategory,
    NotificationPreference,
)


DEFAULT_PREFERENCES: List[Dict[str, Any]] = [
    # ORDER_UPDATES
    {"notification_type": NotificationCategory.ORDER_UPDATES.value, "channel": NotificationChannel.IN_APP.value, "is_enabled": True},
    {"notification_type": NotificationCategory.ORDER_UPDATES.value, "channel": NotificationChannel.EMAIL.value, "is_enabled": True},
    {"notification_type": NotificationCategory.ORDER_UPDATES.value, "channel": NotificationChannel.SMS.value, "is_enabled": True},
    {"notification_type": NotificationCategory.ORDER_UPDATES.value, "channel": NotificationChannel.PUSH.value, "is_enabled": True},

    # PAYMENT_UPDATES
    {"notification_type": NotificationCategory.PAYMENT_UPDATES.value, "channel": NotificationChannel.IN_APP.value, "is_enabled": True},
    {"notification_type": NotificationCategory.PAYMENT_UPDATES.value, "channel": NotificationChannel.EMAIL.value, "is_enabled": True},
    {"notification_type": NotificationCategory.PAYMENT_UPDATES.value, "channel": NotificationChannel.SMS.value, "is_enabled": True},
    {"notification_type": NotificationCategory.PAYMENT_UPDATES.value, "channel": NotificationChannel.PUSH.value, "is_enabled": True},

    # PROMOTIONS
    {"notification_type": NotificationCategory.PROMOTIONS.value, "channel": NotificationChannel.IN_APP.value, "is_enabled": True},
    {"notification_type": NotificationCategory.PROMOTIONS.value, "channel": NotificationChannel.EMAIL.value, "is_enabled": True},
    {"notification_type": NotificationCategory.PROMOTIONS.value, "channel": NotificationChannel.SMS.value, "is_enabled": False},
    {"notification_type": NotificationCategory.PROMOTIONS.value, "channel": NotificationChannel.PUSH.value, "is_enabled": True},

    # SECURITY_ALERTS (Mandatory - always True)
    {"notification_type": NotificationCategory.SECURITY_ALERTS.value, "channel": NotificationChannel.IN_APP.value, "is_enabled": True},
    {"notification_type": NotificationCategory.SECURITY_ALERTS.value, "channel": NotificationChannel.EMAIL.value, "is_enabled": True},
    {"notification_type": NotificationCategory.SECURITY_ALERTS.value, "channel": NotificationChannel.SMS.value, "is_enabled": True},
    {"notification_type": NotificationCategory.SECURITY_ALERTS.value, "channel": NotificationChannel.PUSH.value, "is_enabled": True},
]


class NotificationPreferenceRepository:
    """Repository for user notification channel preferences."""

    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: str,
    ) -> List[NotificationPreference]:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        res = await db.execute(stmt)
        prefs = list(res.scalars().all())

        # If user has no preferences initialized, seed defaults
        if not prefs:
            prefs = await NotificationPreferenceRepository.initialize_defaults(db, user_id)

        return prefs

    @staticmethod
    async def initialize_defaults(
        db: AsyncSession,
        user_id: str,
    ) -> List[NotificationPreference]:
        created = []
        for default in DEFAULT_PREFERENCES:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=default["notification_type"],
                channel=default["channel"],
                is_enabled=default["is_enabled"],
            )
            db.add(pref)
            created.append(pref)
        await db.flush()
        return created

    @staticmethod
    async def is_channel_enabled(
        db: AsyncSession,
        user_id: str,
        category: str,
        channel: str,
    ) -> bool:
        # Security alerts can never be disabled
        if category == NotificationCategory.SECURITY_ALERTS.value:
            return True

        stmt = select(NotificationPreference.is_enabled).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == category,
            NotificationPreference.channel == channel,
        )
        res = await db.execute(stmt)
        val = res.scalar_one_or_none()
        if val is None:
            # Default fallback
            for default in DEFAULT_PREFERENCES:
                if default["notification_type"] == category and default["channel"] == channel:
                    return default["is_enabled"]
            return True
        return val

    @staticmethod
    async def set_preference(
        db: AsyncSession,
        user_id: str,
        category: str,
        channel: str,
        is_enabled: bool,
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == category,
            NotificationPreference.channel == channel,
        )
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()

        if pref:
            pref.is_enabled = is_enabled
        else:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=category,
                channel=channel,
                is_enabled=is_enabled,
            )
            db.add(pref)

        await db.flush()
        return pref
