"""
Cartify Order Service (Module 10)

Domain business logic for order placement, lifecycle management, and auditing:
- Authoritative server-side purchase-time snapshots for items, prices, and address
- Human-friendly, non-guessable order number generation (CRT-YYYYMMDD-XXXXXX)
- Enforces strict state machine transitions and customer cancellation rules
- Atomic cart clearing and checkout session completion upon order placement
- Reliable deduplication with database-backed Idempotency-Key handling
- Scoped to authenticated user_id to prevent horizontal privilege escalation
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
import secrets
import string
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException
from app.models.checkout import CheckoutStatus
from app.models.order import (
    FulfillmentStatus,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.models.user import User
from app.repositories.cart import CartRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.coupon import CouponRepository
from app.repositories.order import OrderRepository
from app.schemas.order import (
    AdminUpdateOrderStatusRequest,
    CancelOrderRequest,
    CreateOrderRequest,
    OrderAddressSnapshot,
    OrderDetailResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderStatusHistoryResponse,
    OrderSummaryResponse,
)

logger = logging.getLogger("cartify.orders")

# Valid state machine transitions
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.FAILED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),   # Terminal
    OrderStatus.CANCELLED: set(),   # Terminal
    OrderStatus.FAILED: set(),      # Terminal
}

CUSTOMER_CANCELLABLE_STATUSES = {OrderStatus.PENDING, OrderStatus.CONFIRMED}


class OrderService:
    @classmethod
    def generate_order_number(cls) -> str:
        """
        Generates a human-friendly unique order number:
        Format: CRT-YYYYMMDD-XXXXXX (e.g., CRT-20260913-A8K4F2)
        Uses cryptographically secure random alphanumeric uppercase characters.
        """
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        alphabet = string.ascii_uppercase + string.digits
        # Avoid visually ambiguous characters
        safe_alphabet = alphabet.translate(str.maketrans("", "", "01IO"))
        suffix = "".join(secrets.choice(safe_alphabet) for _ in range(6))
        return f"CRT-{date_part}-{suffix}"

    @classmethod
    def _format_order_summary(cls, order: Order) -> OrderSummaryResponse:
        """Transforms an Order ORM model into a lightweight OrderSummaryResponse."""
        items = order.items or []
        first_item = items[0] if items else None
        item_count = sum(it.quantity for it in items) if items else 0

        return OrderSummaryResponse(
            id=order.id,
            order_number=order.order_number,
            status=OrderStatus(order.status),
            payment_status=PaymentStatus(order.payment_status),
            fulfillment_status=FulfillmentStatus(order.fulfillment_status),
            currency=order.currency or "INR",
            subtotal=Decimal(str(order.subtotal)).quantize(Decimal("0.01")),
            discount_amount=Decimal(str(order.discount_amount)).quantize(Decimal("0.01")),
            delivery_fee=Decimal(str(order.delivery_fee)).quantize(Decimal("0.01")),
            total_amount=Decimal(str(order.total_amount)).quantize(Decimal("0.01")),
            item_count=item_count,
            first_item_title=first_item.product_name if first_item else None,
            first_item_thumbnail=first_item.thumbnail_url if first_item else None,
            delivery_slot=order.delivery_slot,
            created_at=order.created_at,
        )

    @classmethod
    def _format_order_detail(cls, order: Order) -> OrderDetailResponse:
        """Transforms an Order ORM model into a complete OrderDetailResponse."""
        items_responses = []
        for it in (order.items or []):
            items_responses.append(
                OrderItemResponse(
                    id=it.id,
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    product_name=it.product_name,
                    variant_name=it.variant_name,
                    sku=it.sku,
                    unit_value=it.unit_value,
                    unit_type=it.unit_type,
                    unit_price=Decimal(str(it.unit_price)).quantize(Decimal("0.01")),
                    mrp=Decimal(str(it.mrp)).quantize(Decimal("0.01")) if it.mrp is not None else None,
                    quantity=it.quantity,
                    discount_amount=Decimal(str(it.discount_amount)).quantize(Decimal("0.01")),
                    line_total=Decimal(str(it.line_total)).quantize(Decimal("0.01")),
                    thumbnail_url=it.thumbnail_url,
                    created_at=it.created_at,
                )
            )

        history_responses = []
        for h in (order.status_history or []):
            history_responses.append(
                OrderStatusHistoryResponse(
                    id=h.id,
                    order_id=h.order_id,
                    old_status=h.old_status,
                    new_status=h.new_status,
                    changed_by_user_id=h.changed_by_user_id,
                    reason=h.reason,
                    created_at=h.created_at,
                )
            )

        address_snapshot = OrderAddressSnapshot(
            recipient_name=order.recipient_name,
            phone=order.phone,
            address_line_1=order.address_line_1,
            address_line_2=order.address_line_2,
            landmark=order.landmark,
            city=order.city,
            state=order.state,
            country=order.country or "India",
            postal_code=order.postal_code,
            address_label=order.address_label or "Home",
            latitude=float(order.latitude) if order.latitude is not None else None,
            longitude=float(order.longitude) if order.longitude is not None else None,
        )

        return OrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            status=OrderStatus(order.status),
            payment_status=PaymentStatus(order.payment_status),
            fulfillment_status=FulfillmentStatus(order.fulfillment_status),
            currency=order.currency or "INR",
            subtotal=Decimal(str(order.subtotal)).quantize(Decimal("0.01")),
            discount_amount=Decimal(str(order.discount_amount)).quantize(Decimal("0.01")),
            delivery_fee=Decimal(str(order.delivery_fee)).quantize(Decimal("0.01")),
            tax_amount=Decimal(str(order.tax_amount)).quantize(Decimal("0.01")),
            total_amount=Decimal(str(order.total_amount)).quantize(Decimal("0.01")),
            coupon_code=order.coupon_code,
            coupon_discount_amount=Decimal(str(order.coupon_discount_amount)).quantize(Decimal("0.01")),
            address=address_snapshot,
            delivery_method=order.delivery_method or "STANDARD",
            delivery_slot=order.delivery_slot,
            notes=order.notes,
            checkout_session_id=order.checkout_session_id,
            items=items_responses,
            status_history=history_responses,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    @classmethod
    async def create_order_from_checkout(
        cls,
        db: AsyncSession,
        user_id: str,
        create_in: CreateOrderRequest,
        idempotency_key: Optional[str] = None,
    ) -> OrderDetailResponse:
        """
        Creates an immutable Order from a validated checkout session:
        - Deduplication check via idempotency key
        - Checks if checkout session was already converted to an order
        - Validates checkout session ownership, status, address, and items
        - Preserves purchase-time snapshots of address, items, and pricing
        - Atomically clears purchased cart items
        - Transitions checkout session status to COMPLETED
        - Increments coupon usage counters if applicable
        """
        # 1. Idempotency Check
        if idempotency_key:
            existing_record = await OrderRepository.get_idempotency_record(
                db, user_id=user_id, key=idempotency_key
            )
            if existing_record:
                logger.info(f"Replaying cached order for Idempotency-Key '{idempotency_key}'")
                return OrderDetailResponse.model_validate(existing_record.response_body)

        # 2. Check if order already created from this checkout session
        existing_order = await OrderRepository.get_by_checkout_session_id(
            db, create_in.checkout_session_id
        )
        if existing_order:
            if existing_order.user_id != user_id:
                raise CartifyException(
                    status_code=404,
                    message="Checkout session not found or does not belong to user.",
                    code="CHECKOUT_NOT_FOUND",
                )
            return cls._format_order_detail(existing_order)

        # 3. Load and Validate Checkout Session
        session = await CheckoutRepository.get_by_id(
            db, create_in.checkout_session_id, user_id=user_id
        )
        if not session:
            raise CartifyException(
                status_code=404,
                message="Checkout session not found or does not belong to user.",
                code="CHECKOUT_NOT_FOUND",
            )

        if session.is_expired:
            await CheckoutRepository.mark_status(db, session, CheckoutStatus.EXPIRED)
            raise CartifyException(
                status_code=400,
                message="Checkout session has expired. Please initiate a new checkout preview.",
                code="CHECKOUT_EXPIRED",
            )

        if session.status == CheckoutStatus.CANCELLED.value:
            raise CartifyException(
                status_code=400,
                message="Checkout session has been cancelled.",
                code="CHECKOUT_CANCELLED",
            )

        # Address snapshot required
        addr_data = session.address_snapshot
        if not addr_data and session.address:
            from app.services.checkout_service import CheckoutService
            addr_data = CheckoutService._create_address_snapshot(session.address).model_dump(mode="json")

        if not addr_data:
            raise CartifyException(
                status_code=400,
                message="A delivery address is required before creating an order.",
                code="ADDRESS_REQUIRED",
            )

        # 4. Verify User Cart & Items
        cart = await CartRepository.get_by_user_id(db, user_id)
        if not cart or not cart.items:
            raise CartifyException(
                status_code=400,
                message="Cannot place order with an empty cart.",
                code="EMPTY_CART",
            )

        # Items snapshot verification
        items_snapshot = session.items_snapshot or []
        if not items_snapshot:
            raise CartifyException(
                status_code=400,
                message="Checkout session has no recorded item snapshots.",
                code="EMPTY_CHECKOUT_ITEMS",
            )

        # 5. Extract Purchase-time Snapshots
        recipient_name = addr_data.get("recipientName") or addr_data.get("recipient_name") or "Valued Customer"
        phone = addr_data.get("phone") or addr_data.get("mobile") or ""
        address_line_1 = addr_data.get("addressLine1") or addr_data.get("address_line_1") or ""
        address_line_2 = addr_data.get("addressLine2") or addr_data.get("address_line_2")
        landmark = addr_data.get("landmark")
        city = addr_data.get("city") or ""
        state = addr_data.get("state") or ""
        country = addr_data.get("country") or "India"
        postal_code = addr_data.get("postalCode") or addr_data.get("postal_code") or ""
        address_label = addr_data.get("label") or addr_data.get("addressLabel") or "Home"
        latitude = addr_data.get("latitude")
        longitude = addr_data.get("longitude")

        # Monetary snapshot
        subtotal = Decimal(str(session.subtotal)).quantize(Decimal("0.01"))
        discount_amount = Decimal(str(session.discount_amount)).quantize(Decimal("0.01"))
        delivery_fee = Decimal(str(session.delivery_fee)).quantize(Decimal("0.01"))
        tax_amount = Decimal(str(session.tax_amount)).quantize(Decimal("0.01"))
        total_amount = Decimal(str(session.total_amount)).quantize(Decimal("0.01"))

        # Coupon snapshot
        coupon_code = session.coupon.code if session.coupon else None
        coupon_discount_amount = discount_amount if coupon_code else Decimal("0.00")

        # 6. Generate Unique Order Number
        order_number = cls.generate_order_number()
        # Verify uniqueness
        while await OrderRepository.get_by_id(db, order_number):
            order_number = cls.generate_order_number()

        # 7. Prepare Order Data
        order_dict = {
            "user_id": user_id,
            "order_number": order_number,
            "status": OrderStatus.PENDING.value,
            "payment_status": PaymentStatus.PENDING.value,
            "fulfillment_status": FulfillmentStatus.UNFULFILLED.value,
            "currency": session.currency or "INR",
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "delivery_fee": delivery_fee,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "coupon_code": coupon_code,
            "coupon_discount_amount": coupon_discount_amount,
            "recipient_name": recipient_name,
            "phone": phone,
            "address_line_1": address_line_1,
            "address_line_2": address_line_2,
            "landmark": landmark,
            "city": city,
            "state": state,
            "country": country,
            "postal_code": postal_code,
            "address_label": address_label,
            "latitude": latitude,
            "longitude": longitude,
            "delivery_method": session.delivery_method or "STANDARD",
            "delivery_slot": session.delivery_slot,
            "notes": create_in.notes,
            "checkout_session_id": session.id,
        }

        # 8. Prepare Items Snapshots
        items_dict_list = []
        for it in items_snapshot:
            unit_price = Decimal(str(it.get("unit_price") or it.get("unitPrice"))).quantize(Decimal("0.01"))
            quantity = int(it.get("quantity") or 1)
            line_total = Decimal(str(it.get("line_total") or it.get("lineTotal"))).quantize(Decimal("0.01"))
            unit_str = it.get("unit") or ""
            parts = unit_str.split(" ", 1) if unit_str else []
            unit_val = parts[0] if len(parts) > 0 else None
            unit_t = parts[1] if len(parts) > 1 else None

            items_dict_list.append({
                "product_id": it.get("product_id") or it.get("productId"),
                "variant_id": it.get("variant_id") or it.get("variantId"),
                "product_name": it.get("product_title") or it.get("productTitle") or "Product",
                "variant_name": it.get("variant_name") or it.get("variantName"),
                "sku": it.get("sku"),
                "unit_value": unit_val,
                "unit_type": unit_t,
                "unit_price": unit_price,
                "mrp": unit_price,
                "quantity": quantity,
                "discount_amount": Decimal("0.00"),
                "line_total": line_total,
                "thumbnail_url": it.get("thumbnail_url") or it.get("thumbnailUrl"),
            })

        # 9. Deduct Inventory Stock (Atomic Row-Locking & Audit Trail)
        from app.services.inventory_service import InventoryService
        await InventoryService.deduct_stock_for_order(
            db=db,
            items=items_dict_list,
            order_number=order_number,
            user_id=user_id,
        )

        # 10. Atomic Transaction: Persist Order, Items, and Initial Status History
        created_order = await OrderRepository.create_order(
            db=db,
            order_data=order_dict,
            items_data=items_dict_list,
            initial_reason="Order created from checkout session",
        )

        # Emit Outbox Event for atomic notification delivery
        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="ORDER_CREATED",
            aggregate_type="ORDER",
            aggregate_id=created_order.id,
            user_id=user_id,
            payload={
                "order_id": created_order.id,
                "order_number": created_order.order_number,
                "total_amount": str(created_order.total_amount),
                "item_count": len(items_dict_list),
                "user_id": user_id,
            },
        )

        # 10. Mark CheckoutSession as COMPLETED
        await CheckoutRepository.mark_status(db, session, CheckoutStatus.COMPLETED)

        # 11. Clear Cart
        await CartRepository.clear_cart(db, cart.id)

        # 12. Record Coupon Usage if applied
        if session.coupon:
            await CouponRepository.record_usage(db, session.coupon, user_id)

        # 13. Re-fetch Order with relationships populated
        fresh_order = await OrderRepository.get_by_id(db, created_order.id, user_id=user_id)
        if not fresh_order:
            fresh_order = created_order

        response = cls._format_order_detail(fresh_order)

        # 14. Save Idempotency Record
        if idempotency_key:
            await OrderRepository.save_idempotency_record(
                db=db,
                user_id=user_id,
                key=idempotency_key,
                response_status=201,
                response_body=response.model_dump(mode="json"),
            )

        logger.info(f"Order #{fresh_order.order_number} (ID: {fresh_order.id}) placed successfully for user {user_id}")
        return response

    @classmethod
    async def get_order(
        cls, db: AsyncSession, order_id_or_number: str, user_id: str
    ) -> OrderDetailResponse:
        """
        Retrieves a single order by ID or order_number scoped to user_id.
        """
        order = await OrderRepository.get_by_id(db, order_id_or_number, user_id=user_id)
        if not order:
            raise CartifyException(
                status_code=404,
                message=f"Order '{order_id_or_number}' not found.",
                code="ORDER_NOT_FOUND",
            )
        return cls._format_order_detail(order)

    @classmethod
    async def list_orders(
        cls, db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
    ) -> OrderListResponse:
        """
        Retrieves paginated customer orders.
        """
        orders = await OrderRepository.list_by_user(db, user_id=user_id, limit=limit, offset=offset)
        total = await OrderRepository.count_by_user(db, user_id=user_id)
        summaries = [cls._format_order_summary(o) for o in orders]
        return OrderListResponse(
            items=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def cancel_order(
        cls,
        db: AsyncSession,
        order_id_or_number: str,
        user_id: str,
        cancel_in: Optional[CancelOrderRequest] = None,
    ) -> OrderDetailResponse:
        """
        Customer order cancellation:
        - Only permitted from PENDING or CONFIRMED states
        - Enforces state machine transition rules
        - Appends audit record to order_status_history
        """
        order = await OrderRepository.get_by_id(db, order_id_or_number, user_id=user_id)
        if not order:
            raise CartifyException(
                status_code=404,
                message=f"Order '{order_id_or_number}' not found.",
                code="ORDER_NOT_FOUND",
            )

        curr_status = OrderStatus(order.status)
        if curr_status not in CUSTOMER_CANCELLABLE_STATUSES:
            raise CartifyException(
                status_code=400,
                message=f"Order #{order.order_number} in status '{curr_status.value}' cannot be cancelled.",
                code="ORDER_NOT_CANCELLABLE",
            )

        reason = cancel_in.reason if cancel_in and cancel_in.reason else "Cancelled by customer"

        # Restore inventory stock for cancelled order items
        from app.services.inventory_service import InventoryService
        items_dict = [
            {"variant_id": it.variant_id, "quantity": it.quantity}
            for it in (order.items or [])
        ]
        await InventoryService.restore_stock_for_cancelled_order(
            db=db,
            items=items_dict,
            order_number=order.order_number,
            user_id=user_id,
        )

        updated = await OrderRepository.update_status(
            db=db,
            order=order,
            new_status=OrderStatus.CANCELLED.value,
            changed_by_user_id=user_id,
            reason=reason,
            fulfillment_status=FulfillmentStatus.CANCELLED.value,
        )

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="ORDER_CANCELLED",
            aggregate_type="ORDER",
            aggregate_id=order.id,
            user_id=user_id,
            payload={
                "order_id": order.id,
                "order_number": order.order_number,
                "reason": reason,
                "user_id": user_id,
            },
        )

        return cls._format_order_detail(updated)

    @classmethod
    async def admin_list_orders(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> OrderListResponse:
        """
        Admin order listing with search and status filtering.
        """
        orders, total = await OrderRepository.list_admin_orders(
            db, status=status, search=search, limit=limit, offset=offset
        )
        summaries = [cls._format_order_summary(o) for o in orders]
        return OrderListResponse(
            items=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def admin_get_order(
        cls, db: AsyncSession, order_id_or_number: str
    ) -> OrderDetailResponse:
        """
        Admin order retrieval without user scoping.
        """
        order = await OrderRepository.get_by_id(db, order_id_or_number)
        if not order:
            raise CartifyException(
                status_code=404,
                message=f"Order '{order_id_or_number}' not found.",
                code="ORDER_NOT_FOUND",
            )
        return cls._format_order_detail(order)

    @classmethod
    async def admin_update_status(
        cls,
        db: AsyncSession,
        order_id_or_number: str,
        admin_user: User,
        update_in: AdminUpdateOrderStatusRequest,
    ) -> OrderDetailResponse:
        """
        Admin status update with strict transition validation and audit logging.
        """
        order = await OrderRepository.get_by_id(db, order_id_or_number)
        if not order:
            raise CartifyException(
                status_code=404,
                message=f"Order '{order_id_or_number}' not found.",
                code="ORDER_NOT_FOUND",
            )

        curr_status = OrderStatus(order.status)
        target_status = update_in.status

        valid_targets = ALLOWED_TRANSITIONS.get(curr_status, set())
        if target_status not in valid_targets and target_status != curr_status:
            raise CartifyException(
                status_code=400,
                message=f"Invalid status transition from '{curr_status.value}' to '{target_status.value}'.",
                code="INVALID_STATUS_TRANSITION",
            )

        # Restore inventory stock if transitioning to CANCELLED
        if target_status == OrderStatus.CANCELLED and curr_status != OrderStatus.CANCELLED:
            from app.services.inventory_service import InventoryService
            items_dict = [
                {"variant_id": it.variant_id, "quantity": it.quantity}
                for it in (order.items or [])
            ]
            await InventoryService.restore_stock_for_cancelled_order(
                db=db,
                items=items_dict,
                order_number=order.order_number,
                user_id=admin_user.id,
            )

        fulfillment_val = update_in.fulfillment_status.value if update_in.fulfillment_status else None

        updated = await OrderRepository.update_status(
            db=db,
            order=order,
            new_status=target_status.value,
            changed_by_user_id=admin_user.id,
            reason=update_in.reason or f"Status updated to {target_status.value} by admin",
            fulfillment_status=fulfillment_val,
        )

        if target_status != curr_status:
            from app.services.notification_service import NotificationService
            event_mapping = {
                OrderStatus.CONFIRMED: "ORDER_CONFIRMED",
                OrderStatus.SHIPPED: "ORDER_SHIPPED",
                OrderStatus.DELIVERED: "ORDER_DELIVERED",
                OrderStatus.CANCELLED: "ORDER_CANCELLED",
            }
            if target_status in event_mapping:
                await NotificationService.emit_outbox_event(
                    db=db,
                    event_type=event_mapping[target_status],
                    aggregate_type="ORDER",
                    aggregate_id=order.id,
                    user_id=order.user_id,
                    payload={
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "status": target_status.value,
                        "user_id": order.user_id,
                    },
                )

        return cls._format_order_detail(updated)
