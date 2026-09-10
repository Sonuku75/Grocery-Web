from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.redis import CacheManager
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryResponse

class CategoryService:
    @classmethod
    async def get_all_categories(cls, db: AsyncSession) -> List[CategoryResponse]:
        cache_key = "cache:categories:all"
        cached = await CacheManager.get(cache_key)
        if cached:
            return [CategoryResponse(**item) for item in cached]

        async def fetch():
            # Query active categories ordered by sort_order
            stmt = (
                select(
                    Category,
                    func.count(Product.id).label("item_count"),
                )
                .outerjoin(Product, (Category.id == Product.category_id) & (Product.is_active == True))
                .where(Category.is_active == True)
                .group_by(Category.id)
                .order_by(Category.sort_order.asc())
            )
            res = await db.execute(stmt)
            rows = res.all()

            results = []
            for cat, count in rows:
                c_dict = {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "description": cat.description,
                    "icon": cat.icon,
                    "image_url": cat.image_url,
                    "sort_order": cat.sort_order,
                    "item_count": count or 0,
                }
                results.append(c_dict)
            return results

        data = await CacheManager.get_or_set(
            cache_key,
            fetch,
            ttl=settings.REDIS_CATEGORY_CACHE_TTL,
        )
        return [CategoryResponse(**item) for item in data]

    @classmethod
    async def get_by_slug(cls, db: AsyncSession, slug: str) -> CategoryResponse:
        cache_key = f"cache:category:{slug}"
        cached = await CacheManager.get(cache_key)
        if cached:
            return CategoryResponse(**cached)

        async def fetch():
            stmt = select(Category).where(Category.slug == slug, Category.is_active == True)
            res = await db.execute(stmt)
            cat = res.scalar_one_or_none()
            if not cat:
                raise NotFoundError("Category", slug)

            count_stmt = select(func.count(Product.id)).where(Product.category_id == cat.id, Product.is_active == True)
            count_res = await db.execute(count_stmt)
            item_count = count_res.scalar_one() or 0

            return {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "icon": cat.icon,
                "image_url": cat.image_url,
                "sort_order": cat.sort_order,
                "item_count": item_count,
            }

        data = await CacheManager.get_or_set(
            cache_key,
            fetch,
            ttl=settings.REDIS_CATEGORY_CACHE_TTL,
        )
        return CategoryResponse(**data)

    @classmethod
    async def create_category(cls, db: AsyncSession, data: CategoryCreate) -> Category:
        category = Category(
            id=data.id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            icon=data.icon,
            image_url=data.image_url,
            sort_order=data.sort_order,
            is_active=True,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        await CacheManager.delete("cache:categories:all")
        return category
