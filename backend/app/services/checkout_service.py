"""
Cartify Checkout Service (Module 9)

Domain business logic for checkout sessions:
- Scoped strictly to authenticated user_id to eliminate IDOR vulnerabilities
- Authoritative server-side price calculation and item snapshotting
- Address ownership verification and preservation
- Re-validation of applied coupons against current subtotal and usage limits
- Automatic delivery fee calculation via DeliveryFeeService
- Detection and warning for product variant price changes
- State machine management (ACTIVE -> COMPLETED, EXPIRED, CANCELLED)
- Safe idempotent confirmation coordination
- Strict handoff state ("READY_FOR_ORDER") without triggering premature order creation
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import CartifyException
from app.models.address import Address
from app.models.checkout import CheckoutSession, CheckoutStatus
from app.models.coupon import Coupon
from app.repositories.address import AddressRepository
from app.repositories.cart import CartRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.coupon import CouponRepository
from app.schemas.checkout import (
    CheckoutAddressSnapshot,
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutItemSnapshot,
    CheckoutPreviewRequest,
    CheckoutSummaryResponse,
)
from app.schemas.coupon import CouponSummary
from app.services.coupon_service import CouponService
from app.services.pricing_service import PricingService

logger = logging.getLogger("cartify.checkout")


class CheckoutService:
    @classmethod
    def _create_address_snapshot(cls, address: Address) -> CheckoutAddressSnapshot:
        """Transforms an Address ORM model into an immutable CheckoutAddressSnapshot."""
        return CheckoutAddressSnapshot(
            id=address.id,
            recipient_name=address.recipient_name,
            phone=address.phone,
            address_line_1=address.address_line_1,
            address_line_2=address.address_line_2,
            landmark=address.landmark,
            city=address.city,
            state=address.state,
            country=address.country or "India",
            postal_code=address.postal_code,
            label=address.label or "Home",
            latitude=float(address.latitude) if address.latitude is not None else None,
            longitude=float(address.longitude) if address.longitude is not None else None,
        )

    @classmethod
    def _format_session_summary(
        cls,
        session: CheckoutSession,
        price_changed: bool = False,
        warning_message: Optional[str] = None,
    ) -> CheckoutSummaryResponse:
        """Transforms a CheckoutSession ORM model into a CheckoutSummaryResponse."""
        # Parse items snapshot
        items: List[CheckoutItemSnapshot] = []
        if session.items_snapshot:
            for raw_item in session.items_snapshot:
                items.append(CheckoutItemSnapshot.model_validate(raw_item))

        # Parse address snapshot
        address: Optional[CheckoutAddressSnapshot] = None
        if session.address_snapshot:
            address = CheckoutAddressSnapshot.model_validate(session.address_snapshot)
        elif session.address:
            address = cls._create_address_snapshot(session.address)

        # Coupon summary if present
        coupon_summary: Optional[CouponSummary] = None
        if session.coupon:
            coupon_summary = CouponSummary.model_validate(session.coupon)

        return CheckoutSummaryResponse(
            id=session.id,
            user_id=session.user_id,
            cart_id=session.cart_id,
            status=CheckoutStatus(session.status),
            items=items,
            address=address,
            subtotal=Decimal(str(session.subtotal)).quantize(Decimal("0.01")),
            discount=Decimal(str(session.discount_amount)).quantize(Decimal("0.01")),
            delivery_fee=Decimal(str(session.delivery_fee)).quantize(Decimal("0.01")),
            tax=Decimal(str(session.tax_amount)).quantize(Decimal("0.01")),
            total=Decimal(str(session.total_amount)).quantize(Decimal("0.01")),
            currency=session.currency or "INR",
            coupon=coupon_summary,
            delivery_method=session.delivery_method or "STANDARD",
            delivery_slot=session.delivery_slot,
            expires_at=session.expires_at,
            price_changed=price_changed,
            warning_message=warning_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    @classmethod
    async def preview_checkout(
        cls,
        db: AsyncSession,
        user_id: str,
        preview_data: Optional[CheckoutPreviewRequest] = None,
    ) -> CheckoutSummaryResponse:
        """
        Generates or refreshes an authoritative checkout preview for the customer:
        - Verifies cart contains active, valid items
        - Checks authoritative live product variant prices
        - Verifies and attaches chosen delivery address (or default address)
        - Re-validates applied coupon against minimum order thresholds
        - Computes server-authoritative delivery fee & subtotal/total
        - Persists or updates the active CheckoutSession
        """
        if preview_data is None:
            preview_data = CheckoutPreviewRequest()

        # 1. Retrieve user's cart
        cart = await CartRepository.get_by_user_id(db, user_id)
        if not cart or not cart.items:
            raise CartifyException(
                status_code=400,
                message="Cannot proceed to checkout with an empty cart.",
                code="EMPTY_CART",
            )

        # 2. Inspect items and build authoritative snapshot
        items_snapshot: List[CheckoutItemSnapshot] = []
        subtotal = Decimal("0.00")
        price_changed = False
        warning_messages: List[str] = []

        # Check existing active session to detect price changes
        existing_session = await CheckoutRepository.get_active_session_by_user_id(db, user_id)
        old_prices = {}
        if existing_session and existing_session.items_snapshot:
            for old_it in existing_session.items_snapshot:
                old_prices[old_it.get("variant_id") or old_it.get("variantId")] = Decimal(
                    str(old_it.get("unit_price") or old_it.get("unitPrice"))
                )

        for cart_item in cart.items:
            variant = cart_item.variant
            product = cart_item.product
            if not variant or not variant.is_active:
                prod_title = getattr(product, "name", None) or getattr(product, "title", None) or "An item in your cart"
                raise CartifyException(
                    status_code=400,
                    message=f"'{prod_title}' is currently unavailable. Please remove it to proceed.",
                    code="ITEM_UNAVAILABLE",
                )

            # Live stock check
            from app.services.inventory_service import InventoryService
            is_sufficient, avail_qty, msg = await InventoryService.check_stock(
                db, variant.id, cart_item.quantity
            )
            if not is_sufficient:
                prod_title = getattr(product, "name", None) or getattr(product, "title", None) or "Product"
                if avail_qty <= 0:
                    raise CartifyException(
                        status_code=400,
                        message=f"'{prod_title}' is currently out of stock.",
                        code="OUT_OF_STOCK",
                    )
                else:
                    raise CartifyException(
                        status_code=400,
                        message=f"Insufficient stock for '{prod_title}'. Only {avail_qty} available, requested {cart_item.quantity}.",
                        code="INSUFFICIENT_STOCK",
                    )

            current_price = Decimal(str(variant.price)).quantize(Decimal("0.01"))
            if variant.id in old_prices and old_prices[variant.id] != current_price:
                price_changed = True
                warning_messages.append(
                    f"Price for '{product.title}' updated from ₹{old_prices[variant.id]} to ₹{current_price}."
                )

            line_total = (current_price * cart_item.quantity).quantize(Decimal("0.01"))
            subtotal += line_total

            # Product image URL
            thumbnail_url = None
            if product and product.images and len(product.images) > 0:
                thumbnail_url = product.images[0].image_url
            elif product and getattr(product, "image_url", None):
                thumbnail_url = product.image_url

            unit_str = f"{variant.unit_value} {variant.unit_type}".strip() if variant.unit_value else variant.unit_type

            snapshot_item = CheckoutItemSnapshot(
                variant_id=variant.id,
                product_id=product.id if product else cart_item.product_id,
                sku=variant.sku,
                product_title=product.title if product else "Product",
                variant_name=variant.name,
                unit=unit_str,
                quantity=cart_item.quantity,
                unit_price=current_price,
                line_total=line_total,
                thumbnail_url=thumbnail_url,
            )
            items_snapshot.append(snapshot_item)

        subtotal = subtotal.quantize(Decimal("0.01"))

        # 3. Resolve Address
        address: Optional[Address] = None
        if preview_data.address_id:
            address = await AddressRepository.get_by_id(db, preview_data.address_id, user_id=user_id)
            if not address:
                raise CartifyException(
                    status_code=404,
                    message="Selected delivery address not found or does not belong to your account.",
                    code="ADDRESS_NOT_FOUND",
                )
        else:
            user_addresses = await AddressRepository.list_by_user(db, user_id)
            if user_addresses:
                address = user_addresses[0]

        address_snapshot = cls._create_address_snapshot(address) if address else None

        # 4. Re-validate Coupon
        applied_coupon: Optional[Coupon] = None
        if cart.coupon_id:
            coupon = await CouponRepository.get_by_id(db, cart.coupon_id)
            if coupon:
                is_valid, reason, _, _ = await CouponService.validate_coupon(
                    db, coupon, subtotal, user_id=user_id
                )
                if is_valid:
                    applied_coupon = coupon
                else:
                    warning_messages.append(f"Applied coupon '{coupon.code}' is no longer applicable: {reason}")

        # 5. Authoritative Pricing Calculation
        pricing = PricingService.calculate_totals(
            subtotal=subtotal,
            coupon=applied_coupon,
            delivery_method=preview_data.delivery_method or "STANDARD",
        )

        # 6. Expiration (30 minutes from now)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.CHECKOUT_SESSION_EXPIRE_MINUTES)

        delivery_slot = preview_data.delivery_slot or "Today • Express 15-Minute Delivery"
        delivery_method = preview_data.delivery_method or "STANDARD"

        session_data = {
            "user_id": user_id,
            "cart_id": cart.id,
            "address_id": address.id if address else None,
            "coupon_id": applied_coupon.id if applied_coupon else None,
            "delivery_method": delivery_method,
            "delivery_slot": delivery_slot,
            "subtotal": pricing.subtotal,
            "discount_amount": pricing.discount,
            "delivery_fee": pricing.delivery_fee,
            "tax_amount": pricing.tax,
            "total_amount": pricing.total,
            "currency": "INR",
            "address_snapshot": address_snapshot.model_dump(mode="json") if address_snapshot else None,
            "items_snapshot": [i.model_dump(mode="json") for i in items_snapshot],
            "expires_at": expires_at,
            "status": CheckoutStatus.ACTIVE.value,
        }

        # 7. Persist or Update Active Session
        if existing_session:
            session = await CheckoutRepository.update_session(db, existing_session, session_data)
        else:
            await CheckoutRepository.cancel_active_sessions_for_user(db, user_id)
            session = await CheckoutRepository.create_session(db, session_data)

        # Re-fetch session with relationships
        fresh_session = await CheckoutRepository.get_by_id(db, session.id, user_id)
        if not fresh_session:
            fresh_session = session

        warning_str = " ".join(warning_messages) if warning_messages else None

        return cls._format_session_summary(
            fresh_session,
            price_changed=price_changed,
            warning_message=warning_str,
        )

    @classmethod
    async def get_active_session(
        cls, db: AsyncSession, user_id: str
    ) -> CheckoutSummaryResponse:
        """
        Retrieves the user's currently active checkout session.
        Returns 404 if none exists or if it has expired.
        """
        session = await CheckoutRepository.get_active_session_by_user_id(db, user_id)
        if not session:
            raise CartifyException(
                status_code=404,
                message="No active checkout session found. Please initiate checkout preview.",
                code="CHECKOUT_NOT_FOUND",
            )
        return cls._format_session_summary(session)

    @classmethod
    async def confirm_checkout(
        cls,
        db: AsyncSession,
        user_id: str,
        confirm_data: CheckoutConfirmRequest,
        idempotency_key: Optional[str] = None,
    ) -> CheckoutConfirmResponse:
        """
        Confirms checkout session and marks it READY_FOR_ORDER (COMPLETED):
        - Safe idempotency checking
        - Address presence validation
        - Cart & items presence verification
        - Transitions session state to COMPLETED
        - Clean handoff boundary (Order & Payment in future modules)
        """
        # 1. Idempotency Check
        if idempotency_key:
            existing = await CheckoutRepository.get_by_idempotency_key(db, idempotency_key, user_id)
            if existing and existing.status == CheckoutStatus.COMPLETED.value:
                logger.info(f"Idempotent checkout confirm replay for key '{idempotency_key}'")
                return CheckoutConfirmResponse(
                    checkout_status="READY_FOR_ORDER",
                    checkout_session_id=existing.id,
                    summary=cls._format_session_summary(existing),
                    message="Checkout already confirmed.",
                )

        # 2. Retrieve Target Session
        session = await CheckoutRepository.get_by_id(db, confirm_data.checkout_session_id, user_id)
        if not session:
            raise CartifyException(
                status_code=404,
                message="Checkout session not found or does not belong to user.",
                code="CHECKOUT_NOT_FOUND",
            )

        # Check existing COMPLETED session
        if session.status == CheckoutStatus.COMPLETED.value:
            return CheckoutConfirmResponse(
                checkout_status="READY_FOR_ORDER",
                checkout_session_id=session.id,
                summary=cls._format_session_summary(session),
                message="Checkout already confirmed.",
            )

        # Check expiration
        if session.is_expired or session.status == CheckoutStatus.EXPIRED.value:
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

        # 3. Delivery Address Required
        if not session.address_snapshot and not session.address_id:
            raise CartifyException(
                status_code=400,
                message="A delivery address is required before confirming checkout.",
                code="ADDRESS_REQUIRED",
            )

        # 4. Cart Non-Empty Validation
        cart = await CartRepository.get_by_user_id(db, user_id)
        if not cart or not cart.items:
            raise CartifyException(
                status_code=400,
                message="Cannot confirm checkout with an empty cart.",
                code="EMPTY_CART",
            )

        # 5. Update session metadata and status
        update_fields = {"status": CheckoutStatus.COMPLETED.value}
        if idempotency_key:
            update_fields["idempotency_key"] = idempotency_key
        if confirm_data.delivery_slot:
            update_fields["delivery_slot"] = confirm_data.delivery_slot

        await CheckoutRepository.update_session(db, session, update_fields)

        fresh_session = await CheckoutRepository.get_by_id(db, session.id, user_id)
        if not fresh_session:
            fresh_session = session

        logger.info(f"Checkout session {session.id} successfully confirmed by user {user_id}")

        return CheckoutConfirmResponse(
            checkout_status="READY_FOR_ORDER",
            checkout_session_id=fresh_session.id,
            summary=cls._format_session_summary(fresh_session),
            message="Checkout confirmed and ready for order placement.",
        )

    @classmethod
    async def cancel_checkout(
        cls, db: AsyncSession, checkout_session_id: str, user_id: str
    ) -> bool:
        """
        Cancels an active checkout session.
        """
        session = await CheckoutRepository.get_by_id(db, checkout_session_id, user_id)
        if not session:
            raise CartifyException(
                status_code=404,
                message="Checkout session not found.",
                code="CHECKOUT_NOT_FOUND",
            )

        if session.status == CheckoutStatus.ACTIVE.value:
            await CheckoutRepository.mark_status(db, session, CheckoutStatus.CANCELLED)

        return True
