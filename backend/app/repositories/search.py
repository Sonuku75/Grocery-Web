"""
Cartify Search Repository (Module 5)

Encapsulates database access operations for search and discovery:
- Relevance-scored full-text/substring matching across product name, brand, category, and SKU
- Filter combinations: category hierarchy, brand, price range, active status
- Safe whitelisted sorting with variant price subqueries
- Keyset and opaque cursor pagination
- High-speed autocomplete suggestions for products, brands, and categories
"""

import base64
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import (
    and_,
    case,
    distinct,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.schemas.search import (
    SearchItem,
    SearchItemCategory,
    SearchResponse,
    SuggestionItem,
)


def encode_cursor(offset: int) -> str:
    raw = f"off:{offset}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> Optional[int]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        if raw.startswith("off:"):
            return int(raw.split(":", 1)[1])
    except Exception:
        pass
    return None


class SearchRepository:
    @classmethod
    async def search_products(
        cls,
        db: AsyncSession,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort: str = "relevance",
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Product], Optional[str], bool, int]:
        """
        Executes a relevance-ranked, filtered search query with cursor pagination.
        Returns: (items, next_cursor, has_more, total_count)
        """
        query_clean = q.strip().lower() if q and q.strip() else None

        # Base query with eager-loading
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.images),
            )
            .outerjoin(Category, Product.category_id == Category.id)
        )
        count_query = (
            select(func.count(distinct(Product.id)))
            .select_from(Product)
            .outerjoin(Category, Product.category_id == Category.id)
        )

        filters = [Product.is_active.is_(True)]

        relevance_col = None

        if query_clean:
            exact_name = func.lower(Product.name) == query_clean
            prefix_name = func.lower(Product.name).startswith(query_clean)
            contains_name = func.lower(Product.name).contains(query_clean)
            exact_brand = func.lower(Product.brand) == query_clean
            contains_brand = func.lower(Product.brand).contains(query_clean)
            cat_match = func.lower(Category.name).contains(query_clean)
            sku_match = select(ProductVariant.id).where(
                and_(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.is_active.is_(True),
                    func.lower(ProductVariant.sku).contains(query_clean),
                )
            ).exists()

            relevance_score = case(
                (exact_name, 100),
                (prefix_name, 80),
                (contains_name, 60),
                (exact_brand, 50),
                (contains_brand, 40),
                (cat_match, 20),
                (sku_match, 10),
                else_=0,
            )

            q_filter = or_(
                exact_name,
                prefix_name,
                contains_name,
                exact_brand,
                contains_brand,
                cat_match,
                sku_match,
            )
            filters.append(q_filter)
            relevance_col = relevance_score

        # Category hierarchy filter
        if category_id:
            subcat_ids_subquery = select(Category.id).where(Category.parent_id == category_id)
            filters.append(
                or_(
                    Product.category_id == category_id,
                    Product.category_id.in_(subcat_ids_subquery),
                )
            )

        # Brand filter
        if brand:
            filters.append(func.lower(Product.brand) == brand.strip().lower())

        # Price range filter on active variants
        if min_price is not None or max_price is not None:
            v_conditions = [
                ProductVariant.product_id == Product.id,
                ProductVariant.is_active.is_(True),
            ]
            if min_price is not None:
                v_conditions.append(ProductVariant.price >= min_price)
            if max_price is not None:
                v_conditions.append(ProductVariant.price <= max_price)

            filters.append(select(ProductVariant.id).where(and_(*v_conditions)).exists())

        # Apply filters to base query and count query
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

        # Scalar subquery for variant prices (used in sorting)
        variant_min_price = (
            select(func.min(ProductVariant.price))
            .where(
                and_(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.is_active.is_(True),
                )
            )
            .correlate(Product)
            .scalar_subquery()
        )

        # Apply sorting
        if sort == "price_low_to_high":
            query = query.order_by(variant_min_price.asc().nulls_last(), Product.id.asc())
        elif sort == "price_high_to_low":
            query = query.order_by(variant_min_price.desc().nulls_last(), Product.id.desc())
        elif sort == "newest":
            query = query.order_by(Product.created_at.desc(), Product.id.desc())
        elif sort == "featured":
            query = query.order_by(Product.is_featured.desc(), Product.created_at.desc(), Product.id.desc())
        else:
            # Default: relevance
            if relevance_col is not None:
                query = query.order_by(
                    relevance_col.desc(),
                    Product.is_featured.desc(),
                    Product.created_at.desc(),
                    Product.id.desc(),
                )
            else:
                query = query.order_by(
                    Product.is_featured.desc(),
                    Product.created_at.desc(),
                    Product.id.desc(),
                )

        # Parse cursor
        offset = 0
        if cursor:
            decoded_offset = decode_cursor(cursor)
            if decoded_offset is not None:
                offset = decoded_offset

        # Execute total count
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Execute pagination query (fetch limit + 1 to check has_more)
        paginated_query = query.offset(offset).limit(limit + 1)
        result = await db.execute(paginated_query)
        items = list(result.scalars().unique().all())

        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
            next_cursor = encode_cursor(offset + limit)
        else:
            next_cursor = None

        return items, next_cursor, has_more, total_count

    @classmethod
    async def get_suggestions(
        cls,
        db: AsyncSession,
        q: str,
        limit: int = 8,
    ) -> List[SuggestionItem]:
        """
        Retrieves autocomplete suggestions grouped across products, brands, and categories.
        """
        query_clean = q.strip().lower()
        if not query_clean:
            return []

        suggestions: List[SuggestionItem] = []

        # 1. Product suggestions (prefix match preferred, then substring)
        prod_query = (
            select(Product)
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
            .where(
                and_(
                    Product.is_active.is_(True),
                    func.lower(Product.name).contains(query_clean),
                )
            )
            .order_by(
                case(
                    (func.lower(Product.name).startswith(query_clean), 0),
                    else_=1,
                ),
                Product.name.asc(),
            )
            .limit(limit)
        )
        prod_result = await db.execute(prod_query)
        products = list(prod_result.scalars().unique().all())

        for p in products:
            active_variants = [v for v in p.variants if v.is_active]
            min_price = min((v.price for v in active_variants), default=None)
            primary_img = next((img.image_url for img in p.images if img.is_primary), p.image_url)

            suggestions.append(
                SuggestionItem(
                    type="product",
                    label=p.name,
                    slug=p.slug,
                    id=p.id,
                    price=min_price,
                    imageUrl=primary_img,
                )
            )
            if len(suggestions) >= limit:
                return suggestions

        # 2. Brand suggestions
        remaining_limit = max(0, limit - len(suggestions))
        if remaining_limit > 0:
            brand_query = (
                select(distinct(Product.brand))
                .where(
                    and_(
                        Product.is_active.is_(True),
                        func.lower(Product.brand).contains(query_clean),
                    )
                )
                .order_by(Product.brand.asc())
                .limit(min(remaining_limit, 3))
            )
            brand_result = await db.execute(brand_query)
            brands = list(brand_result.scalars().all())

            for b in brands:
                suggestions.append(
                    SuggestionItem(
                        type="brand",
                        label=b,
                    )
                )
                if len(suggestions) >= limit:
                    return suggestions

        # 3. Category suggestions
        remaining_limit = max(0, limit - len(suggestions))
        if remaining_limit > 0:
            cat_query = (
                select(Category)
                .where(
                    and_(
                        Category.is_active.is_(True),
                        func.lower(Category.name).contains(query_clean),
                    )
                )
                .order_by(Category.name.asc())
                .limit(min(remaining_limit, 3))
            )
            cat_result = await db.execute(cat_query)
            categories = list(cat_result.scalars().all())

            for c in categories:
                suggestions.append(
                    SuggestionItem(
                        type="category",
                        label=c.name,
                        slug=c.slug,
                        id=c.id,
                    )
                )
                if len(suggestions) >= limit:
                    return suggestions

        return suggestions
