"""
Cartify Search Service (Module 5)

Encapsulates business logic for search and discovery:
- Query normalization and input validation
- Redis cache-aside for high-speed autocomplete suggestions
- Authoritative pricing and discount transformation from active variants
- Safe cursor pagination management
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import CacheManager
from app.models.product import Product
from app.repositories.search import SearchRepository
from app.schemas.search import (
    SearchFilterParams,
    SearchItem,
    SearchItemCategory,
    SearchResponse,
    SearchSuggestionParams,
    SearchSuggestionResponse,
    SuggestionItem,
)


class SearchService:
    SUGGESTION_CACHE_PREFIX = "cache:search:sug:"
    SUGGESTION_CACHE_TTL = 300  # 5 minutes

    @classmethod
    def _format_search_item(cls, product: Product) -> SearchItem:
        """
        Transforms a Product entity into a platform-agnostic SearchItem.
        Extracts authoritative pricing from active variants.
        """
        active_variants = [v for v in product.variants if v.is_active] if product.variants else []
        if active_variants:
            # Sort by price ascending to select lead/starting price
            sorted_variants = sorted(active_variants, key=lambda v: (v.price, v.sort_order))
            lead_variant = sorted_variants[0]
            price = lead_variant.price
            mrp = lead_variant.mrp
            discount = lead_variant.discount_percentage
            unit = f"{lead_variant.unit_value} {lead_variant.unit_type}".strip()
        else:
            price = Decimal("0.00")
            mrp = Decimal("0.00")
            discount = Decimal("0.00")
            unit = None

        # Find primary image or product image_url
        images = product.images or []
        primary_image = next((img.image_url for img in images if img.is_primary), product.image_url)

        category_item = None
        if product.category:
            category_item = SearchItemCategory(
                id=product.category.id,
                name=product.category.name,
                slug=product.category.slug,
            )

        return SearchItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            brand=product.brand,
            image_url=primary_image,
            price=price,
            mrp=mrp,
            discount_percentage=discount,
            unit=unit,
            is_featured=product.is_featured,
            category=category_item,
        )

    @classmethod
    async def search_products(
        cls,
        db: AsyncSession,
        filters: SearchFilterParams,
    ) -> SearchResponse:
        """
        Searches active products with relevance ranking, filters, sorting, and cursor pagination.
        """
        items, next_cursor, has_more, total = await SearchRepository.search_products(
            db=db,
            q=filters.q,
            category_id=filters.category_id,
            brand=filters.brand,
            min_price=filters.min_price,
            max_price=filters.max_price,
            sort=filters.sort,
            limit=filters.limit,
            cursor=filters.cursor,
        )

        formatted_items = [cls._format_search_item(p) for p in items]

        return SearchResponse(
            query=filters.q,
            items=formatted_items,
            next_cursor=next_cursor,
            has_more=has_more,
            total=total,
        )

    @classmethod
    async def get_suggestions(
        cls,
        db: AsyncSession,
        params: SearchSuggestionParams,
    ) -> SearchSuggestionResponse:
        """
        Provides fast autocomplete suggestions with Redis cache-aside.
        """
        normalized_q = params.q.strip().lower()
        cache_key = f"{cls.SUGGESTION_CACHE_PREFIX}{normalized_q}:{params.limit}"

        # 1. Attempt cache retrieval
        cached = await CacheManager.get(cache_key)
        if cached:
            try:
                return SearchSuggestionResponse.model_validate(cached)
            except Exception:
                pass

        # 2. Database retrieval
        items = await SearchRepository.get_suggestions(
            db=db,
            q=normalized_q,
            limit=params.limit,
        )

        response = SearchSuggestionResponse(items=items)

        # 3. Store in cache
        try:
            await CacheManager.set(
                cache_key,
                response.model_dump(mode="json"),
                ttl_seconds=cls.SUGGESTION_CACHE_TTL,
            )
        except Exception:
            pass

        return response
