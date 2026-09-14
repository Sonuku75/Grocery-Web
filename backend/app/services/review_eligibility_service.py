"""
Cartify Review Eligibility Service (Module 14)

Centralized purchase and review eligibility engine:
- Server-authoritative purchase verification
- Strict user order ownership checks (preventing horizontal privilege escalation / IDOR)
- Enforces order fulfillment state (must be DELIVERED / fulfilled)
- Prevents reviewing cancelled, failed, or unowned orders
- Enforces one review per eligible purchased item policy
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import CartifyException
from app.models.order import FulfillmentStatus, Order, OrderItem, OrderStatus
from app.models.product import Product
from app.repositories.review import ReviewRepository

logger = logging.getLogger("cartify.reviews.eligibility")


class ReviewEligibilityService:
    @classmethod
    async def get_reviewable_items(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: Optional[str] = None,
    ) -> List[OrderItem]:
        """
        Retrieves all order items for the user that belong to DELIVERED orders
        and have not yet been reviewed.
        """
        stmt = (
            select(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .options(
                selectinload(OrderItem.order),
                selectinload(OrderItem.product),
                selectinload(OrderItem.review),
            )
            .where(
                Order.user_id == user_id,
                (Order.status == OrderStatus.DELIVERED.value)
                | (Order.fulfillment_status == FulfillmentStatus.DELIVERED.value),
                Order.status != OrderStatus.CANCELLED.value,
                Order.status != OrderStatus.FAILED.value,
            )
        )
        if product_id is not None:
            stmt = stmt.where(OrderItem.product_id == product_id)

        res = await db.execute(stmt)
        items = list(res.scalars().all())

        # Filter out items that already have a non-deleted review
        eligible_items = []
        for item in items:
            existing = await ReviewRepository.get_by_order_item(db, item.id)
            if not existing:
                eligible_items.append(item)

        return eligible_items

    @classmethod
    async def can_review_product(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
    ) -> Tuple[bool, Optional[str], List[OrderItem]]:
        """
        Evaluates whether an authenticated user is currently permitted to review a product.
        Returns:
            (can_review: bool, reason: Optional[str], eligible_items: List[OrderItem])
        """
        # Verify product exists and is active
        prod_stmt = select(Product).where(Product.id == product_id)
        prod_res = await db.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        if not product:
            return False, "PRODUCT_NOT_FOUND", []

        eligible_items = await cls.get_reviewable_items(db, user_id=user_id, product_id=product_id)
        if not eligible_items:
            # Check if they previously purchased and reviewed it
            reviewed_stmt = (
                select(OrderItem)
                .join(Order, OrderItem.order_id == Order.id)
                .where(
                    Order.user_id == user_id,
                    OrderItem.product_id == product_id,
                )
            )
            reviewed_res = await db.execute(reviewed_stmt)
            has_purchase = reviewed_res.first() is not None
            if has_purchase:
                return False, "REVIEW_ALREADY_EXISTS", []
            return False, "REVIEW_NOT_ELIGIBLE", []

        return True, None, eligible_items

    @classmethod
    async def verify_order_item_for_review(
        cls,
        db: AsyncSession,
        user_id: str,
        product_id: str,
        order_item_id: str,
    ) -> OrderItem:
        """
        Performs multi-point server-authoritative validation for review creation:
        1. Order item must exist.
        2. Order item must belong to requested product.
        3. Order must belong to authenticated user (IDOR prevention).
        4. Order must be DELIVERED / fulfilled.
        5. Order must NOT be CANCELLED or FAILED.
        6. Item must not have been reviewed yet (Duplicate prevention).
        """
        stmt = (
            select(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .options(
                selectinload(OrderItem.order),
                selectinload(OrderItem.product),
            )
            .where(OrderItem.id == order_item_id)
        )
        res = await db.execute(stmt)
        order_item = res.scalar_one_or_none()

        if not order_item:
            raise CartifyException(
                status_code=404,
                message=f"Order item with identifier '{order_item_id}' was not found.",
                code="ORDER_ITEM_NOT_FOUND",
            )

        # Verify product matching
        if order_item.product_id != product_id:
            raise CartifyException(
                status_code=400,
                message="The specified order item does not correspond to the requested product.",
                code="REVIEW_NOT_ELIGIBLE",
            )

        # Verify order ownership (Critical IDOR protection)
        order = order_item.order
        if not order or order.user_id != user_id:
            raise CartifyException(
                status_code=403,
                message="You are not authorized to review items from an order you do not own.",
                code="REVIEW_ACCESS_DENIED",
            )

        # Verify order state (must be DELIVERED)
        is_delivered = (
            order.status == OrderStatus.DELIVERED.value
            or order.fulfillment_status == FulfillmentStatus.DELIVERED.value
        )
        if not is_delivered:
            raise CartifyException(
                status_code=400,
                message="Reviews can only be submitted for successfully delivered orders.",
                code="REVIEW_NOT_ELIGIBLE",
            )

        # Disallow cancelled or failed orders
        if order.status in {OrderStatus.CANCELLED.value, OrderStatus.FAILED.value}:
            raise CartifyException(
                status_code=400,
                message="Reviews cannot be submitted for cancelled or failed orders.",
                code="REVIEW_NOT_ELIGIBLE",
            )

        # Check existing non-deleted review
        existing = await ReviewRepository.get_by_order_item(db, order_item_id)
        if existing:
            raise CartifyException(
                status_code=409,
                message="A review has already been submitted for this purchased item.",
                code="REVIEW_ALREADY_EXISTS",
            )

        return order_item
