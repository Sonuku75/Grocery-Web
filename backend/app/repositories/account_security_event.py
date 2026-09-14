"""
Cartify Account Security Event Repository (Module 15.1)

Encapsulates audit event creation and query access for account security events.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_security_event import AccountSecurityEvent


class AccountSecurityEventRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AccountSecurityEvent:
        """
        Creates and persists an immutable security audit event.
        """
        event = AccountSecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata_json=metadata_json,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def list_by_user_id(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AccountSecurityEvent]:
        """
        Lists security events for a specific user, ordered newest first.
        """
        stmt = (
            select(AccountSecurityEvent)
            .where(AccountSecurityEvent.user_id == user_id)
            .order_by(desc(AccountSecurityEvent.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
