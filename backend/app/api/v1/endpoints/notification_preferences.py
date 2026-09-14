"""
Cartify Notification Preferences API Endpoints (Module 13)

Customer notification preference management:
- GET /api/v1/notification-preferences: Fetch preference matrix
- PUT /api/v1/notification-preferences: Update preference with mandatory security alerts check
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification_preference import (
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    UpdateNotificationPreferenceRequest,
)
from app.services.notification_preference_service import NotificationPreferenceService

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@router.get(
    "",
    response_model=ApiResponse[NotificationPreferencesResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Get user notification preferences",
)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[NotificationPreferencesResponse]:
    """Retrieves full category x channel preference matrix for authenticated user."""
    data = await NotificationPreferenceService.get_user_preferences(
        db=db, user_id=current_user.id
    )
    return ApiResponse(success=True, data=data)


@router.put(
    "",
    response_model=ApiResponse[NotificationPreferenceItem],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Update user notification preference",
)
async def update_preference(
    req: UpdateNotificationPreferenceRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[NotificationPreferenceItem]:
    """
    Updates an individual category x channel preference.
    Rejects any request attempting to disable mandatory security alerts with HTTP 400.
    """
    data = await NotificationPreferenceService.update_preference(
        db=db, user_id=current_user.id, request=req
    )
    return ApiResponse(
        success=True,
        data=data,
        message=f"Preference updated for {req.category} on {req.channel}",
    )
