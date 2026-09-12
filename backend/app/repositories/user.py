"""
Cartify User & Token Repository (Module 1)

Encapsulates all database operations for Users, RefreshTokens, and PasswordResetTokens.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken

class UserRepository:
    # ---------------- User Operations ----------------
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        stmt = select(User).where(User.phone == phone)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email_or_phone(db: AsyncSession, identifier: str) -> Optional[User]:
        stmt = select(User).where(
            or_(User.email == identifier.lower(), User.phone == identifier)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User, update_data: Dict[str, Any]) -> User:
        for key, value in update_data.items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user

    # ---------------- RefreshToken Operations ----------------
    @staticmethod
    async def create_refresh_token(
        db: AsyncSession,
        user_id: str,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def get_refresh_token_by_hash(
        db: AsyncSession, token_hash: str
    ) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def revoke_token_family(db: AsyncSession, family_id: str) -> None:
        """Revokes all tokens in a family when reuse of a compromised token is detected."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> None:
        """Revokes all active refresh tokens for a user (e.g. on password reset)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.execute(stmt)
        await db.commit()

    # ---------------- PasswordResetToken Operations ----------------
    @staticmethod
    async def create_password_reset_token(
        db: AsyncSession,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.commit()
        await db.refresh(reset_token)
        return reset_token

    @staticmethod
    async def get_valid_password_reset_token(
        db: AsyncSession, token_hash: str
    ) -> Optional[PasswordResetToken]:
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_password_reset_token_used(
        db: AsyncSession, token: PasswordResetToken
    ) -> None:
        token.used_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def invalidate_existing_reset_tokens(
        db: AsyncSession, user_id: str
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        await db.execute(stmt)
        await db.commit()
