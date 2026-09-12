"""
Cartify Category Repository (Module 3)

Encapsulates database operations for hierarchical categories:
- Top-level and subcategory querying
- Slug uniqueness checks
- Dependent children counts
- Active/inactive filtering
"""

from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category


class CategoryRepository:
    @classmethod
    async def list_top_level(
        cls,
        db: AsyncSession,
        active_only: bool = True,
        limit: int = 100,
        skip: int = 0,
    ) -> Sequence[Category]:
        """Retrieves top-level categories (parent_id IS NULL) ordered by sort_order."""
        query = (
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.parent_id.is_(None))
        )
        if active_only:
            query = query.where(Category.is_active.is_(True))

        query = query.order_by(Category.sort_order.asc(), Category.name.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def count_top_level(
        cls,
        db: AsyncSession,
        active_only: bool = True,
    ) -> int:
        """Counts top-level categories matching active filter."""
        query = select(func.count(Category.id)).where(Category.parent_id.is_(None))
        if active_only:
            query = query.where(Category.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one() or 0

    @classmethod
    async def list_subcategories(
        cls,
        db: AsyncSession,
        parent_id: str,
        active_only: bool = True,
    ) -> Sequence[Category]:
        """Retrieves direct subcategories for a given parent_id."""
        query = select(Category).where(Category.parent_id == parent_id)
        if active_only:
            query = query.where(Category.is_active.is_(True))
        query = query.order_by(Category.sort_order.asc(), Category.name.asc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        category_id: str,
        active_only: bool = False,
    ) -> Optional[Category]:
        """Retrieves a single category by primary key UUID."""
        query = (
            select(Category)
            .options(selectinload(Category.children), selectinload(Category.parent))
            .where(Category.id == category_id)
        )
        if active_only:
            query = query.where(Category.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_slug(
        cls,
        db: AsyncSession,
        slug: str,
        active_only: bool = False,
    ) -> Optional[Category]:
        """Retrieves a category by unique URL slug."""
        query = (
            select(Category)
            .options(selectinload(Category.children), selectinload(Category.parent))
            .where(Category.slug == slug)
        )
        if active_only:
            query = query.where(Category.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def count_children(
        cls,
        db: AsyncSession,
        category_id: str,
        active_only: bool = False,
    ) -> int:
        """Counts direct subcategories under a given category."""
        query = select(func.count(Category.id)).where(Category.parent_id == category_id)
        if active_only:
            query = query.where(Category.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one() or 0

    @classmethod
    async def slug_exists(
        cls,
        db: AsyncSession,
        slug: str,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """Checks if a slug is already taken by another category."""
        query = select(Category.id).where(Category.slug == slug)
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create(cls, db: AsyncSession, data: dict) -> Category:
        """Persists a new category record."""
        category = Category(**data)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @classmethod
    async def update(
        cls, db: AsyncSession, category: Category, update_data: dict
    ) -> Category:
        """Updates attributes on an existing category."""
        for key, value in update_data.items():
            setattr(category, key, value)
        await db.commit()
        await db.refresh(category)
        return category

    @classmethod
    async def delete(cls, db: AsyncSession, category: Category) -> None:
        """Hard-deletes a category record."""
        await db.delete(category)
        await db.commit()
