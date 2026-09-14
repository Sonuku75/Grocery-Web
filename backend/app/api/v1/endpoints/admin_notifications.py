"""
Cartify Admin Notifications API Endpoints (Module 13)

Administrative visibility and operations for notifications, deliveries, outbox, and templates:
- GET /api/v1/admin/notifications: System-wide notification listing
- GET /api/v1/admin/notifications/deliveries: Multi-channel delivery audits
- POST /api/v1/admin/notifications/process-outbox: Trigger background outbox batch processing
- GET /api/v1/admin/notifications/templates: List active templates
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, require_admin
from app.models.user import User
from app.repositories.notification import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.repositories.notification_template import NotificationTemplateRepository
from app.schemas.common import ApiResponse
from app.schemas.notification import (
    NotificationDeliveryResponse,
    NotificationResponse,
    NotificationTemplateResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])


@router.get(
    "",
    response_model=ApiResponse[List[NotificationResponse]],
    summary="Admin list all customer notifications",
)
async def admin_list_notifications(
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    user_id: Optional[str] = Query(None, alias="userId"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[List[NotificationResponse]]:
    """List notifications system-wide with status and type filters."""
    items, _ = await NotificationRepository.list_admin(
        db=db,
        limit=limit,
        offset=offset,
        status=status_filter,
        notification_type=type_filter,
        user_id=user_id,
    )
    return ApiResponse(
        success=True,
        data=[NotificationResponse.model_validate(it) for it in items],
    )


@router.get(
    "/deliveries",
    response_model=ApiResponse[List[NotificationDeliveryResponse]],
    summary="Admin list delivery attempts",
)
async def admin_list_deliveries(
    channel: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[List[NotificationDeliveryResponse]]:
    """Inspect delivery statuses across In-App, Email, SMS, and Push gateways."""
    items, _ = await NotificationDeliveryRepository.list_admin(
        db=db,
        limit=limit,
        offset=offset,
        channel=channel,
        status=status_filter,
    )
    return ApiResponse(
        success=True,
        data=[NotificationDeliveryResponse.model_validate(it) for it in items],
    )


@router.post(
    "/process-outbox",
    response_model=ApiResponse[dict],
    summary="Trigger outbox worker batch",
)
async def admin_process_outbox(
    batch_size: int = Query(50, ge=1, le=200),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """Manually triggers outbox processing for pending transactional events."""
    processed = await NotificationService.process_outbox_batch(db=db, limit=batch_size)
    return ApiResponse(
        success=True,
        data={"processedCount": processed},
        message=f"Processed {processed} outbox events",
    )


@router.get(
    "/templates",
    response_model=ApiResponse[List[NotificationTemplateResponse]],
    summary="Admin list notification templates",
)
async def admin_list_templates(
    channel: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[List[NotificationTemplateResponse]]:
    """Lists registered notification templates."""
    templates = await NotificationTemplateRepository.list_templates(
        db=db, channel=channel
    )
    return ApiResponse(
        success=True,
        data=[NotificationTemplateResponse.model_validate(t) for t in templates],
    )
