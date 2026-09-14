"""
Cartify Account Change Request Repository (Module 15.1)

Encapsulates staged verification records for sensitive account modifications (email, phone).
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_change_request import AccountChangeRequest


class AccountChangeRequestRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        change_type: str,
        target_value: str,
        verification_token_hash: str,
        expires_at: datetime,
    ) -> AccountChangeRequest:
        """
        Creates an unverified account change request.
        """
        now = datetime.now(timezone.utc)
        req = AccountChangeRequest(
            user_id=user_id,
            change_type=change_type,
            target_value=target_value,
            verification_token_hash=verification_token_hash,
            expires_at=expires_at,
            is_verified=False,
            created_at=now,
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def get_active_by_user_and_type(
        db: AsyncSession, user_id: str, change_type: str
    ) -> Optional[AccountChangeRequest]:
        """
        Retrieves the latest pending (non-verified, non-expired) change request.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(AccountChangeRequest)
            .where(
                AccountChangeRequest.user_id == user_id,
                AccountChangeRequest.change_type == change_type,
                AccountChangeRequest.is_verified == False,
                AccountChangeRequest.expires_at > now,
            )
            .order_by(desc(AccountChangeRequest.created_at))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_token_hash(
        db: AsyncSession, token_hash: str
    ) -> Optional[AccountChangeRequest]:
        """
        Retrieves a change request by its SHA-256 token hash.
        """
        stmt = select(AccountChangeRequest).where(
            AccountChangeRequest.verification_token_hash == token_hash
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_completed(
        db: AsyncSession, request_id: str
    ) -> bool:
        """
        Marks a change request as verified and completed.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(AccountChangeRequest)
            .where(
                AccountChangeRequest.id == request_id,
                AccountChangeRequest.is_verified == False,
            )
            .values(
                is_verified=True,
                completed_at=now,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
