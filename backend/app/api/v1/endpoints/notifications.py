"""
Cartify Notifications API Endpoints (Module 13)

Customer in-app notification center endpoints:
- GET /api/v1/notifications: Paginated notifications with cursor support & unread count
- GET /api/v1/notifications/unread-count: Quick unread count for UI badges
- PATCH /api/v1/notifications/{notification_id}/read: Mark single notification read (IDOR protected)
- POST /api/v1/notifications/read-all: Mark all notifications read
- DELETE /api/v1/notifications/{notification_id}: Delete notification (IDOR protected)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=ApiResponse[NotificationListResponse],
    dependencies=[Depends(rate_limit(limit=100, window_seconds=60))],
    summary="List customer notifications",
)
async def list_notifications(
    unread_only: bool = Query(False, alias="unreadOnly"),
    notification_type: Optional[str] = Query(None, alias="type"),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[NotificationListResponse]:
    """
    Returns paginated notifications for authenticated user.
    Enforces strict user scoping (IDOR safe).
    """
    data = await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        cursor=cursor,
    )
    return ApiResponse(success=True, data=data)


@router.get(
    "/unread-count",
    response_model=ApiResponse[UnreadCountResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Get unread notifications count",
)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[UnreadCountResponse]:
    """Returns number of unread notifications for badge display."""
    data = await NotificationService.get_unread_count(db=db, user_id=current_user.id)
    return ApiResponse(success=True, data=data)


@router.patch(
    "/{notification_id}/read",
    response_model=ApiResponse[NotificationResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Mark single notification as read",
)
async def mark_notification_as_read(
    notification_id: str = Path(..., description="Notification UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[NotificationResponse]:
    """Marks notification as read. Fails with 404 if notification does not belong to user."""
    data = await NotificationService.mark_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    return ApiResponse(success=True, data=data, message="Notification marked as read")


@router.post(
    "/read-all",
    response_model=ApiResponse[dict],
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
    summary="Mark all notifications as read",
)
async def mark_all_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """Marks all unread notifications for the user as read."""
    updated_count = await NotificationService.mark_all_as_read(
        db=db, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data={"updatedCount": updated_count},
        message=f"{updated_count} notifications marked as read",
    )


@router.delete(
    "/{notification_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Delete customer notification",
)
async def delete_notification(
    notification_id: str = Path(..., description="Notification UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """Permanently deletes notification for the authenticated customer."""
    await NotificationService.delete_notification(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data={"notificationId": notification_id},
        message="Notification deleted successfully",
    )
