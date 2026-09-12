"""
Cartify User Service (Module 1)

Handles user profile management, secure profile updates, and password changes.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import CartifyException, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdateRequest

class UserService:
    @classmethod
    async def get_profile(cls, db: AsyncSession, user_id: str) -> UserResponse:
        user = await UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise NotFoundError("User", user_id)
        return UserResponse.model_validate(user)

    @classmethod
    async def update_profile(
        cls, db: AsyncSession, user: User, data: UserUpdateRequest
    ) -> UserResponse:
        """
        Updates allowed profile fields (name, phone, avatar_url).
        Strictly prevents role escalation or email modification via profile update.
        """
        updates = {}
        if data.name is not None:
            updates["name"] = data.name.strip()

        if data.phone is not None:
            new_phone = data.phone.strip() or None
            if new_phone and new_phone != user.phone:
                existing = await UserRepository.get_by_phone(db, new_phone)
                if existing and existing.id != user.id:
                    raise CartifyException(
                        status_code=409,
                        detail="A user with this phone number already exists.",
                        code="PHONE_ALREADY_EXISTS",
                    )
            updates["phone"] = new_phone

        if data.avatar_url is not None:
            updates["avatar_url"] = data.avatar_url

        if updates:
            user = await UserRepository.update(db, user, updates)

        return UserResponse.model_validate(user)

    @classmethod
    async def change_password(
        cls, db: AsyncSession, user: User, data: ChangePasswordRequest
    ) -> None:
        """
        Verifies current password and updates to new password hash.
        Revokes all active refresh tokens for session security.
        """
        if not verify_password(data.current_password, user.password_hash):
            raise CartifyException(
                status_code=400,
                detail="Current password is incorrect.",
                code="INVALID_CURRENT_PASSWORD",
            )

        user.password_hash = get_password_hash(data.new_password)
        await db.commit()

        # Invalidate active refresh tokens
        await UserRepository.revoke_all_user_tokens(db, user.id)
