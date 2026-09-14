"""
Cartify User Session Repository (Module 15.1)

Encapsulates active session queries, updates, and revocations for multi-device management.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession


class UserSessionRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        session_identifier: str,
        expires_at: datetime,
        device_name: Optional[str] = None,
        platform: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """
        Persists a new active user session.
        session_identifier is a SHA-256 hash of the random session token.
        """
        now = datetime.now(timezone.utc)
        session = UserSession(
            user_id=user_id,
            session_identifier=session_identifier,
            expires_at=expires_at,
            device_name=device_name,
            platform=platform,
            ip_address=ip_address,
            user_agent=user_agent,
            last_seen_at=now,
            created_at=now,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_by_identifier(
        db: AsyncSession, session_identifier: str
    ) -> Optional[UserSession]:
        """Looks up a session by its unique SHA-256 identifier."""
        stmt = select(UserSession).where(
            UserSession.session_identifier == session_identifier
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession, session_id: str
    ) -> Optional[UserSession]:
        """Looks up a session by its UUID."""
        stmt = select(UserSession).where(UserSession.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_by_user_id(
        db: AsyncSession, user_id: str
    ) -> List[UserSession]:
        """
        Returns all non-revoked, non-expired sessions for a user.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(desc(UserSession.last_seen_at))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_last_seen(
        db: AsyncSession, session_identifier: str
    ) -> None:
        """Updates the last_seen_at timestamp for an active session."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(
                UserSession.session_identifier == session_identifier,
                UserSession.revoked_at.is_(None),
            )
            .values(last_seen_at=now)
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def revoke(
        db: AsyncSession, session_id: str, user_id: str
    ) -> bool:
        """
        Revokes a single session owned by user_id. Returns True if revoked, False otherwise.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def revoke_all_for_user(
        db: AsyncSession, user_id: str, except_identifier: Optional[str] = None
    ) -> int:
        """
        Revokes all active sessions for a user, optionally preserving the current session.
        """
        now = datetime.now(timezone.utc)
        conditions = [
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        ]
        if except_identifier:
            conditions.append(UserSession.session_identifier != except_identifier)

        stmt = (
            update(UserSession)
            .where(*conditions)
            .values(revoked_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
