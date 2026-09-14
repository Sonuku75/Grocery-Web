"""
Cartify Push Device Registration API Endpoints (Module 13)

Endpoints for registering mobile and web push notification devices:
- POST /api/v1/devices: Register or update device token
- GET /api/v1/devices: List active devices for authenticated customer
- DELETE /api/v1/devices/{device_id}: Deactivate device on logout/removal (IDOR safe)
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.device import (
    DeviceListResponse,
    DeviceResponse,
    RegisterDeviceRequest,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/devices", tags=["Push Devices"])


@router.post(
    "",
    response_model=ApiResponse[DeviceResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Register push device token",
)
async def register_device(
    request: RegisterDeviceRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[DeviceResponse]:
    """Registers push token for user device. Returns device data with masked token."""
    data = await NotificationService.register_device(
        db=db, user_id=current_user.id, request=request
    )
    return ApiResponse(
        success=True,
        data=data,
        message="Device registered successfully for push notifications",
    )


@router.get(
    "",
    response_model=ApiResponse[DeviceListResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="List customer registered devices",
)
async def list_devices(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[DeviceListResponse]:
    """Lists registered devices for current user with masked tokens."""
    data = await NotificationService.list_user_devices(db=db, user_id=current_user.id)
    return ApiResponse(success=True, data=data)


@router.delete(
    "/{device_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Deactivate push device",
)
async def deactivate_device(
    device_id: str = Path(..., description="Device UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """Deactivates device token. Fails with 404 if device does not belong to user."""
    await NotificationService.deactivate_device(
        db=db, device_id=device_id, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data={"deviceId": device_id},
        message="Device deactivated successfully",
    )
