from decimal import Decimal
from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.product import Product
from app.schemas.cart import CartItemResponse, CartResponse
from app.schemas.product import ProductResponse

class CartService:
    @classmethod
    async def get_or_create_cart(cls, db: AsyncSession, user_id: str) -> Cart:
        stmt = select(Cart).where(Cart.user_id == user_id)
        result = await db.execute(stmt)
        cart = result.scalar_one_or_none()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        return cart

    @classmethod
    async def get_cart(cls, db: AsyncSession, user_id: str) -> CartResponse:
        cart = await cls.get_or_create_cart(db, user_id)
        
        # Load items with product and category info
        stmt = (
            select(CartItem, Product, Category.name.label("category_name"))
            .join(Product, CartItem.product_id == Product.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .where(CartItem.cart_id == cart.id)
        )
        result = await db.execute(stmt)
        rows = result.all()

        item_responses = []
        subtotal = Decimal("0.00")
        total_items = 0

        for item, product, cat_name in rows:
            prod_resp = ProductResponse(
                id=product.id,
                name=product.name,
                slug=product.slug,
                brand=product.brand,
                category_id=product.category_id,
                category_name=cat_name,
                description=product.description,
                specifications=product.specifications or {},
                price=Decimal(str(product.price)),
                original_price=Decimal(str(product.original_price)),
                discount_percent=product.discount_percent,
                unit=product.unit,
                stock=product.stock,
                rating=Decimal(str(product.rating)),
                rating_count=product.rating_count,
                images=product.images or [],
                tags=product.tags or [],
                is_popular=product.is_popular,
                is_featured=product.is_featured,
                is_deal=product.is_deal,
                in_stock=product.in_stock,
            )
            item_responses.append(
                CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product=prod_resp,
                )
            )
            subtotal += Decimal(str(product.price)) * item.quantity
            total_items += item.quantity

        delivery_fee = Decimal("0.00") if (subtotal >= Decimal("500.00") or total_items == 0) else Decimal("40.00")
        discount = Decimal("0.00")
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        total = (subtotal - discount + delivery_fee + tax).quantize(Decimal("0.01"))

        return CartResponse(
            id=cart.id,
            items=item_responses,
            item_count=total_items,
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
            tax=tax,
            total=total,
        )

    @classmethod
    async def add_item(cls, db: AsyncSession, user_id: str, product_id: str, quantity: int = 1) -> CartResponse:
        cart = await cls.get_or_create_cart(db, user_id)

        prod_stmt = select(Product).where(Product.id == product_id, Product.is_active == True)
        prod_res = await db.execute(prod_stmt)
        if not prod_res.scalar_one_or_none():
            raise NotFoundError("Product", product_id)

        item_stmt = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        item_res = await db.execute(item_stmt)
        cart_item = item_res.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.add(cart_item)

        await db.commit()
        return await cls.get_cart(db, user_id)

    @classmethod
    async def update_quantity(cls, db: AsyncSession, user_id: str, product_id: str, quantity: int) -> CartResponse:
        cart = await cls.get_or_create_cart(db, user_id)

        item_stmt = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        item_res = await db.execute(item_stmt)
        cart_item = item_res.scalar_one_or_none()

        if not cart_item:
            raise NotFoundError("CartItem", product_id)

        if quantity <= 0:
            await db.delete(cart_item)
        else:
            cart_item.quantity = quantity

        await db.commit()
        return await cls.get_cart(db, user_id)

    @classmethod
    async def remove_item(cls, db: AsyncSession, user_id: str, product_id: str) -> CartResponse:
        cart = await cls.get_or_create_cart(db, user_id)
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id))
        await db.commit()
        return await cls.get_cart(db, user_id)

    @classmethod
    async def clear_cart(cls, db: AsyncSession, user_id: str) -> None:
        cart = await cls.get_or_create_cart(db, user_id)
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await db.commit()
