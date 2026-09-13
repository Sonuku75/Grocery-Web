"""
Cartify Checkout Service Unit Tests (Module 9)

Unit tests for delivery fee calculation, pricing engine, snapshots, and checkout schemas:
- Delivery fee threshold (free above ₹499, ₹40 below, ₹0 for empty)
- Authoritative pricing with Decimal precision (subtotal - discount + delivery_fee + tax)
- Address & item snapshot serialization and validation
- Checkout session expiration logic
- Schema alias compatibility (camelCase and snake_case)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.models.address import Address
from app.models.checkout import CheckoutSession, CheckoutStatus
from app.models.coupon import Coupon, DiscountType
from app.schemas.checkout import (
    CheckoutAddressSnapshot,
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutItemSnapshot,
    CheckoutPreviewRequest,
    CheckoutSummaryResponse,
)
from app.services.checkout_service import CheckoutService
from app.services.delivery_fee_service import DeliveryFeeService
from app.services.pricing_service import PricingBreakdown, PricingService


class TestDeliveryFeeService:
    def test_free_delivery_above_threshold(self):
        # Above 499 threshold
        fee = DeliveryFeeService.calculate_delivery_fee(Decimal("500.00"))
        assert fee == Decimal("0.00")

    def test_free_delivery_at_exact_threshold(self):
        # Exactly 499 threshold
        fee = DeliveryFeeService.calculate_delivery_fee(Decimal("499.00"))
        assert fee == Decimal("0.00")

    def test_standard_delivery_fee_below_threshold(self):
        # Below 499 threshold -> standard fee ₹40.00
        fee = DeliveryFeeService.calculate_delivery_fee(Decimal("498.99"))
        assert fee == Decimal("40.00")

        fee_low = DeliveryFeeService.calculate_delivery_fee(Decimal("120.00"))
        assert fee_low == Decimal("40.00")

    def test_zero_or_negative_subtotal_has_zero_delivery_fee(self):
        fee_zero = DeliveryFeeService.calculate_delivery_fee(Decimal("0.00"))
        assert fee_zero == Decimal("0.00")

        fee_neg = DeliveryFeeService.calculate_delivery_fee(Decimal("-10.00"))
        assert fee_neg == Decimal("0.00")


class TestPricingService:
    def test_pricing_without_coupon_below_threshold(self):
        pricing = PricingService.calculate_totals(subtotal=Decimal("300.00"))
        assert pricing.subtotal == Decimal("300.00")
        assert pricing.discount == Decimal("0.00")
        assert pricing.delivery_fee == Decimal("40.00")
        assert pricing.tax == Decimal("0.00")
        assert pricing.total == Decimal("340.00")

    def test_pricing_without_coupon_above_threshold(self):
        pricing = PricingService.calculate_totals(subtotal=Decimal("600.00"))
        assert pricing.subtotal == Decimal("600.00")
        assert pricing.discount == Decimal("0.00")
        assert pricing.delivery_fee == Decimal("0.00")
        assert pricing.tax == Decimal("0.00")
        assert pricing.total == Decimal("600.00")

    def test_pricing_with_percentage_coupon(self):
        coupon = Coupon(
            id="cp-1",
            code="SAVE10",
            name="10% Off",
            discount_type=DiscountType.PERCENTAGE.value,
            discount_value=Decimal("10.00"),
            minimum_order_value=Decimal("100.00"),
            maximum_discount=Decimal("100.00"),
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            is_active=True,
        )
        # Subtotal 500: discount = 50, free delivery (subtotal >= 499), total = 450
        pricing = PricingService.calculate_totals(subtotal=Decimal("500.00"), coupon=coupon)
        assert pricing.subtotal == Decimal("500.00")
        assert pricing.discount == Decimal("50.00")
        assert pricing.delivery_fee == Decimal("0.00")
        assert pricing.total == Decimal("450.00")

    def test_pricing_with_fixed_coupon_and_delivery_fee(self):
        coupon = Coupon(
            id="cp-2",
            code="FLAT50",
            name="₹50 Off",
            discount_type=DiscountType.FIXED_AMOUNT.value,
            discount_value=Decimal("50.00"),
            minimum_order_value=Decimal("100.00"),
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            is_active=True,
        )
        # Subtotal 200: discount = 50, delivery fee = 40, total = 200 - 50 + 40 = 190
        pricing = PricingService.calculate_totals(subtotal=Decimal("200.00"), coupon=coupon)
        assert pricing.subtotal == Decimal("200.00")
        assert pricing.discount == Decimal("50.00")
        assert pricing.delivery_fee == Decimal("40.00")
        assert pricing.total == Decimal("190.00")

    def test_total_cannot_be_negative(self):
        coupon = Coupon(
            id="cp-huge",
            code="BIGDISC",
            name="Huge Discount",
            discount_type=DiscountType.FIXED_AMOUNT.value,
            discount_value=Decimal("1000.00"),
            minimum_order_value=Decimal("0.00"),
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            is_active=True,
        )
        # Subtotal 100: max discount is subtotal 100, delivery fee is 40 -> total = 40
        pricing = PricingService.calculate_totals(subtotal=Decimal("100.00"), coupon=coupon)
        assert pricing.subtotal == Decimal("100.00")
        assert pricing.discount == Decimal("100.00")
        assert pricing.delivery_fee == Decimal("40.00")
        assert pricing.total == Decimal("40.00")


class TestCheckoutModelsAndSchemas:
    def test_checkout_session_is_expired(self):
        now = datetime.now(timezone.utc)
        active_sess = CheckoutSession(
            id="sess-1",
            user_id="usr-1",
            cart_id="cart-1",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("140.00"),
            expires_at=now + timedelta(minutes=30),
        )
        assert not active_sess.is_expired

        expired_sess = CheckoutSession(
            id="sess-2",
            user_id="usr-1",
            cart_id="cart-1",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("140.00"),
            expires_at=now - timedelta(minutes=5),
        )
        assert expired_sess.is_expired

    def test_checkout_address_snapshot_creation(self):
        addr = Address(
            id="addr-1",
            user_id="usr-1",
            recipient_name="Rahul Sharma",
            phone="9876543210",
            address_line_1="Flat 402, Sunshine Apts",
            address_line_2="Koramangala 4th Block",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560034",
            label="Home",
            is_default=True,
        )
        snapshot = CheckoutService._create_address_snapshot(addr)
        assert snapshot.id == "addr-1"
        assert snapshot.recipient_name == "Rahul Sharma"
        assert snapshot.city == "Bengaluru"
        assert snapshot.postal_code == "560034"
        assert snapshot.label == "Home"

        # Dump to json dict and validate re-parsing
        dumped = snapshot.model_dump(mode="json", by_alias=True)
        assert dumped["recipientName"] == "Rahul Sharma"
        assert dumped["postalCode"] == "560034"

        reloaded = CheckoutAddressSnapshot.model_validate(dumped)
        assert reloaded.recipient_name == "Rahul Sharma"

    def test_checkout_item_snapshot_serialization(self):
        item = CheckoutItemSnapshot(
            variant_id="var-101",
            product_id="prod-1",
            sku="APPL-1KG",
            product_title="Fresh Shimla Apples",
            variant_name="1 kg pack",
            unit="1 kg",
            quantity=2,
            unit_price=Decimal("180.00"),
            line_total=Decimal("360.00"),
            thumbnail_url="https://images.cartify.com/apple.jpg",
        )
        dumped = item.model_dump(mode="json", by_alias=True)
        assert dumped["variantId"] == "var-101"
        assert dumped["productTitle"] == "Fresh Shimla Apples"
        assert dumped["lineTotal"] == "360.00"

        # Load from camelCase dict
        loaded = CheckoutItemSnapshot.model_validate(dumped)
        assert loaded.variant_id == "var-101"
        assert loaded.quantity == 2
        assert loaded.line_total == Decimal("360.00")

    def test_checkout_preview_request_aliases(self):
        req_camel = CheckoutPreviewRequest.model_validate({
            "addressId": "addr-123",
            "deliveryMethod": "EXPRESS",
            "deliverySlot": "Tomorrow • 10:00 AM",
        })
        assert req_camel.address_id == "addr-123"
        assert req_camel.delivery_method == "EXPRESS"
        assert req_camel.delivery_slot == "Tomorrow • 10:00 AM"

        req_snake = CheckoutPreviewRequest.model_validate({
            "address_id": "addr-456",
            "delivery_method": "STANDARD",
        })
        assert req_snake.address_id == "addr-456"
        assert req_snake.delivery_method == "STANDARD"

    def test_checkout_confirm_request_aliases(self):
        req_camel = CheckoutConfirmRequest.model_validate({
            "checkoutSessionId": "sess-xyz",
            "deliverySlot": "Evening 6-8 PM",
        })
        assert req_camel.checkout_session_id == "sess-xyz"
        assert req_camel.delivery_slot == "Evening 6-8 PM"

        req_snake = CheckoutConfirmRequest.model_validate({
            "session_id": "sess-abc",
        })
        assert req_snake.checkout_session_id == "sess-abc"
