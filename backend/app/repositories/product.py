"""
Cartify Product Repository (Module 4)

Encapsulates database access operations for products:
- Keyset cursor pagination and whitelisted sorting
- Eager loading of variants, images, and category
- Active/inactive filtering for public vs admin contexts
- Slug collision existence checks
"""

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant


def encode_cursor(created_at: datetime, item_id: str) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> Optional[Tuple[datetime, str]]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        parts = raw.split("|", 1)
        if len(parts) == 2:
            return datetime.fromisoformat(parts[0]), parts[1]
    except Exception:
        pass
    return None


class ProductRepository:
    @classmethod
    async def list_products(
        cls,
        db: AsyncSession,
        active_only: bool = True,
        category_id: Optional[str] = None,
        subcategory_id: Optional[str] = None,
        brand: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sort: str = "newest",
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Product], Optional[str], bool, int]:
        """
        Retrieves products using scalable keyset cursor pagination and whitelisted sorting.
        Returns: (items, next_cursor, has_more, total_count)
        """
        # Base query with eager-loading to avoid N+1 queries
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        count_query = select(func.count(Product.id))

        filters = []
        if active_only:
            filters.append(Product.is_active.is_(True))

        target_cat = subcategory_id or category_id
        if target_cat:
            # Also match if target_cat is parent of subcategories
            subcat_ids_stmt = select(Category.id).where(Category.parent_id == target_cat)
            filters.append(
                or_(
                    Product.category_id == target_cat,
                    Product.category_id.in_(subcat_ids_stmt),
                )
            )

        if brand:
            filters.append(func.lower(Product.brand) == brand.strip().lower())

        if is_featured is not None:
            filters.append(Product.is_featured.is_(is_featured))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Total count
        total_res = await db.execute(count_query)
        total = total_res.scalar_one() or 0

        # Keyset cursor filtering
        if cursor and sort == "newest":
            decoded = decode_cursor(cursor)
            if decoded:
                c_time, c_id = decoded
                query = query.where(
                    or_(
                        Product.created_at < c_time,
                        and_(Product.created_at == c_time, Product.id < c_id),
                    )
                )

        # Sorting logic
        if sort == "price_low_to_high":
            min_price_subq = (
                select(func.min(ProductVariant.price))
                .where(ProductVariant.product_id == Product.id)
                .where(ProductVariant.is_active.is_(True))
                .scalar_subquery()
            )
            query = query.order_by(min_price_subq.asc(), Product.id.asc())
        elif sort == "price_high_to_low":
            max_price_subq = (
                select(func.max(ProductVariant.price))
                .where(ProductVariant.product_id == Product.id)
                .where(ProductVariant.is_active.is_(True))
                .scalar_subquery()
            )
            query = query.order_by(max_price_subq.desc(), Product.id.asc())
        elif sort == "featured":
            query = query.order_by(
                Product.is_featured.desc(),
                Product.created_at.desc(),
                Product.id.desc(),
            )
        else:  # newest
            query = query.order_by(Product.created_at.desc(), Product.id.desc())

        # Fetch limit + 1 to check for has_more
        query = query.limit(limit + 1)
        result = await db.execute(query)
        records = list(result.scalars().all())

        has_more = len(records) > limit
        items = records[:limit]

        next_cursor = None
        if has_more and items and sort == "newest":
            last_item = items[-1]
            next_cursor = encode_cursor(last_item.created_at, last_item.id)

        return items, next_cursor, has_more, total

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        product_id: str,
        active_only: bool = True,
    ) -> Optional[Product]:
        """Retrieves single product with all relationships eager-loaded."""
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.images),
            )
            .where(Product.id == product_id)
        )
        if active_only:
            query = query.where(Product.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_slug(
        cls,
        db: AsyncSession,
        slug: str,
        active_only: bool = True,
    ) -> Optional[Product]:
        """Retrieves single product by unique URL slug."""
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.images),
            )
            .where(Product.slug == slug)
        )
        if active_only:
            query = query.where(Product.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def slug_exists(
        cls,
        db: AsyncSession,
        slug: str,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """Checks if a slug is already taken by another product."""
        query = select(Product.id).where(Product.slug == slug)
        if exclude_id:
            query = query.where(Product.id != exclude_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create(cls, db: AsyncSession, data: Dict[str, Any]) -> Product:
        """Persists a new product."""
        product = Product(**data)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        product: Product,
        data: Dict[str, Any],
    ) -> Product:
        """Updates product with allowed fields."""
        for key, value in data.items():
            if hasattr(product, key) and key not in ("id", "created_at", "updated_at"):
                setattr(product, key, value)
        await db.commit()
        await db.refresh(product)
        return product
