"""
Cartify Wishlist Service (Module 6)

Domain business logic for customer wishlist management:
- Authoritative user scoping: prevents IDOR and cross-user data leakage
- Concurrency & race condition safety: handles simultaneous duplicate requests cleanly via DB unique constraints
- Eager joins and product aggregate formatting to eliminate N+1 queries
- Keyset cursor pagination and total wishlist count computation
"""

import logging
from typing import Optional
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.models.wishlist import WishlistItem
from app.repositories.product import ProductRepository
from app.repositories.wishlist import WishlistRepository
from app.schemas.category import CategoryResponse
from app.schemas.product_image import ProductImageResponse
from app.schemas.product_variant import ProductVariantResponse
from app.schemas.wishlist import (
    WishlistCheckResponse,
    WishlistItemResponse,
    WishlistProductResponse,
    WishlistRemoveResponse,
    WishlistResponse,
)
from app.services.product_service import ProductService

logger = logging.getLogger("cartify.wishlist")


class WishlistService:
    @classmethod
    def _format_wishlist_product(cls, product: Product) -> WishlistProductResponse:
        """Transforms a Product ORM instance into a WishlistProductResponse with calculated aggregates."""
        summary = ProductService._format_product_summary(product)
        category_resp = None
        if product.category:
            category_resp = CategoryResponse(
                id=product.category.id,
                name=product.category.name,
                slug=product.category.slug,
                description=product.category.description,
                icon=getattr(product.category, "icon", None) or "Compass",
                image_url=getattr(product.category, "image_url", None),
                parent_id=getattr(product.category, "parent_id", None),
                is_active=getattr(product.category, "is_active", True),
                sort_order=getattr(product.category, "sort_order", 0) if getattr(product.category, "sort_order", 0) is not None else 0,
            )

        return WishlistProductResponse(
            id=summary.id,
            name=summary.name,
            slug=summary.slug,
            brand=summary.brand,
            description=summary.description,
            short_description=summary.short_description,
            image_url=summary.image_url,
            is_active=summary.is_active,
            is_featured=summary.is_featured,
            min_price=summary.min_price,
            min_mrp=summary.min_mrp,
            max_discount_percentage=summary.max_discount_percentage,
            primary_variant=summary.primary_variant,
            variants=summary.variants,
            images=summary.images,
            category=category_resp,
            category_id=summary.category_id,
            rating=4.8,
            rating_count=120,
        )

    @classmethod
    def _format_wishlist_item(cls, item: WishlistItem) -> WishlistItemResponse:
        """Transforms a WishlistItem ORM instance into a WishlistItemResponse."""
        product_resp = cls._format_wishlist_product(item.product)
        return WishlistItemResponse(
            id=item.id,
            product_id=item.product_id,
            product=product_resp,
            created_at=item.created_at,
        )

    @classmethod
    async def get_user_wishlist(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> WishlistResponse:
        """
        Retrieves the authenticated user's wishlist using keyset cursor pagination.
        Never returns items belonging to other users.
        """
        items, next_cursor, has_more, count = await WishlistRepository.list_user_wishlist(
            db=db,
            user_id=user_id,
            limit=limit,
            cursor=cursor,
        )

        formatted_items = [cls._format_wishlist_item(i) for i in items if i.product]
        return WishlistResponse(
            items=formatted_items,
            count=count,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @classmethod
    async def add_item(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
    ) -> WishlistItemResponse:
        """
        Adds a product to the authenticated user's wishlist.
        - Validates product existence (404 if missing)
        - Validates product active status (400 if inactive)
        - Gracefully recovers from duplicate requests / race conditions without 500 errors
        """
        # 1. Validate product exists
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        # 2. Validate product active status
        if not product.is_active:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Cannot add inactive product '{product.name}' to wishlist.",
                code="PRODUCT_INACTIVE",
            )

        # 3. Check if already wishlisted
        existing = await WishlistRepository.get_by_user_and_product(db, user_id, product_id)
        if existing:
            return cls._format_wishlist_item(existing)

        # 4. Create and commit with race condition safety
        try:
            await WishlistRepository.create(db, user_id, product_id)
            await db.commit()
            item = await WishlistRepository.get_by_user_and_product(db, user_id, product_id)
            logger.info("Product '%s' added to wishlist for user '%s'", product_id, user_id)
            return cls._format_wishlist_item(item)
        except IntegrityError:
            await db.rollback()
            # Concurrently created by another in-flight request
            item = await WishlistRepository.get_by_user_and_product(db, user_id, product_id)
            if item:
                return cls._format_wishlist_item(item)
            raise

    @classmethod
    async def remove_item(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
    ) -> WishlistRemoveResponse:
        """
        Removes a product from the user's wishlist.
        Scoped strictly to user_id. Idempotent: returns cleanly even if not found.
        """
        deleted = await WishlistRepository.delete(db, user_id, product_id)
        await db.commit()
        if deleted:
            logger.info("Product '%s' removed from wishlist for user '%s'", product_id, user_id)
        return WishlistRemoveResponse(
            product_id=product_id,
            removed=deleted,
            message="Product removed from wishlist" if deleted else "Product was not in wishlist",
        )

    @classmethod
    async def check_item(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
    ) -> WishlistCheckResponse:
        """Lightweight endpoint for ProductCard and ProductDetail wishlisted status."""
        is_wished = await WishlistRepository.is_wishlisted(db, user_id, product_id)
        return WishlistCheckResponse(product_id=product_id, is_wishlisted=is_wished)

    @classmethod
    async def count_user_wishlist(cls, db: AsyncSession, user_id: str) -> int:
        """Returns total active count of items in user's wishlist."""
        return await WishlistRepository.count_user_wishlist(db, user_id)
