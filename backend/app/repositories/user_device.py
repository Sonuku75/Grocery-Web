"""
User Device Repository (Module 13)

Manages mobile and web push notification device tokens.
Never returns unmasked device tokens in client payloads.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_device import UserDevice


class UserDeviceRepository:
    """Repository for user push notification devices."""

    @staticmethod
    async def register_device(
        db: AsyncSession,
        user_id: str,
        platform: str,
        device_token: str,
        app_version: Optional[str] = None,
    ) -> UserDevice:
        stmt = select(UserDevice).where(
            UserDevice.user_id == user_id,
            UserDevice.device_token == device_token,
        )
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if device:
            device.platform = platform.upper()
            device.app_version = app_version
            device.is_active = True
            device.last_seen_at = now
        else:
            device = UserDevice(
                user_id=user_id,
                platform=platform.upper(),
                device_token=device_token,
                app_version=app_version,
                is_active=True,
                last_seen_at=now,
            )
            db.add(device)

        await db.flush()
        return device

    @staticmethod
    async def get_active_devices_for_user(
        db: AsyncSession,
        user_id: str,
    ) -> List[UserDevice]:
        stmt = select(UserDevice).where(
            UserDevice.user_id == user_id,
            UserDevice.is_active == True,
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: str,
    ) -> List[UserDevice]:
        stmt = select(UserDevice).where(
            UserDevice.user_id == user_id,
        ).order_by(UserDevice.last_seen_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def deactivate_device(
        db: AsyncSession,
        device_id: str,
        user_id: str,
    ) -> bool:
        stmt = select(UserDevice).where(
            UserDevice.id == device_id,
            UserDevice.user_id == user_id,
        )
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            return False

        device.is_active = False
        await db.flush()
        return True

    @staticmethod
    async def deactivate_token(
        db: AsyncSession,
        device_token: str,
    ) -> int:
        stmt = select(UserDevice).where(
            UserDevice.device_token == device_token,
            UserDevice.is_active == True,
        )
        res = await db.execute(stmt)
        devices = list(res.scalars().all())
        for d in devices:
            d.is_active = False
        await db.flush()
        return len(devices)
