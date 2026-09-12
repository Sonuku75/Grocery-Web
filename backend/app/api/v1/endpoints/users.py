"""
Cartify User Endpoints (Module 1)

Endpoints:
- GET /api/v1/users/me: Retrieve current authenticated user profile
- PATCH /api/v1/users/me: Update current user profile (name, phone, avatar)
- POST /api/v1/users/me/change-password: Change current user password
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db_reader, get_db_writer
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.common import ApiResponse
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdateRequest
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[UserResponse]:
    """Retrieve profile of the currently authenticated user."""
    profile = await UserService.get_profile(db=db, user_id=current_user.id)
    return ApiResponse(
        success=True,
        message="Profile retrieved successfully.",
        data=profile,
    )

@router.patch(
    "/me",
    response_model=ApiResponse[UserResponse],
)
async def update_my_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[UserResponse]:
    """Update profile fields (name, phone, avatar_url). Role or email escalation is strictly prohibited."""
    updated = await UserService.update_profile(db=db, user=current_user, data=payload)
    return ApiResponse(
        success=True,
        message="Profile updated successfully.",
        data=updated,
    )

@router.post(
    "/me/change-password",
    response_model=ApiResponse[MessageResponse],
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """Change current user's password and revoke active refresh tokens."""
    await UserService.change_password(db=db, user=current_user, data=payload)
    return ApiResponse(
        success=True,
        message="Password changed successfully.",
        data=MessageResponse(message="Password changed successfully."),
    )
