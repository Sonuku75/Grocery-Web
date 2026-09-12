"""
Cartify Product Image Repository (Module 4)

Encapsulates database operations for product images:
- Primary image management and exclusivity
- Image ordering and removal
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_image import ProductImage


class ProductImageRepository:
    @classmethod
    async def list_by_product_id(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> List[ProductImage]:
        """Retrieves all images for a product ordered by sort_order."""
        query = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order.asc(), ProductImage.created_at.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        image_id: str,
    ) -> Optional[ProductImage]:
        """Retrieves image by UUID."""
        query = select(ProductImage).where(ProductImage.id == image_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def clear_primary_for_product(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> None:
        """Sets is_primary = False for all images of the given product."""
        stmt = (
            update(ProductImage)
            .where(ProductImage.product_id == product_id)
            .values(is_primary=False)
        )
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        data: Dict[str, Any],
    ) -> ProductImage:
        """Persists a new product image."""
        image = ProductImage(**data)
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        image: ProductImage,
        data: Dict[str, Any],
    ) -> ProductImage:
        """Updates image attributes."""
        for key, value in data.items():
            if hasattr(image, key) and key not in ("id", "created_at"):
                setattr(image, key, value)
        await db.commit()
        await db.refresh(image)
        return image

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        image: ProductImage,
    ) -> None:
        """Deletes image record."""
        await db.delete(image)
        await db.commit()
