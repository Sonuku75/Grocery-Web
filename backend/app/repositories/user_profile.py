"""
Cartify User Profile Repository (Module 15.1)

Encapsulates database operations for UserProfile records.
"""

from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_profile import UserProfile


class UserProfileRepository:
    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
        """Fetches the user profile for the given user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert(
        db: AsyncSession, user_id: str, profile_data: Dict[str, Any]
    ) -> UserProfile:
        """
        Creates or updates a user profile record for the specified user ID.
        """
        profile = await UserProfileRepository.get_by_user_id(db, user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id, **profile_data)
            db.add(profile)
        else:
            for key, val in profile_data.items():
                setattr(profile, key, val)
        await db.commit()
        await db.refresh(profile)
        return profile
