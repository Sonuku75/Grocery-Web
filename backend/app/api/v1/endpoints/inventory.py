"""
Cartify Customer Inventory API (Module 11)

Customer-facing inventory availability endpoint:
- Real-time stock status check for product variants
- Safe projection: exposes only available_quantity, is_available, is_low_stock
- Rate-limited and validated against inactive or missing variants
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, rate_limit
from app.schemas.common import ApiResponse
from app.schemas.inventory import CustomerInventoryResponse
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get(
    "/variants/{variant_id}",
    response_model=ApiResponse[CustomerInventoryResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Get customer-safe variant stock availability",
)
async def get_variant_availability(
    variant_id: str = Path(..., description="Product variant UUID"),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CustomerInventoryResponse]:
    """
    Returns customer-safe availability information for a specific product variant:
    - Verifies that variant and parent product exist and are active
    - Returns available_quantity, is_available, and is_low_stock flags
    """
    availability = await InventoryService.get_customer_stock(db, variant_id)
    return ApiResponse[CustomerInventoryResponse](
        success=True,
        data=availability,
        message="Variant availability retrieved successfully.",
    )
