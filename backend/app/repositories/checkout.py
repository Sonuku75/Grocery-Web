"""
Cartify Checkout Repository (Module 9)

Data access and query management for checkout sessions:
- Scoped strictly to authenticated user_id to prevent IDOR vulnerabilities
- Eagerly loads address, coupon, and cart relationships
- Tracks active sessions, expiration, and idempotency keys
- Transactional session creation, state transition, and updates
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.checkout import CheckoutSession, CheckoutStatus


class CheckoutRepository:
    @classmethod
    async def get_by_id(
        cls, db: AsyncSession, session_id: str, user_id: Optional[str] = None
    ) -> Optional[CheckoutSession]:
        """
        Retrieves checkout session by ID, optionally scoped to user_id.
        """
        stmt = (
            select(CheckoutSession)
            .options(
                selectinload(CheckoutSession.address),
                selectinload(CheckoutSession.coupon),
                selectinload(CheckoutSession.cart),
            )
            .where(CheckoutSession.id == session_id)
        )
        if user_id is not None:
            stmt = stmt.where(CheckoutSession.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_active_session_by_user_id(
        cls, db: AsyncSession, user_id: str
    ) -> Optional[CheckoutSession]:
        """
        Retrieves the latest ACTIVE checkout session for a user.
        If the session has passed expires_at, marks it EXPIRED and returns None.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(CheckoutSession)
            .options(
                selectinload(CheckoutSession.address),
                selectinload(CheckoutSession.coupon),
                selectinload(CheckoutSession.cart),
            )
            .where(
                CheckoutSession.user_id == user_id,
                CheckoutSession.status == CheckoutStatus.ACTIVE.value,
            )
            .order_by(CheckoutSession.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if session:
            exp = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=timezone.utc)
            if now > exp:
                session.status = CheckoutStatus.EXPIRED.value
                await db.flush()
                return None

        return session

    @classmethod
    async def get_by_idempotency_key(
        cls, db: AsyncSession, idempotency_key: str, user_id: str
    ) -> Optional[CheckoutSession]:
        """
        Retrieves a checkout session by idempotency key and user_id.
        """
        stmt = (
            select(CheckoutSession)
            .options(
                selectinload(CheckoutSession.address),
                selectinload(CheckoutSession.coupon),
                selectinload(CheckoutSession.cart),
            )
            .where(
                CheckoutSession.idempotency_key == idempotency_key,
                CheckoutSession.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def cancel_active_sessions_for_user(
        cls, db: AsyncSession, user_id: str
    ) -> int:
        """
        Marks any currently ACTIVE checkout sessions for the user as CANCELLED.
        """
        stmt = (
            update(CheckoutSession)
            .where(
                CheckoutSession.user_id == user_id,
                CheckoutSession.status == CheckoutStatus.ACTIVE.value,
            )
            .values(status=CheckoutStatus.CANCELLED.value)
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount

    @classmethod
    async def create_session(
        cls, db: AsyncSession, session_data: dict
    ) -> CheckoutSession:
        """
        Creates and flushes a new checkout session.
        """
        session = CheckoutSession(**session_data)
        db.add(session)
        await db.flush()
        return session

    @classmethod
    async def update_session(
        cls, db: AsyncSession, session: CheckoutSession, update_data: dict
    ) -> CheckoutSession:
        """
        Updates fields on an existing checkout session.
        """
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        await db.flush()
        return session

    @classmethod
    async def mark_status(
        cls, db: AsyncSession, session: CheckoutSession, status: CheckoutStatus
    ) -> CheckoutSession:
        """
        Updates session status.
        """
        session.status = status.value
        await db.flush()
        return session
