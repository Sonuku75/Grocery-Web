"""
Cartify Cart Service (Module 7)

Domain business logic for shopping cart operations:
- Scoped strictly to authenticated user_id (prevents IDOR and horizontal escalation)
- Authoritative server-side price calculation based on ProductVariant.price
- Bounded quantity constraints (1 <= quantity <= 99)
- Handles concurrent additions safely (unique constraint recovery)
- Calculates subtotal and line total with high-precision Decimal arithmetic
- Eager relationships loaded via CartRepository to eliminate N+1 queries
"""

import logging
from decimal import Decimal
from typing import Optional
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, ForbiddenError, NotFoundError
from app.models.cart import Cart, CartItem
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.repositories.product_variant import ProductVariantRepository
from app.schemas.cart import (
    CartClearResponse,
    CartItemResponse,
    CartProductSummary,
    CartResponse,
    CartVariantSummary,
)

logger = logging.getLogger("cartify.cart")


from app.models.coupon import Coupon
from app.repositories.coupon import CouponRepository
from app.schemas.coupon import CouponSummary
from app.services.coupon_service import CouponService


class CartService:
    @classmethod
    def _format_cart_item(cls, item: CartItem) -> Optional[CartItemResponse]:
        """Transforms a CartItem ORM instance into CartItemResponse with authoritative price calculations."""
        if not item.product or not item.variant:
            return None

        unit_price = Decimal(str(item.variant.price)).quantize(Decimal("0.01"))
        line_total = (unit_price * item.quantity).quantize(Decimal("0.01"))

        variant_summary = CartVariantSummary(
            id=item.variant.id,
            product_id=item.variant.product_id,
            sku=item.variant.sku,
            name=item.variant.name,
            unit=f"{item.variant.unit_value} {item.variant.unit_type}".strip(),
            price=unit_price,
            mrp=Decimal(str(item.variant.mrp)).quantize(Decimal("0.01")) if item.variant.mrp is not None else None,
            stock_quantity=99 if item.variant.is_active else 0,
            is_active=item.variant.is_active,
        )

        prod_title = getattr(item.product, "name", None) or getattr(item.product, "title", "")
        product_summary = CartProductSummary(
            id=item.product.id,
            title=prod_title,
            name=prod_title,
            slug=item.product.slug,
            thumbnail_url=item.product.image_url,
            is_active=item.product.is_active,
        )

        return CartItemResponse(
            id=item.id,
            cart_id=item.cart_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            unit_price=unit_price,
            line_total=line_total,
            product=product_summary,
            variant=variant_summary,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @classmethod
    def _format_cart(
        cls,
        cart: Cart,
        applied_coupon: Optional[CouponSummary] = None,
        discount: Decimal = Decimal("0.00"),
    ) -> CartResponse:
        """Transforms a Cart ORM model into CartResponse with authoritative totals."""
        formatted_items = []
        subtotal = Decimal("0.00")
        item_count = 0

        for item in cart.items:
            formatted_item = cls._format_cart_item(item)
            if formatted_item:
                formatted_items.append(formatted_item)
                subtotal += formatted_item.line_total
                item_count += formatted_item.quantity

        subtotal = subtotal.quantize(Decimal("0.01"))

        # If applied_coupon was not explicitly passed, inspect cart.coupon if present
        if applied_coupon is None and getattr(cart, "coupon", None):
            coupon = cart.coupon
            if coupon.is_active and not coupon.is_expired:
                discount = CouponService.calculate_discount(coupon, subtotal)
                applied_coupon = CouponSummary.model_validate(coupon)
            else:
                discount = Decimal("0.00")

        delivery_fee = Decimal("0.00")
        tax = Decimal("0.00")
        total = max(Decimal("0.00"), (subtotal - discount + delivery_fee + tax).quantize(Decimal("0.01")))

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=formatted_items,
            item_count=item_count,
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
            tax=tax,
            total=total,
            applied_coupon=applied_coupon,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    @classmethod
    async def _revalidate_and_format_cart(cls, db: AsyncSession, cart: Cart) -> CartResponse:
        """
        Revalidates any attached coupon against current subtotal and database state.
        If the coupon has expired or subtotal dropped below minimum_order_value,
        gracefully detaches coupon and resets discount to 0.00 without error.
        """
        formatted_items = []
        subtotal = Decimal("0.00")
        item_count = 0

        for item in cart.items:
            formatted_item = cls._format_cart_item(item)
            if formatted_item:
                formatted_items.append(formatted_item)
                subtotal += formatted_item.line_total
                item_count += formatted_item.quantity

        subtotal = subtotal.quantize(Decimal("0.01"))
        discount = Decimal("0.00")
        applied_coupon: Optional[CouponSummary] = None

        if cart.coupon_id:
            coupon = cart.coupon
            if not coupon:
                coupon = await CouponRepository.get_by_id(db, cart.coupon_id)

            if coupon and subtotal > Decimal("0.00"):
                is_valid, msg, _, calc_discount = await CouponService.validate_coupon(
                    db=db,
                    code_or_coupon=coupon,
                    subtotal=subtotal,
                    user_id=cart.user_id,
                )
                if is_valid:
                    discount = calc_discount
                    applied_coupon = CouponSummary.model_validate(coupon)
                else:
                    logger.info(
                        "Coupon '%s' automatically detached from cart '%s' because: %s",
                        coupon.code,
                        cart.id,
                        msg,
                    )
                    cart.coupon_id = None
                    cart.coupon = None
                    await db.flush()
                    await db.commit()
            else:
                cart.coupon_id = None
                cart.coupon = None
                await db.flush()
                await db.commit()

        delivery_fee = Decimal("0.00")
        tax = Decimal("0.00")
        total = max(Decimal("0.00"), (subtotal - discount + delivery_fee + tax).quantize(Decimal("0.01")))

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=formatted_items,
            item_count=item_count,
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
            tax=tax,
            total=total,
            applied_coupon=applied_coupon,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    @classmethod
    async def get_cart(cls, db: AsyncSession, user_id: str) -> CartResponse:
        """
        Retrieves the authenticated user's cart, creating an empty one if not yet initialized.
        Automatically revalidates any applied coupon against current cart subtotal.
        """
        cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=True)
        return await cls._revalidate_and_format_cart(db, cart)

    @classmethod
    async def add_item(
        cls,
        db: AsyncSession,
        user_id: str,
        variant_id: str,
        quantity: int = 1,
        product_id: Optional[str] = None,
    ) -> CartResponse:
        """
        Adds a product variant to the user's cart.
        - Validates bounded quantity (1 <= quantity <= 99)
        - Validates variant exists and is active
        - Validates parent product exists and is active
        - Increments existing variant quantity if already present (capped at 99)
        - Concurrency-safe against race conditions
        """
        if quantity < 1 or quantity > 99:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Quantity must be between 1 and 99.",
                code="INVALID_QUANTITY",
            )

        variant = await ProductVariantRepository.get_by_id(db, variant_id)
        if not variant:
            raise NotFoundError("ProductVariant", variant_id)
        if not variant.is_active:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Cannot add inactive variant '{variant.name}' to cart.",
                code="VARIANT_INACTIVE",
            )

        product = await ProductRepository.get_by_id(db, variant.product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", variant.product_id)
        if not product.is_active:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Cannot add inactive product '{product.name}' to cart.",
                code="PRODUCT_INACTIVE",
            )

        cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=True)

        existing_item = await CartRepository.get_item_by_cart_and_variant(db, cart.id, variant.id)
        if existing_item:
            new_qty = min(existing_item.quantity + quantity, 99)
            await CartRepository.update_item_quantity(db, existing_item, new_qty)
            await db.commit()
        else:
            try:
                async with db.begin_nested():
                    await CartRepository.add_item(
                        db=db,
                        cart_id=cart.id,
                        product_id=product.id,
                        variant_id=variant.id,
                        quantity=min(quantity, 99),
                    )
                await db.commit()
            except IntegrityError:
                await db.rollback()
                existing_item = await CartRepository.get_item_by_cart_and_variant(db, cart.id, variant.id)
                if existing_item:
                    new_qty = min(existing_item.quantity + quantity, 99)
                    await CartRepository.update_item_quantity(db, existing_item, new_qty)
                    await db.commit()
                else:
                    raise

        fresh_cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=False)
        logger.info(
            "User '%s' added %d of variant '%s' to cart",
            user_id,
            quantity,
            variant_id,
        )
        return await cls._revalidate_and_format_cart(db, fresh_cart)

    @classmethod
    async def update_item_quantity(
        cls,
        db: AsyncSession,
        user_id: str,
        cart_item_id: str,
        quantity: int,
    ) -> CartResponse:
        """
        Updates quantity for a cart item.
        - Validates bounded quantity (1 <= quantity <= 99)
        - IDOR check: verifies cart belongs to authenticated user
        - Auto-revalidates applied coupon against new subtotal
        """
        if quantity < 1 or quantity > 99:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Quantity must be between 1 and 99.",
                code="INVALID_QUANTITY",
            )

        item = await CartRepository.get_item_by_id(db, cart_item_id)
        if not item:
            raise NotFoundError("CartItem", cart_item_id)

        if not item.cart or item.cart.user_id != user_id:
            raise ForbiddenError("You do not have permission to modify this cart item.")

        await CartRepository.update_item_quantity(db, item, quantity)
        await db.commit()

        fresh_cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=False)
        logger.info(
            "User '%s' updated cart item '%s' quantity to %d",
            user_id,
            cart_item_id,
            quantity,
        )
        return await cls._revalidate_and_format_cart(db, fresh_cart)

    @classmethod
    async def remove_item(
        cls,
        db: AsyncSession,
        user_id: str,
        cart_item_id: str,
    ) -> CartResponse:
        """
        Removes an item from user's cart.
        - IDOR check: verifies cart belongs to authenticated user
        - Auto-revalidates applied coupon against new subtotal
        """
        item = await CartRepository.get_item_by_id(db, cart_item_id)
        if not item:
            raise NotFoundError("CartItem", cart_item_id)

        if not item.cart or item.cart.user_id != user_id:
            raise ForbiddenError("You do not have permission to remove this cart item.")

        await CartRepository.delete_item(db, cart_item_id, item.cart_id)
        await db.commit()

        fresh_cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=True)
        logger.info("User '%s' removed cart item '%s'", user_id, cart_item_id)
        return await cls._revalidate_and_format_cart(db, fresh_cart)

    @classmethod
    async def clear_cart(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> CartClearResponse:
        """
        Removes all items and any applied coupon from authenticated user's cart.
        """
        cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=False)
        if cart:
            cart.coupon_id = None
            cart.coupon = None
            await CartRepository.clear_cart(db, cart.id)
            await db.commit()
            logger.info("User '%s' cleared cart '%s'", user_id, cart.id)
            return CartClearResponse(message="Cart cleared successfully", cart_id=cart.id)
        return CartClearResponse(message="Cart cleared successfully", cart_id=None)

    @classmethod
    async def count_cart_items(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> int:
        """
        Returns total count of items (sum of quantities) in user's cart.
        """
        return await CartRepository.count_cart_items(db, user_id)

    @classmethod
    async def apply_coupon(
        cls,
        db: AsyncSession,
        user_id: str,
        code: str,
    ) -> CartResponse:
        """
        Applies a promotional coupon code to the user's active cart.
        - Validates cart is not empty
        - Strictly validates coupon rules, limits, and order threshold
        - Attaches coupon to cart
        """
        cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=True)
        if not cart.items:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Cannot apply coupon to an empty cart.",
                code="EMPTY_CART",
            )

        # Calculate current subtotal
        subtotal = Decimal("0.00")
        for item in cart.items:
            if item.variant:
                unit_price = Decimal(str(item.variant.price)).quantize(Decimal("0.01"))
                subtotal += unit_price * item.quantity

        is_valid, msg, coupon, discount = await CouponService.validate_coupon(
            db=db,
            code_or_coupon=code,
            subtotal=subtotal,
            user_id=user_id,
        )

        if not is_valid or not coupon:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
                code="INVALID_COUPON",
            )

        cart.coupon_id = coupon.id
        cart.coupon = coupon
        await db.commit()

        fresh_cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=False)
        logger.info(
            "User '%s' applied coupon '%s' (discount: ₹%s) to cart '%s'",
            user_id,
            coupon.code,
            discount,
            fresh_cart.id,
        )
        return await cls._revalidate_and_format_cart(db, fresh_cart)

    @classmethod
    async def remove_coupon(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> CartResponse:
        """
        Removes currently applied coupon from the user's cart.
        """
        cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=True)
        if cart.coupon_id is not None:
            cart.coupon_id = None
            cart.coupon = None
            await db.commit()
            logger.info("User '%s' removed coupon from cart '%s'", user_id, cart.id)

        fresh_cart = await CartRepository.get_by_user_id(db, user_id, create_if_missing=False)
        return await cls._revalidate_and_format_cart(db, fresh_cart)

