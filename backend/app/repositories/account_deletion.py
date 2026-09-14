"""
Cartify Account Deletion Request Repository (Module 15.1)

Encapsulates database operations for customer account deletion requests.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus


class AccountDeletionRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        scheduled_at: datetime,
        reason: Optional[str] = None,
    ) -> AccountDeletionRequest:
        """
        Creates a new PENDING account deletion request.
        """
        now = datetime.now(timezone.utc)
        req = AccountDeletionRequest(
            user_id=user_id,
            status=AccountDeletionStatus.PENDING,
            reason=reason,
            requested_at=now,
            scheduled_at=scheduled_at,
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def get_pending_by_user_id(
        db: AsyncSession, user_id: str
    ) -> Optional[AccountDeletionRequest]:
        """
        Returns the active PENDING deletion request for a user if one exists.
        """
        stmt = (
            select(AccountDeletionRequest)
            .where(
                AccountDeletionRequest.user_id == user_id,
                AccountDeletionRequest.status == AccountDeletionStatus.PENDING,
            )
            .order_by(desc(AccountDeletionRequest.requested_at))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def cancel(
        db: AsyncSession, request_id: str, user_id: str
    ) -> bool:
        """
        Cancels a pending account deletion request for the given user.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(AccountDeletionRequest)
            .where(
                AccountDeletionRequest.id == request_id,
                AccountDeletionRequest.user_id == user_id,
                AccountDeletionRequest.status == AccountDeletionStatus.PENDING,
            )
            .values(
                status=AccountDeletionStatus.CANCELLED,
                cancelled_at=now,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def complete(
        db: AsyncSession, request_id: str
    ) -> bool:
        """
        Marks an account deletion request as COMPLETED.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(AccountDeletionRequest)
            .where(
                AccountDeletionRequest.id == request_id,
                AccountDeletionRequest.status == AccountDeletionStatus.PENDING,
            )
            .values(
                status=AccountDeletionStatus.COMPLETED,
                completed_at=now,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
