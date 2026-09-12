"""
Cartify Product Variant Repository (Module 4)

Encapsulates database operations for product variants:
- SKU lookup and uniqueness enforcement
- Variant CRUD scoped to product parent
- Active/inactive filtering
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_variant import ProductVariant


class ProductVariantRepository:
    @classmethod
    async def list_by_product_id(
        cls,
        db: AsyncSession,
        product_id: str,
        active_only: bool = True,
    ) -> List[ProductVariant]:
        """Retrieves variants for a given product ordered by sort_order and price."""
        query = select(ProductVariant).where(ProductVariant.product_id == product_id)
        if active_only:
            query = query.where(ProductVariant.is_active.is_(True))
        query = query.order_by(ProductVariant.sort_order.asc(), ProductVariant.price.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        variant_id: str,
    ) -> Optional[ProductVariant]:
        """Retrieves a single variant by UUID."""
        query = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_sku(
        cls,
        db: AsyncSession,
        sku: str,
    ) -> Optional[ProductVariant]:
        """Retrieves variant by unique SKU string."""
        query = select(ProductVariant).where(ProductVariant.sku == sku.strip().upper())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def sku_exists(
        cls,
        db: AsyncSession,
        sku: str,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """Verifies if an uppercase SKU is already assigned to another variant."""
        query = select(ProductVariant.id).where(ProductVariant.sku == sku.strip().upper())
        if exclude_id:
            query = query.where(ProductVariant.id != exclude_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        data: Dict[str, Any],
    ) -> ProductVariant:
        """Persists a new product variant."""
        variant = ProductVariant(**data)
        db.add(variant)
        await db.commit()
        await db.refresh(variant)
        return variant

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        variant: ProductVariant,
        data: Dict[str, Any],
    ) -> ProductVariant:
        """Updates variant with allowed fields."""
        for key, value in data.items():
            if hasattr(variant, key) and key not in ("id", "created_at", "updated_at"):
                setattr(variant, key, value)
        await db.commit()
        await db.refresh(variant)
        return variant

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        variant: ProductVariant,
    ) -> None:
        """Deletes variant permanently."""
        await db.delete(variant)
        await db.commit()
