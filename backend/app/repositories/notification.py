"""
Notification and Delivery Repositories (Module 13)

Provides optimized data access for customer in-app notifications and delivery tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationPriority,
    NotificationStatus,
)


class NotificationRepository:
    """Repository for managing in-app customer notifications."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = NotificationPriority.MEDIUM.value,
        reference_key: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        # Check idempotency / deduplication if reference_key is provided
        if reference_key:
            stmt = select(Notification).where(
                Notification.user_id == user_id,
                Notification.reference_key == reference_key,
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
            priority=priority,
            status=NotificationStatus.UNREAD.value,
            reference_key=reference_key,
            expires_at=expires_at,
        )
        db.add(notification)
        await db.flush()
        return notification

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        notification_id: str,
    ) -> Optional[Notification]:
        stmt = select(Notification).where(Notification.id == notification_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Notification], int, int, Optional[str]]:
        """
        Returns (items, total_count, unread_count, next_cursor).
        Cursor pagination is based on created_at timestamp string (ISO format).
        """
        # Base filter for current user
        base_filters = [Notification.user_id == user_id]
        if unread_only:
            base_filters.append(Notification.status == NotificationStatus.UNREAD.value)
        if notification_type:
            base_filters.append(Notification.type == notification_type)

        # Count total matching
        total_stmt = select(func.count(Notification.id)).where(*base_filters)
        total_res = await db.execute(total_stmt)
        total_count = total_res.scalar_one() or 0

        # Count unread
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD.value,
        )
        unread_res = await db.execute(unread_stmt)
        unread_count = unread_res.scalar_one() or 0

        # Query items with cursor
        query_filters = list(base_filters)
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
                query_filters.append(Notification.created_at < cursor_dt)
            except (ValueError, TypeError):
                pass

        stmt = (
            select(Notification)
            .where(*query_filters)
            .order_by(desc(Notification.created_at))
            .limit(limit + 1)
        )
        res = await db.execute(stmt)
        rows = list(res.scalars().all())

        next_cursor = None
        if len(rows) > limit:
            items = rows[:limit]
            next_cursor = items[-1].created_at.isoformat()
        else:
            items = rows

        return items, total_count, unread_count, next_cursor

    @staticmethod
    async def count_unread(
        db: AsyncSession,
        user_id: str,
    ) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD.value,
        )
        res = await db.execute(stmt)
        return res.scalar_one() or 0

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_id: str,
        user_id: str,
    ) -> Optional[Notification]:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            return None

        if notification.status != NotificationStatus.READ.value:
            notification.status = NotificationStatus.READ.value
            notification.read_at = datetime.now(timezone.utc)
            await db.flush()

        return notification

    @staticmethod
    async def mark_all_as_read(
        db: AsyncSession,
        user_id: str,
    ) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD.value,
            )
            .values(
                status=NotificationStatus.READ.value,
                read_at=now,
            )
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount or 0

    @staticmethod
    async def delete_notification(
        db: AsyncSession,
        notification_id: str,
        user_id: str,
    ) -> bool:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            return False

        await db.delete(notification)
        await db.flush()
        return True

    @staticmethod
    async def list_admin(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[List[Notification], int]:
        filters = []
        if status:
            filters.append(Notification.status == status)
        if notification_type:
            filters.append(Notification.type == notification_type)
        if user_id:
            filters.append(Notification.user_id == user_id)

        count_stmt = select(func.count(Notification.id)).where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        stmt = (
            select(Notification)
            .where(*filters)
            .order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all()), total


class NotificationDeliveryRepository:
    """Repository for managing multi-channel delivery attempts and webhook logs."""

    @staticmethod
    async def create_delivery(
        db: AsyncSession,
        notification_id: str,
        user_id: str,
        channel: str,
        provider: str,
        status: str = DeliveryStatus.PENDING.value,
    ) -> NotificationDelivery:
        delivery = NotificationDelivery(
            notification_id=notification_id,
            user_id=user_id,
            channel=channel,
            provider=provider,
            status=status,
            attempt_count=0,
        )
        db.add(delivery)
        await db.flush()
        return delivery

    @staticmethod
    async def update_delivery_status(
        db: AsyncSession,
        delivery_id: str,
        status: str,
        provider_message_id: Optional[str] = None,
        failure_code: Optional[str] = None,
        failure_message: Optional[str] = None,
        delivered_at: Optional[datetime] = None,
    ) -> Optional[NotificationDelivery]:
        stmt = select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        res = await db.execute(stmt)
        delivery = res.scalar_one_or_none()
        if not delivery:
            return None

        delivery.status = status
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.now(timezone.utc)

        if provider_message_id:
            delivery.provider_message_id = provider_message_id
        if failure_code:
            delivery.failure_code = failure_code
        if failure_message:
            delivery.failure_message = failure_message
        if delivered_at:
            delivery.delivered_at = delivered_at
        elif status == DeliveryStatus.DELIVERED.value:
            delivery.delivered_at = datetime.now(timezone.utc)
        elif status == DeliveryStatus.FAILED.value:
            delivery.failed_at = datetime.now(timezone.utc)

        await db.flush()
        return delivery

    @staticmethod
    async def get_by_provider_message_id(
        db: AsyncSession,
        provider: str,
        provider_message_id: str,
    ) -> Optional[NotificationDelivery]:
        stmt = select(NotificationDelivery).where(
            NotificationDelivery.provider == provider,
            NotificationDelivery.provider_message_id == provider_message_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_admin(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[NotificationDelivery], int]:
        filters = []
        if channel:
            filters.append(NotificationDelivery.channel == channel)
        if status:
            filters.append(NotificationDelivery.status == status)

        count_stmt = select(func.count(NotificationDelivery.id)).where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        stmt = (
            select(NotificationDelivery)
            .where(*filters)
            .order_by(desc(NotificationDelivery.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all()), total
