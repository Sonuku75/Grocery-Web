"""
Cartify Category Service (Module 3)

Domain business logic for categories & subcategories:
- Clean URL-safe slug generation with collision handling
- Hierarchy validation (no self-parenting, no circular hierarchy, 2-level limit)
- Active-only filtering for customer endpoints vs admin visibility
- Safe deactivation & dependent child checking
- Redis cache-aside with automated invalidation
"""

import logging
import re
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import CartifyException, NotFoundError
from app.core.redis import CacheManager
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)

logger = logging.getLogger("cartify.categories")


def slugify(text: str) -> str:
    """Converts display text into a clean URL-safe slug."""
    # Replace ampersand with "and"
    text = text.replace("&", "and")
    # Lowercase and replace non-alphanumeric chars with hyphens
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading and trailing hyphens
    slug = text.strip("-")
    return slug or "category"


class CategoryService:
    CACHE_KEY_TOP_LEVEL = "cache:categories:top_level"
    CACHE_PATTERN = "cache:categories:*"

    @classmethod
    async def _invalidate_cache(cls) -> None:
        """Invalidates all cached category responses in Redis."""
        try:
            await CacheManager.delete_pattern(cls.CACHE_PATTERN)
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")

    @classmethod
    async def list_categories(
        cls,
        db: AsyncSession,
        active_only: bool = True,
        include_subcategories: bool = False,
        limit: int = 100,
        skip: int = 0,
    ) -> CategoryListResponse:
        """
        Lists top-level categories.
        Customer requests (active_only=True) are served via Redis cache when possible.
        """
        cache_key = f"{cls.CACHE_KEY_TOP_LEVEL}:{active_only}:{include_subcategories}:{limit}:{skip}"
        if active_only:
            try:
                cached = await CacheManager.get(cache_key)
                if cached:
                    return CategoryListResponse(**cached)
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")

        categories = await CategoryRepository.list_top_level(
            db, active_only=active_only, limit=limit, skip=skip
        )
        total = await CategoryRepository.count_top_level(db, active_only=active_only)

        items: List[CategoryResponse] = []
        for cat in categories:
            resp = CategoryResponse.model_validate(cat)
            if include_subcategories:
                active_subs = [
                    CategoryResponse.model_validate(sub)
                    for sub in cat.children
                    if (not active_only or sub.is_active)
                ]
                resp.subcategories = active_subs
            else:
                resp.subcategories = None
            items.append(resp)

        result = CategoryListResponse(items=items, total=total)

        if active_only:
            try:
                await CacheManager.set(
                    cache_key,
                    result.model_dump(mode="json"),
                    ttl=settings.REDIS_CATEGORY_CACHE_TTL,
                )
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")

        return result

    @classmethod
    async def get_category_by_id(
        cls,
        db: AsyncSession,
        category_id: str,
        active_only: bool = True,
    ) -> CategoryResponse:
        """Retrieves a single category by ID, including its direct subcategories."""
        category = await CategoryRepository.get_by_id(db, category_id, active_only=active_only)
        if not category:
            raise NotFoundError("Category", category_id)

        resp = CategoryResponse.model_validate(category)
        active_subs = [
            CategoryResponse.model_validate(sub)
            for sub in category.children
            if (not active_only or sub.is_active)
        ]
        resp.subcategories = active_subs
        return resp

    @classmethod
    async def get_category_by_slug(
        cls,
        db: AsyncSession,
        slug: str,
        active_only: bool = True,
    ) -> CategoryResponse:
        """Retrieves a category by URL slug, including its direct subcategories."""
        category = await CategoryRepository.get_by_slug(db, slug, active_only=active_only)
        if not category:
            raise NotFoundError("Category", slug)

        resp = CategoryResponse.model_validate(category)
        active_subs = [
            CategoryResponse.model_validate(sub)
            for sub in category.children
            if (not active_only or sub.is_active)
        ]
        resp.subcategories = active_subs
        return resp

    @classmethod
    async def list_subcategories(
        cls,
        db: AsyncSession,
        category_id: str,
        active_only: bool = True,
    ) -> CategoryListResponse:
        """Retrieves direct subcategories for a given parent category ID."""
        parent = await CategoryRepository.get_by_id(db, category_id, active_only=active_only)
        if not parent:
            raise NotFoundError("Category", category_id)

        subcategories = await CategoryRepository.list_subcategories(
            db, category_id, active_only=active_only
        )
        items = [CategoryResponse.model_validate(s) for s in subcategories]
        return CategoryListResponse(items=items, total=len(items))

    @classmethod
    async def _generate_unique_slug(
        cls,
        db: AsyncSession,
        base_name: str,
        exclude_id: Optional[str] = None,
    ) -> str:
        """Generates a unique URL-safe slug from category name, appending numbers on collision."""
        base_slug = slugify(base_name)
        candidate = base_slug
        counter = 2

        while await CategoryRepository.slug_exists(db, candidate, exclude_id=exclude_id):
            candidate = f"{base_slug}-{counter}"
            counter += 1

        return candidate

    @classmethod
    async def _validate_parent_hierarchy(
        cls,
        db: AsyncSession,
        parent_id: Optional[str],
        category_id: Optional[str] = None,
    ) -> Optional[Category]:
        """
        Validates parent hierarchy rules:
        1. Self-parenting forbidden
        2. Parent must exist in DB
        3. 2-level hierarchy limit: parent cannot itself be a subcategory (no 3+ levels)
        4. Cycle detection: parent chain cannot loop back to category_id
        """
        if not parent_id:
            return None

        if category_id and parent_id == category_id:
            raise CartifyException(
                status_code=400,
                message="A category cannot be its own parent.",
                code="INVALID_PARENT_CATEGORY",
            )

        parent = await CategoryRepository.get_by_id(db, parent_id)
        if not parent:
            raise CartifyException(
                status_code=404,
                message=f"Parent category with id '{parent_id}' does not exist.",
                code="INVALID_PARENT_CATEGORY",
            )

        if category_id:
            # Check if parent or its ancestors lead back to category_id (cycle check)
            curr = parent
            while curr:
                if curr.id == category_id or curr.parent_id == category_id:
                    raise CartifyException(
                        status_code=400,
                        message="Circular reference detected in category hierarchy.",
                        code="CATEGORY_CIRCULAR_REFERENCE",
                    )
                if curr.parent_id:
                    curr = await CategoryRepository.get_by_id(db, curr.parent_id)
                else:
                    break

        if parent.parent_id is not None:
            raise CartifyException(
                status_code=400,
                message="Multi-level nesting beyond 2 levels (Category -> Subcategory) is not allowed.",
                code="INVALID_PARENT_CATEGORY",
            )

        return parent

    @classmethod
    async def create_category(
        cls,
        db: AsyncSession,
        data: CategoryCreateRequest,
    ) -> CategoryResponse:
        """Creates a new category (Admin only)."""
        # Validate parent hierarchy if subcategory
        if data.parent_id:
            await cls._validate_parent_hierarchy(db, data.parent_id)

        # Resolve unique slug
        if data.slug:
            if await CategoryRepository.slug_exists(db, data.slug):
                raise CartifyException(
                    status_code=409,
                    message=f"Category slug '{data.slug}' is already in use.",
                    code="CATEGORY_SLUG_ALREADY_EXISTS",
                )
            slug = data.slug
        else:
            slug = await cls._generate_unique_slug(db, data.name)

        create_dict = {
            "name": data.name,
            "slug": slug,
            "description": data.description,
            "icon": data.icon or "Compass",
            "image_url": data.image_url,
            "parent_id": data.parent_id,
            "sort_order": data.sort_order,
            "is_active": data.is_active,
        }

        category = await CategoryRepository.create(db, create_dict)
        await cls._invalidate_cache()
        return CategoryResponse.model_validate(category)

    @classmethod
    async def update_category(
        cls,
        db: AsyncSession,
        category_id: str,
        data: CategoryUpdateRequest,
    ) -> CategoryResponse:
        """Updates category fields (Admin only)."""
        category = await CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category", category_id)

        update_dict = {}

        if data.parent_id is not None:
            if data.parent_id == "":
                update_dict["parent_id"] = None
            else:
                await cls._validate_parent_hierarchy(db, data.parent_id, category_id=category_id)
                update_dict["parent_id"] = data.parent_id

        if data.slug is not None:
            if await CategoryRepository.slug_exists(db, data.slug, exclude_id=category_id):
                raise CartifyException(
                    status_code=409,
                    message=f"Category slug '{data.slug}' is already in use.",
                    code="CATEGORY_SLUG_ALREADY_EXISTS",
                )
            update_dict["slug"] = data.slug

        if data.name is not None:
            update_dict["name"] = data.name

        if data.description is not None:
            update_dict["description"] = data.description

        if data.icon is not None:
            update_dict["icon"] = data.icon

        if data.image_url is not None:
            update_dict["image_url"] = data.image_url

        if data.sort_order is not None:
            update_dict["sort_order"] = data.sort_order

        if data.is_active is not None:
            update_dict["is_active"] = data.is_active

        updated = await CategoryRepository.update(db, category, update_dict)
        await cls._invalidate_cache()
        return CategoryResponse.model_validate(updated)

    @classmethod
    async def delete_category(
        cls,
        db: AsyncSession,
        category_id: str,
        hard_delete: bool = False,
    ) -> dict:
        """
        Deactivates or hard-deletes a category (Admin only).
        Defaults to safe deactivation (is_active=False).
        Hard delete enforces zero subcategory dependencies.
        """
        category = await CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError("Category", category_id)

        if hard_delete:
            child_count = await CategoryRepository.count_children(db, category_id)
            if child_count > 0:
                raise CartifyException(
                    status_code=400,
                    message=f"Cannot delete category with {child_count} active subcategories. Deactivate them first or delete them individually.",
                    code="CATEGORY_HAS_DEPENDENCIES",
                )
            await CategoryRepository.delete(db, category)
            await cls._invalidate_cache()
            return {"message": "Category permanently deleted successfully."}
        else:
            # Safe soft deactivation
            await CategoryRepository.update(db, category, {"is_active": False})
            # Also deactivate direct children
            subcategories = await CategoryRepository.list_subcategories(
                db, category_id, active_only=True
            )
            for sub in subcategories:
                await CategoryRepository.update(db, sub, {"is_active": False})

            await cls._invalidate_cache()
            return {"message": "Category and its subcategories deactivated successfully."}
