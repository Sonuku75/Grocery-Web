"""
Cartify Account Deletion Service (Module 15.1)

Manages safe, non-destructive account deletion lifecycle with grace periods.
Protects historical order, payment, and audit trails from accidental corruption.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError, UnauthorizedError
from app.core.security import verify_password
from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.repositories.account_deletion import AccountDeletionRepository
from app.schemas.account import AccountDeletionResponse
from app.services.security_event_service import SecurityEventService

logger = logging.getLogger("cartify.account_deletion")

DEFAULT_GRACE_PERIOD_DAYS = 30


class AccountDeletionService:
    @classmethod
    async def has_active_orders(cls, db: AsyncSession, user_id: str) -> bool:
        """
        Checks whether user has active orders in flight that prevent immediate deletion scheduling.
        """
        terminal_statuses = (
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        )
        stmt = (
            select(Order)
            .where(
                Order.user_id == user_id,
                Order.status.not_in(terminal_statuses),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def request_deletion(
        cls,
        db: AsyncSession,
        user: User,
        current_password: str,
        reason: Optional[str] = None,
        grace_period_days: int = DEFAULT_GRACE_PERIOD_DAYS,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AccountDeletionResponse:
        """
        Schedules account deletion after password confirmation and business constraint validation.
        Enters PENDING status with a grace period. Does NOT delete data immediately.
        """
        # 1. Verify current password
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Incorrect password. Identity confirmation failed.")

        # 2. Check if a request is already pending
        existing = await AccountDeletionRepository.get_pending_by_user_id(db, user.id)
        if existing:
            raise CartifyException(
                status_code=400,
                detail="An account deletion request is already pending for this account.",
                code="DELETION_ALREADY_PENDING",
            )

        # 3. Check for active orders in flight
        if await cls.has_active_orders(db, user.id):
            raise CartifyException(
                status_code=400,
                detail="Cannot request account deletion while you have orders in progress.",
                code="ACTIVE_ORDERS_EXIST",
            )

        # 4. Schedule deletion
        now = datetime.now(timezone.utc)
        scheduled_at = now + timedelta(days=grace_period_days)

        deletion_req = await AccountDeletionRepository.create(
            db=db,
            user_id=user.id,
            scheduled_at=scheduled_at,
            reason=reason,
        )

        # 5. Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="ACCOUNT_DELETION_REQUESTED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "scheduled_at": scheduled_at.isoformat(),
                "reason": reason,
            },
        )

        return AccountDeletionResponse(
            id=deletion_req.id,
            status=deletion_req.status,
            requested_at=deletion_req.requested_at,
            scheduled_at=deletion_req.scheduled_at,
            grace_period_days=grace_period_days,
        )

    @classmethod
    async def cancel_deletion(
        cls,
        db: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Cancels an active pending account deletion request.
        """
        pending = await AccountDeletionRepository.get_pending_by_user_id(db, user.id)
        if not pending:
            raise NotFoundError("No pending account deletion request found.")

        cancelled = await AccountDeletionRepository.cancel(db, pending.id, user.id)
        if cancelled:
            await SecurityEventService.record_security_event(
                db=db,
                user_id=user.id,
                event_type="ACCOUNT_DELETION_CANCELLED",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"request_id": pending.id},
            )
        return cancelled

    @classmethod
    async def get_deletion_status(
        cls, db: AsyncSession, user_id: str
    ) -> Optional[AccountDeletionRequest]:
        """
        Returns active pending deletion request for the given user if one exists.
        """
        return await AccountDeletionRepository.get_pending_by_user_id(db, user_id)
