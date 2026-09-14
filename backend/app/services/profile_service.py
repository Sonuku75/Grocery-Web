"""
Cartify Profile Service (Module 15.1)

Handles user profile retrieval, mass-assignment-protected updates, and audit tracking.
Server-authoritatively ensures account ownership and separates primary user auth from profile metadata.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError
from app.models.user import User
from app.repositories.account_deletion import AccountDeletionRepository
from app.repositories.user import UserRepository
from app.repositories.user_profile import UserProfileRepository
from app.schemas.account import AccountProfileResponse, ProfileUpdateRequest
from app.services.security_event_service import SecurityEventService

logger = logging.getLogger("cartify.profile")


class ProfileService:
    @classmethod
    async def get_profile(
        cls, db: AsyncSession, user_id: str
    ) -> AccountProfileResponse:
        """
        Retrieves the combined user and profile details.
        Also checks for any pending account deletion request.
        """
        user = await UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise NotFoundError("User profile not found or inactive.")

        profile = await UserProfileRepository.get_by_user_id(db, user_id)
        pending_deletion = await AccountDeletionRepository.get_pending_by_user_id(db, user_id)

        return AccountProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            avatar_url=user.avatar_url,
            date_of_birth=profile.date_of_birth if profile else None,
            bio=profile.bio if profile else None,
            is_verified=user.is_verified,
            created_at=user.created_at,
            has_pending_deletion=pending_deletion is not None,
        )

    @classmethod
    async def update_profile(
        cls,
        db: AsyncSession,
        user: User,
        data: ProfileUpdateRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AccountProfileResponse:
        """
        Updates profile fields in a transaction.
        Updates user.name and user.avatar_url on users table.
        Updates date_of_birth and bio on user_profiles table.
        Privileged fields (role, id, is_active, is_verified, email, phone) cannot be updated here.
        """
        updated_fields = []

        # 1. Update primary User table attributes if provided
        user_updates = {}
        if data.name is not None and data.name != user.name:
            user_updates["name"] = data.name
            updated_fields.append("name")

        if data.phone is not None and data.phone != user.phone:
            existing_phone = await UserRepository.get_by_phone(db, data.phone)
            if existing_phone and existing_phone.id != user.id:
                raise CartifyException(
                    status_code=409,
                    detail="This phone number is already registered to another account.",
                    code="PHONE_ALREADY_IN_USE",
                )
            user_updates["phone"] = data.phone
            updated_fields.append("phone")

        if data.avatar_url is not None and data.avatar_url != user.avatar_url:
            user_updates["avatar_url"] = data.avatar_url
            updated_fields.append("avatar_url")

        if user_updates:
            await UserRepository.update(db, user, user_updates)

        # 2. Update or create UserProfile attributes if provided
        profile_data = {}
        if data.date_of_birth is not None:
            profile_data["date_of_birth"] = data.date_of_birth
            updated_fields.append("date_of_birth")

        if data.bio is not None:
            profile_data["bio"] = data.bio
            updated_fields.append("bio")

        if profile_data:
            await UserProfileRepository.upsert(db, user.id, profile_data)

        # 3. Record security audit event if any updates occurred
        if updated_fields:
            await SecurityEventService.record_security_event(
                db=db,
                user_id=user.id,
                event_type="PROFILE_UPDATED",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                metadata={"updated_fields": updated_fields},
            )

        return await cls.get_profile(db, user.id)
