from decimal import Decimal
import logging
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InsufficientStockError, NotFoundError
from app.core.redis import CacheManager
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderItemResponse, OrderResponse

logger = logging.getLogger("cartify.order_service")

class OrderService:
    @classmethod
    async def create_order(
        cls,
        db: AsyncSession,
        user_id: str,
        data: OrderCreate,
        idempotency_key: Optional[str] = None,
    ) -> OrderResponse:
        """
        Concurrency-safe order creation with:
        1. Idempotency protection against duplicate submissions.
        2. Deadlock prevention via deterministic product sorting.
        3. Row-level locks (SELECT FOR UPDATE) preventing inventory overselling.
        4. Atomic transaction with historical price snapshots.
        """
        # 1. Check for existing order with same idempotency key
        if idempotency_key:
            stmt = select(Order).where(Order.idempotency_key == idempotency_key)
            result = await db.execute(stmt)
            existing_order = result.scalar_one_or_none()
            if existing_order:
                # Fetch order items to build complete response
                items_stmt = select(OrderItem).where(OrderItem.order_id == existing_order.id)
                items_res = await db.execute(items_stmt)
                existing_items = items_res.scalars().all()
                return cls._build_order_response(existing_order, existing_items)

        # 2. Sort items lexicographically to prevent deadlocks under high concurrency
        sorted_items = sorted(data.items, key=lambda x: x.product_id)

        # 3. Lock products and verify stock
        product_ids = [item.product_id for item in sorted_items]
        stmt = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .with_for_update()
        )
        result = await db.execute(stmt)
        locked_products = {p.id: p for p in result.scalars().all()}

        # Verify all products exist and are active
        for item in sorted_items:
            product = locked_products.get(item.product_id)
            if not product or not product.is_active:
                raise NotFoundError("Product", item.product_id)

            if product.stock < item.quantity:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.stock,
                    requested=item.quantity,
                )

        # 4. Decrement inventory atomically and build order items
        subtotal = Decimal("0.00")
        order_items_to_create = []

        for item in sorted_items:
            product = locked_products[item.product_id]
            product.stock -= item.quantity
            if product.stock == 0:
                product.in_stock = False

            item_price = Decimal(str(product.price))
            item_total = item_price * item.quantity
            subtotal += item_total

            img_url = product.images[0] if (product.images and len(product.images) > 0) else ""

            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_image=img_url,
                unit=product.unit,
                price=item_price,
                quantity=item.quantity,
                total_price=item_total,
            )
            order_items_to_create.append(order_item)

        # 5. Calculate fees and totals
        discount = Decimal("0.00")
        if data.coupon_code:
            code = data.coupon_code.strip().upper()
            if code == "WELCOME50":
                discount = min(subtotal * Decimal("0.10"), Decimal("50.00"))
            elif code == "FREESHIP":
                discount = Decimal("0.00")

        delivery_fee = Decimal("0.00") if subtotal >= Decimal("500.00") else Decimal("40.00")
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        total = (subtotal - discount + delivery_fee + tax).quantize(Decimal("0.01"))

        # 6. Create Order record
        order = Order(
            user_id=user_id,
            idempotency_key=idempotency_key,
            status="order_placed",
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
            tax=tax,
            total=total,
            delivery_address=data.delivery_address,
            delivery_slot=data.delivery_slot,
            payment_method=data.payment_method,
            payment_status="paid" if data.payment_method == "card" else "pending",
        )
        db.add(order)
        await db.flush()  # Populates order.id

        # Associate items with order
        for oi in order_items_to_create:
            oi.order_id = order.id
            db.add(oi)

        # 7. Clear user cart if present
        cart_stmt = select(Cart).where(Cart.user_id == user_id)
        cart_res = await db.execute(cart_stmt)
        user_cart = cart_res.scalar_one_or_none()
        if user_cart:
            await db.execute(delete(CartItem).where(CartItem.cart_id == user_cart.id))

        await db.commit()
        await db.refresh(order)

        # 8. Invalidate product caches asynchronously
        for pid in product_ids:
            await CacheManager.delete(f"cache:product:{pid}")
        await CacheManager.delete_pattern("cache:products:*")

        return cls._build_order_response(order, order_items_to_create)

    @classmethod
    async def get_user_orders(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
    ) -> List[OrderResponse]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        orders = res.scalars().all()

        results = []
        for ord_obj in orders:
            item_stmt = select(OrderItem).where(OrderItem.order_id == ord_obj.id)
            item_res = await db.execute(item_stmt)
            items = item_res.scalars().all()
            results.append(cls._build_order_response(ord_obj, items))
        return results

    @classmethod
    async def get_order_by_id(
        cls,
        db: AsyncSession,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> OrderResponse:
        stmt = select(Order).where(Order.id == order_id)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)
        res = await db.execute(stmt)
        ord_obj = res.scalar_one_or_none()
        if not ord_obj:
            raise NotFoundError("Order", order_id)

        item_stmt = select(OrderItem).where(OrderItem.order_id == ord_obj.id)
        item_res = await db.execute(item_stmt)
        items = item_res.scalars().all()
        return cls._build_order_response(ord_obj, items)

    @staticmethod
    def _build_order_response(order: Order, items: List[OrderItem]) -> OrderResponse:
        item_responses = [
            OrderItemResponse(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product_name,
                product_image=i.product_image,
                unit=i.unit,
                price=Decimal(str(i.price)),
                quantity=i.quantity,
                total_price=Decimal(str(i.total_price)),
            )
            for i in items
        ]
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            subtotal=Decimal(str(order.subtotal)),
            discount=Decimal(str(order.discount)),
            delivery_fee=Decimal(str(order.delivery_fee)),
            tax=Decimal(str(order.tax)),
            total=Decimal(str(order.total)),
            delivery_address=order.delivery_address,
            delivery_slot=order.delivery_slot,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            created_at=order.created_at,
            items=item_responses,
        )
