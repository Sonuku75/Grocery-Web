import base64
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.redis import CacheManager
from app.models.category import Category
from app.models.product import Product
from app.schemas.common import CursorPage
from app.schemas.product import ProductCreate, ProductFilterParams, ProductResponse, ProductUpdate

def encode_cursor(created_at: datetime, item_id: str) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")

def decode_cursor(cursor: str) -> Tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        parts = raw.split("|", 1)
        return datetime.fromisoformat(parts[0]), parts[1]
    except Exception:
        raise ValueError("Invalid cursor format")

class ProductService:
    @staticmethod
    def _generate_cache_key(prefix: str, params: Dict[str, Any]) -> str:
        serialized = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.md5(serialized.encode("utf-8")).hexdigest()
        return f"cache:products:{prefix}:{digest}"

    @classmethod
    async def get_products_keyset(
        cls,
        db: AsyncSession,
        filters: ProductFilterParams,
    ) -> CursorPage[ProductResponse]:
        """
        Retrieves products using high-performance Keyset (Cursor) Pagination.
        Leverages Redis Cache-Aside with stampede protection.
        """
        cache_key = cls._generate_cache_key("keyset", filters.model_dump())
        cached = await CacheManager.get(cache_key)
        if cached:
            return CursorPage[ProductResponse](**cached)

        async def fetch_from_db():
            stmt = select(
                Product,
                Category.name.label("category_name"),
            ).outerjoin(
                Category, Product.category_id == Category.id
            ).where(
                Product.is_active == True
            )

            # Filtering using composite indexes
            if filters.category:
                stmt = stmt.where(
                    or_(
                        Product.category_id == filters.category,
                        Category.slug == filters.category,
                    )
                )
            if filters.brand:
                stmt = stmt.where(Product.brand.ilike(f"%{filters.brand}%"))
            if filters.min_price is not None:
                stmt = stmt.where(Product.price >= filters.min_price)
            if filters.max_price is not None:
                stmt = stmt.where(Product.price <= filters.max_price)
            if filters.min_rating is not None:
                stmt = stmt.where(Product.rating >= filters.min_rating)
            if filters.in_stock is not None:
                stmt = stmt.where(Product.in_stock == filters.in_stock)
            if filters.search:
                pattern = f"%{filters.search}%"
                stmt = stmt.where(
                    or_(
                        Product.name.ilike(pattern),
                        Product.brand.ilike(pattern),
                        Product.description.ilike(pattern),
                    )
                )

            # Keyset pagination clause: (created_at < cursor_time OR (created_at == cursor_time AND id < cursor_id))
            if filters.cursor:
                try:
                    c_time, c_id = decode_cursor(filters.cursor)
                    stmt = stmt.where(
                        or_(
                            Product.created_at < c_time,
                            and_(Product.created_at == c_time, Product.id < c_id),
                        )
                    )
                except ValueError:
                    pass

            stmt = stmt.order_by(Product.created_at.desc(), Product.id.desc())
            stmt = stmt.limit(filters.limit + 1)

            result = await db.execute(stmt)
            rows = result.all()

            has_more = len(rows) > filters.limit
            items_slice = rows[: filters.limit]

            product_responses = []
            for p, cat_name in items_slice:
                resp = ProductResponse(
                    id=p.id,
                    name=p.name,
                    slug=p.slug,
                    brand=p.brand,
                    category_id=p.category_id,
                    category_name=cat_name,
                    description=p.description,
                    specifications=p.specifications or {},
                    price=p.price,
                    original_price=p.original_price,
                    discount_percent=p.discount_percent,
                    unit=p.unit,
                    stock=p.stock,
                    rating=p.rating,
                    rating_count=p.rating_count,
                    images=p.images or [],
                    tags=p.tags or [],
                    is_popular=p.is_popular,
                    is_featured=p.is_featured,
                    is_deal=p.is_deal,
                    in_stock=p.in_stock,
                )
                product_responses.append(resp.model_dump())

            next_cursor = None
            if has_more and items_slice:
                last_p, _ = items_slice[-1]
                next_cursor = encode_cursor(last_p.created_at, last_p.id)

            return {
                "items": product_responses,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": filters.limit,
            }

        page_data = await CacheManager.get_or_set(
            cache_key,
            fetch_from_db,
            ttl=settings.REDIS_PRODUCT_CACHE_TTL,
        )
        return CursorPage[ProductResponse](**page_data)

    @classmethod
    async def get_by_id_or_slug(
        cls,
        db: AsyncSession,
        identifier: str,
    ) -> ProductResponse:
        cache_key = f"cache:product:{identifier}"
        cached = await CacheManager.get(cache_key)
        if cached:
            return ProductResponse(**cached)

        async def fetch_single():
            stmt = select(
                Product,
                Category.name.label("category_name"),
            ).outerjoin(
                Category, Product.category_id == Category.id
            ).where(
                or_(Product.id == identifier, Product.slug == identifier),
                Product.is_active == True,
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                raise NotFoundError("Product", identifier)
            p, cat_name = row
            resp = ProductResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                brand=p.brand,
                category_id=p.category_id,
                category_name=cat_name,
                description=p.description,
                specifications=p.specifications or {},
                price=p.price,
                original_price=p.original_price,
                discount_percent=p.discount_percent,
                unit=p.unit,
                stock=p.stock,
                rating=p.rating,
                rating_count=p.rating_count,
                images=p.images or [],
                tags=p.tags or [],
                is_popular=p.is_popular,
                is_featured=p.is_featured,
                is_deal=p.is_deal,
                in_stock=p.in_stock,
            )
            return resp.model_dump()

        data = await CacheManager.get_or_set(
            cache_key,
            fetch_single,
            ttl=settings.REDIS_PRODUCT_CACHE_TTL,
        )
        return ProductResponse(**data)

    @classmethod
    async def create_product(
        cls,
        db: AsyncSession,
        data: ProductCreate,
    ) -> Product:
        product = Product(
            id=data.id,
            name=data.name,
            slug=data.slug,
            brand=data.brand,
            category_id=data.category_id,
            description=data.description,
            specifications=data.specifications,
            price=data.price,
            original_price=data.original_price,
            discount_percent=data.discount_percent,
            unit=data.unit,
            stock=data.stock,
            rating=data.rating,
            rating_count=data.rating_count,
            images=data.images,
            tags=data.tags,
            is_popular=data.is_popular,
            is_featured=data.is_featured,
            is_deal=data.is_deal,
            in_stock=data.stock > 0,
            is_active=True,
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)

        # Invalidate listing caches
        await CacheManager.delete_pattern("cache:products:*")
        return product

    @classmethod
    async def update_product(
        cls,
        db: AsyncSession,
        product_id: str,
        data: ProductUpdate,
    ) -> Product:
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundError("Product", product_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "stock" in update_dict and "in_stock" not in update_dict:
            update_dict["in_stock"] = update_dict["stock"] > 0

        for key, val in update_dict.items():
            setattr(product, key, val)

        await db.commit()
        await db.refresh(product)

        # Invalidate specific product cache & listings
        await CacheManager.delete(f"cache:product:{product.id}")
        await CacheManager.delete(f"cache:product:{product.slug}")
        await CacheManager.delete_pattern("cache:products:*")
        return product
