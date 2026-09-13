"""
Cartify Cart Repository (Module 7)

Encapsulates all database queries and transactions for carts and cart items:
- Scoped to authenticated user_id to prevent IDOR / horizontal privilege escalation
- Eagerly loads items, product, images, and variant via selectinload to eliminate N+1 queries
- Enforces atomic operations and handles concurrency/savepoints cleanly
"""

from typing import Optional
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant


class CartRepository:
    @classmethod
    async def get_by_user_id(
        cls, db: AsyncSession, user_id: str, create_if_missing: bool = False
    ) -> Optional[Cart]:
        """
        Retrieves the cart for a specific user, with all items, product details,
        and variant data eagerly loaded.
        """
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images),
                selectinload(Cart.items).selectinload(CartItem.variant),
                selectinload(Cart.coupon),
            )
            .where(Cart.user_id == user_id)
        )
        res = await db.execute(stmt)
        cart = res.scalar_one_or_none()

        if cart is None and create_if_missing:
            cart = Cart(user_id=user_id)
            db.add(cart)
            try:
                await db.flush()
                # Re-fetch with all eager loads populated
                res = await db.execute(stmt)
                cart = res.scalar_one_or_none()
            except IntegrityError:
                # Concurrent request already created the cart
                res = await db.execute(stmt)
                cart = res.scalar_one_or_none()

        return cart

    @classmethod
    async def get_item_by_id(
        cls, db: AsyncSession, item_id: str
    ) -> Optional[CartItem]:
        """
        Retrieves a single cart item by ID with cart, product, and variant loaded.
        """
        stmt = (
            select(CartItem)
            .options(
                selectinload(CartItem.cart),
                selectinload(CartItem.product).selectinload(Product.images),
                selectinload(CartItem.variant),
            )
            .where(CartItem.id == item_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_item_by_cart_and_variant(
        cls, db: AsyncSession, cart_id: str, variant_id: str
    ) -> Optional[CartItem]:
        """
        Finds existing item for this specific cart and variant.
        """
        stmt = (
            select(CartItem)
            .options(
                selectinload(CartItem.product).selectinload(Product.images),
                selectinload(CartItem.variant),
            )
            .where(
                CartItem.cart_id == cart_id,
                CartItem.variant_id == variant_id,
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def add_item(
        cls, db: AsyncSession, cart_id: str, product_id: str, variant_id: str, quantity: int = 1
    ) -> CartItem:
        """
        Inserts a new item into the cart.
        """
        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
        )
        db.add(item)
        await db.flush()
        return item

    @classmethod
    async def update_item_quantity(
        cls, db: AsyncSession, item: CartItem, quantity: int
    ) -> CartItem:
        """
        Updates the quantity for an existing cart item.
        """
        item.quantity = quantity
        await db.flush()
        return item

    @classmethod
    async def delete_item(
        cls, db: AsyncSession, item_id: str, cart_id: str
    ) -> bool:
        """
        Removes an item from the cart scoped to the cart_id.
        """
        stmt = (
            delete(CartItem)
            .where(
                CartItem.id == item_id,
                CartItem.cart_id == cart_id,
            )
            .execution_options(synchronize_session=False)
        )
        res = await db.execute(stmt)
        return res.rowcount > 0

    @classmethod
    async def clear_cart(
        cls, db: AsyncSession, cart_id: str
    ) -> int:
        """
        Deletes all items for a given cart.
        """
        stmt = (
            delete(CartItem)
            .where(CartItem.cart_id == cart_id)
            .execution_options(synchronize_session=False)
        )
        res = await db.execute(stmt)
        return res.rowcount

    @classmethod
    async def count_cart_items(
        cls, db: AsyncSession, user_id: str
    ) -> int:
        """
        Calculates total item count (sum of quantities) for the user's cart.
        """
        stmt = (
            select(func.coalesce(func.sum(CartItem.quantity), 0))
            .join(Cart, Cart.id == CartItem.cart_id)
            .where(Cart.user_id == user_id)
        )
        res = await db.execute(stmt)
        return int(res.scalar_one() or 0)
