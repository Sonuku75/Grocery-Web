"""
Cartify Review Repository (Module 14)

Data access and query management for reviews:
- Filtered public product reviews (only PUBLISHED and non-deleted)
- Sorting: MOST_RECENT, MOST_HELPFUL, HIGHEST_RATING, LOWEST_RATING
- Keyset / cursor pagination with safe bounding (max 50, default 20)
- Scoped user reviews query (IDOR protection)
- Concurrency-safe atomic helpful count increment / decrement
- Transactional creation, update, and soft-delete
"""

import base64
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review, ReviewStatus


class ReviewRepository:
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        review_id: str,
        include_deleted: bool = False,
    ) -> Optional[Review]:
        """
        Retrieves review by primary key ID with loaded relationships.
        """
        stmt = (
            select(Review)
            .options(
                selectinload(Review.user),
                selectinload(Review.product),
                selectinload(Review.order),
                selectinload(Review.order_item),
            )
            .where(Review.id == review_id)
        )
        if not include_deleted:
            stmt = stmt.where(Review.deleted_at.is_(None))

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_order_item(
        cls,
        db: AsyncSession,
        order_item_id: str,
        include_deleted: bool = False,
    ) -> Optional[Review]:
        """
        Finds review linked to a specific order line item.
        """
        stmt = select(Review).where(Review.order_item_id == order_item_id)
        if not include_deleted:
            stmt = stmt.where(Review.deleted_at.is_(None))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_user_product_order(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
        order_id: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Optional[Review]:
        """
        Checks if customer has reviewed this product within a specific order.
        """
        stmt = select(Review).where(
            Review.user_id == user_id,
            Review.product_id == product_id,
        )
        if order_id is not None:
            stmt = stmt.where(Review.order_id == order_id)
        if not include_deleted:
            stmt = stmt.where(Review.deleted_at.is_(None))

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_for_product(
        cls,
        db: AsyncSession,
        product_id: str,
        rating: Optional[int] = None,
        verified_only: bool = False,
        sort: str = "MOST_RECENT",
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Review], Optional[str], int]:
        """
        Retrieves published, non-deleted reviews for a product with cursor pagination.
        Only PUBLISHED reviews are exposed to public callers.
        """
        limit = min(max(1, limit), 50)
        base_where = [
            Review.product_id == product_id,
            Review.status == ReviewStatus.PUBLISHED.value,
            Review.deleted_at.is_(None),
        ]
        if rating is not None and 1 <= rating <= 5:
            base_where.append(Review.rating == rating)
        if verified_only:
            base_where.append(Review.is_verified_purchase.is_(True))

        # Total count matching criteria
        count_stmt = select(func.count(Review.id)).where(*base_where)
        count_res = await db.execute(count_stmt)
        total_count = int(count_res.scalar_one() or 0)

        # Build order by clause
        if sort == "MOST_HELPFUL":
            order_criteria = [Review.helpful_count.desc(), Review.created_at.desc(), Review.id.desc()]
        elif sort == "HIGHEST_RATING":
            order_criteria = [Review.rating.desc(), Review.created_at.desc(), Review.id.desc()]
        elif sort == "LOWEST_RATING":
            order_criteria = [Review.rating.asc(), Review.created_at.desc(), Review.id.desc()]
        else:  # Default: MOST_RECENT
            order_criteria = [Review.created_at.desc(), Review.id.desc()]

        stmt = (
            select(Review)
            .options(
                selectinload(Review.user),
            )
            .where(*base_where)
            .order_by(*order_criteria)
        )

        # Handle cursor if provided
        offset = 0
        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode("utf-8")).decode("utf-8")
                if decoded.startswith("offset:"):
                    offset = int(decoded.split("offset:")[1])
            except Exception:
                offset = 0

        stmt = stmt.offset(offset).limit(limit + 1)
        res = await db.execute(stmt)
        items = list(res.scalars().all())

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            next_cursor = base64.b64encode(f"offset:{offset + limit}".encode("utf-8")).decode("utf-8")

        return items, next_cursor, total_count

    @classmethod
    async def list_for_user(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Review], int]:
        """
        Retrieves all reviews submitted by the authenticated user (including pending),
        excluding soft-deleted reviews.
        """
        limit = min(max(1, limit), 50)
        base_where = [
            Review.user_id == user_id,
            Review.deleted_at.is_(None),
        ]
        count_stmt = select(func.count(Review.id)).where(*base_where)
        count_res = await db.execute(count_stmt)
        total_count = int(count_res.scalar_one() or 0)

        stmt = (
            select(Review)
            .options(
                selectinload(Review.product),
                selectinload(Review.order),
            )
            .where(*base_where)
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total_count

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        review_data: dict,
    ) -> Review:
        """
        Creates a new review within the active database transaction.
        """
        review = Review(**review_data)
        db.add(review)
        await db.flush()
        return review

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        review: Review,
        update_data: dict,
    ) -> Review:
        """
        Updates review fields and refreshes updated_at timestamp.
        """
        for key, value in update_data.items():
            setattr(review, key, value)
        review.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return review

    @classmethod
    async def soft_delete(
        cls,
        db: AsyncSession,
        review: Review,
    ) -> Review:
        """
        Soft-deletes review by recording deleted_at and marking status DELETED.
        """
        now = datetime.now(timezone.utc)
        review.deleted_at = now
        review.status = ReviewStatus.DELETED.value
        review.updated_at = now
        await db.flush()
        return review

    @classmethod
    async def atomic_increment_helpful(cls, db: AsyncSession, review_id: str) -> None:
        """
        Atomically increments review.helpful_count in database.
        """
        stmt = (
            update(Review)
            .where(Review.id == review_id)
            .values(helpful_count=Review.helpful_count + 1)
        )
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def atomic_decrement_helpful(cls, db: AsyncSession, review_id: str) -> None:
        """
        Atomically decrements review.helpful_count in database, bounded at zero.
        """
        stmt = (
            update(Review)
            .where(Review.id == review_id)
            .values(
                helpful_count=case(
                    (Review.helpful_count > 0, Review.helpful_count - 1),
                    else_=0,
                )
            )
        )
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def list_admin_reviews(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        product_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Review], int]:
        """
        Admin query with optional status filtering and product scoping.
        """
        limit = min(max(1, limit), 100)
        base_where = []
        if status and status.strip():
            base_where.append(Review.status == status.strip().upper())
        if product_id and product_id.strip():
            base_where.append(Review.product_id == product_id.strip())

        count_stmt = select(func.count(Review.id))
        if base_where:
            count_stmt = count_stmt.where(*base_where)
        count_res = await db.execute(count_stmt)
        total_count = int(count_res.scalar_one() or 0)

        stmt = (
            select(Review)
            .options(
                selectinload(Review.user),
                selectinload(Review.product),
                selectinload(Review.order),
            )
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if base_where:
            stmt = stmt.where(*base_where)

        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total_count
