"""
Cartify Address Endpoints (Module 2)

Endpoints:
- POST /api/v1/addresses: Create delivery address
- GET /api/v1/addresses: List current user's delivery addresses
- GET /api/v1/addresses/{address_id}: Get single address
- PATCH /api/v1/addresses/{address_id}: Update address
- DELETE /api/v1/addresses/{address_id}: Delete address
- PATCH /api/v1/addresses/{address_id}/default: Set address as default
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, rate_limit
from app.core.database import get_db_reader, get_db_writer
from app.models.user import User
from app.schemas.address import (
    AddressCreateRequest,
    AddressListResponse,
    AddressResponse,
    AddressUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.services.address import AddressService

router = APIRouter(prefix="/addresses", tags=["Addresses"])

@router.post(
    "",
    response_model=ApiResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
)
async def create_address(
    payload: AddressCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AddressResponse]:
    """
    Create a new delivery address for the authenticated user.
    The user_id is strictly derived from authentication context.
    """
    address = await AddressService.create_address(
        db=db, user_id=current_user.id, data=payload
    )
    return ApiResponse(
        success=True,
        message="Address created successfully.",
        data=address,
    )

@router.get(
    "",
    response_model=ApiResponse[AddressListResponse],
)
async def list_addresses(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AddressListResponse]:
    """List all delivery addresses owned by the authenticated user."""
    addresses = await AddressService.list_addresses(db=db, user_id=current_user.id)
    return ApiResponse(
        success=True,
        message="Addresses retrieved successfully.",
        data=addresses,
    )

@router.get(
    "/{address_id}",
    response_model=ApiResponse[AddressResponse],
)
async def get_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AddressResponse]:
    """
    Retrieve a specific address.
    Strictly verifies ownership, returning 404 if not found or unauthorized.
    """
    address = await AddressService.get_address(
        db=db, address_id=address_id, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        message="Address retrieved successfully.",
        data=address,
    )

@router.patch(
    "/{address_id}",
    response_model=ApiResponse[AddressResponse],
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
)
async def update_address(
    address_id: str,
    payload: AddressUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AddressResponse]:
    """Update delivery address details with ownership enforcement."""
    address = await AddressService.update_address(
        db=db, address_id=address_id, user_id=current_user.id, data=payload
    )
    return ApiResponse(
        success=True,
        message="Address updated successfully.",
        data=address,
    )

@router.delete(
    "/{address_id}",
    response_model=ApiResponse[dict],
)
async def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """Delete a delivery address with automatic default address promotion."""
    await AddressService.delete_address(
        db=db, address_id=address_id, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        message="Address deleted successfully.",
        data={"id": address_id},
    )

@router.patch(
    "/{address_id}/default",
    response_model=ApiResponse[AddressResponse],
)
async def set_default_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AddressResponse]:
    """Atomically set an address as the default delivery address."""
    address = await AddressService.set_default_address(
        db=db, address_id=address_id, user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        message="Default address updated successfully.",
        data=address,
    )
