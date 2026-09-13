"""
Cartify Order Repository (Module 10)

Data access and query management for orders, order items, status history, and idempotency:
- Strict ownership scoping (user_id) to prevent IDOR and privilege escalation
- Eager relationships loaded via selectinload to eliminate N+1 queries
- Transactional atomicity across orders, items, and status audit entries
- Database-level idempotency record persistence and lookup
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import (
    FulfillmentStatus,
    IdempotencyRecord,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)


class OrderRepository:
    @classmethod
    async def get_by_id(
        cls, db: AsyncSession, order_id_or_number: str, user_id: Optional[str] = None
    ) -> Optional[Order]:
        """
        Retrieves an order by internal UUID or public order_number.
        When user_id is provided, scopes query to enforce ownership.
        """
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.user),
            )
            .where(
                or_(
                    Order.id == order_id_or_number,
                    Order.order_number == order_id_or_number,
                )
            )
        )
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_checkout_session_id(
        cls, db: AsyncSession, checkout_session_id: str
    ) -> Optional[Order]:
        """
        Finds existing order created from a specific checkout session.
        """
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
            .where(Order.checkout_session_id == checkout_session_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_by_user(
        cls, db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[Order]:
        """
        Retrieves paginated customer orders sorted newest first.
        """
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def count_by_user(cls, db: AsyncSession, user_id: str) -> int:
        """
        Counts total orders placed by customer.
        """
        stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
        res = await db.execute(stmt)
        return int(res.scalar_one() or 0)

    @classmethod
    async def list_admin_orders(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Order], int]:
        """
        Admin query with optional status filtering and order_number/name search.
        """
        base_stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count(Order.id))

        filters = []
        if status and status.strip():
            filters.append(Order.status == status.strip().upper())
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.recipient_name.ilike(pattern),
                    Order.phone.ilike(pattern),
                )
            )

        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        base_stmt = base_stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)

        items_res = await db.execute(base_stmt)
        count_res = await db.execute(count_stmt)

        return list(items_res.scalars().all()), int(count_res.scalar_one() or 0)

    @classmethod
    async def create_order(
        cls,
        db: AsyncSession,
        order_data: dict,
        items_data: List[dict],
        initial_reason: Optional[str] = "Order created from checkout",
    ) -> Order:
        """
        Atomically creates Order, OrderItems, and initial OrderStatusHistory.
        """
        order = Order(**order_data)
        db.add(order)
        await db.flush()

        for item_dict in items_data:
            order_item = OrderItem(order_id=order.id, **item_dict)
            db.add(order_item)

        history_entry = OrderStatusHistory(
            order_id=order.id,
            old_status=None,
            new_status=order.status,
            changed_by_user_id=order.user_id,
            reason=initial_reason,
        )
        db.add(history_entry)

        await db.flush()
        return order

    @classmethod
    async def update_status(
        cls,
        db: AsyncSession,
        order: Order,
        new_status: str,
        changed_by_user_id: Optional[str] = None,
        reason: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
    ) -> Order:
        """
        Updates order status, optionally updates fulfillment status,
        and appends an immutable audit record to order_status_history.
        """
        old_status = order.status
        order.status = new_status
        if fulfillment_status is not None:
            order.fulfillment_status = fulfillment_status

        history_entry = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
            reason=reason,
        )
        db.add(history_entry)
        await db.flush()
        return order

    @classmethod
    async def get_idempotency_record(
        cls, db: AsyncSession, user_id: str, key: str
    ) -> Optional[IdempotencyRecord]:
        """
        Retrieves non-expired idempotency record.
        """
        now = datetime.now(timezone.utc)
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.key == key,
            IdempotencyRecord.expires_at > now,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def save_idempotency_record(
        cls,
        db: AsyncSession,
        user_id: str,
        key: str,
        response_status: int,
        response_body: dict,
        request_hash: Optional[str] = None,
        expires_in_hours: int = 24,
    ) -> IdempotencyRecord:
        """
        Saves an idempotent response record with 24-hour expiration.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expires_in_hours)
        rec = IdempotencyRecord(
            user_id=user_id,
            key=key,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
            expires_at=expires_at,
        )
        db.add(rec)
        await db.flush()
        return rec
