"""
Cartify Wishlist Repository (Module 6)

Encapsulates all database operations for customer wishlist items:
- Scoped to authenticated user_id to prevent IDOR / horizontal privilege escalation
- Uses keyset cursor pagination on (created_at DESC, id DESC)
- Eagerly loads product, variants, images, and categories via selectinload to eliminate N+1 queries
- Fast existence and count queries for badges and state indicators
"""

import base64
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.wishlist import WishlistItem


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


class WishlistRepository:
    @classmethod
    async def get_by_user_and_product(
        cls, db: AsyncSession, user_id: str, product_id: str
    ) -> Optional[WishlistItem]:
        """Retrieves a specific wishlist entry for a user and product."""
        stmt = (
            select(WishlistItem)
            .options(
                selectinload(WishlistItem.product).selectinload(Product.variants),
                selectinload(WishlistItem.product).selectinload(Product.images),
                selectinload(WishlistItem.product).selectinload(Product.category),
            )
            .where(
                WishlistItem.user_id == user_id,
                WishlistItem.product_id == product_id,
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_user_wishlist(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[WishlistItem], Optional[str], bool, int]:
        """
        Returns keyset-paginated wishlist items for the authenticated user
        along with next_cursor, has_more flag, and total user wishlist count.
        """
        # 1. Total count query
        count_stmt = select(func.count(WishlistItem.id)).where(WishlistItem.user_id == user_id)
        count_res = await db.execute(count_stmt)
        total_count = count_res.scalar_one() or 0

        # 2. Main query with eager joins
        query = (
            select(WishlistItem)
            .options(
                selectinload(WishlistItem.product).selectinload(Product.variants),
                selectinload(WishlistItem.product).selectinload(Product.images),
                selectinload(WishlistItem.product).selectinload(Product.category),
            )
            .where(WishlistItem.user_id == user_id)
        )

        # Keyset cursor filtering
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                c_time, c_id = decoded
                query = query.where(
                    or_(
                        WishlistItem.created_at < c_time,
                        and_(WishlistItem.created_at == c_time, WishlistItem.id < c_id),
                    )
                )

        # Stable descending order matching composite index idx_wishlist_keyset
        query = query.order_by(WishlistItem.created_at.desc(), WishlistItem.id.desc())

        # Fetch limit + 1 to detect next page without separate count
        query = query.limit(limit + 1)
        res = await db.execute(query)
        items = list(res.scalars().all())

        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
            next_cursor = encode_cursor(items[-1].created_at, items[-1].id)
        else:
            next_cursor = None

        return items, next_cursor, has_more, total_count

    @classmethod
    async def count_user_wishlist(cls, db: AsyncSession, user_id: str) -> int:
        """Returns total active count of items in user's wishlist."""
        stmt = select(func.count(WishlistItem.id)).where(WishlistItem.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one() or 0

    @classmethod
    async def is_wishlisted(cls, db: AsyncSession, user_id: str, product_id: str) -> bool:
        """Returns True if the product is in the user's wishlist, else False."""
        stmt = select(func.count(WishlistItem.id)).where(
            WishlistItem.user_id == user_id,
            WishlistItem.product_id == product_id,
        )
        res = await db.execute(stmt)
        count = res.scalar_one() or 0
        return count > 0

    @classmethod
    async def create(
        cls, db: AsyncSession, user_id: str, product_id: str
    ) -> WishlistItem:
        """Creates a new wishlist item."""
        item = WishlistItem(user_id=user_id, product_id=product_id)
        db.add(item)
        await db.flush()
        return item

    @classmethod
    async def delete(
        cls, db: AsyncSession, user_id: str, product_id: str
    ) -> bool:
        """
        Removes a product from the user's wishlist.
        Guarantees user scoping (WHERE user_id = :user_id AND product_id = :product_id).
        Returns True if a record was deleted, False if it was not found.
        """
        stmt = (
            delete(WishlistItem)
            .where(
                WishlistItem.user_id == user_id,
                WishlistItem.product_id == product_id,
            )
            .execution_options(synchronize_session=False)
        )
        res = await db.execute(stmt)
        return res.rowcount > 0
