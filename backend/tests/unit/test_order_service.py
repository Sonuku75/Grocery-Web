"""
Cartify Order Service Unit Tests (Module 10)

Unit tests for order number generation, lifecycle state machine, cancellation rules,
and schema serialization/alias mapping:
- Order number format: CRT-YYYYMMDD-XXXXXX with cryptographically secure unambiguous charset
- State machine transition validation (valid vs invalid transitions)
- Terminal state enforcement (DELIVERED, CANCELLED, FAILED cannot transition)
- Customer cancellation restrictions (only PENDING or CONFIRMED allowed)
- Dual camelCase and snake_case schema alias serialization
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.core.errors import CartifyException
from app.models.order import (
    FulfillmentStatus,
    OrderStatus,
    PaymentStatus,
)
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
from app.services.order_service import (
    ALLOWED_TRANSITIONS,
    CUSTOMER_CANCELLABLE_STATUSES,
    OrderService,
)


class TestOrderNumberGeneration:
    def test_order_number_format(self):
        """Generates order numbers matching CRT-YYYYMMDD-XXXXXX pattern."""
        num = OrderService.generate_order_number()
        pattern = r"^CRT-\d{8}-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{6}$"
        assert re.match(pattern, num), f"Order number '{num}' does not match pattern"

    def test_order_numbers_are_unique(self):
        """Generates distinct order numbers on successive calls."""
        numbers = {OrderService.generate_order_number() for _ in range(100)}
        assert len(numbers) == 100

    def test_order_number_excludes_ambiguous_characters(self):
        """Ensures 0, 1, I, O are never present in the random suffix."""
        ambiguous = set("01IO")
        for _ in range(50):
            num = OrderService.generate_order_number()
            suffix = num.split("-")[2]
            assert not any(c in ambiguous for c in suffix), f"Found ambiguous char in {num}"


class TestOrderStateMachine:
    def test_pending_allowed_transitions(self):
        valid = ALLOWED_TRANSITIONS[OrderStatus.PENDING]
        assert valid == {OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.FAILED}

    def test_confirmed_allowed_transitions(self):
        valid = ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED]
        assert valid == {OrderStatus.PROCESSING, OrderStatus.CANCELLED}

    def test_processing_allowed_transitions(self):
        valid = ALLOWED_TRANSITIONS[OrderStatus.PROCESSING]
        assert valid == {OrderStatus.SHIPPED, OrderStatus.CANCELLED}

    def test_shipped_allowed_transitions(self):
        valid = ALLOWED_TRANSITIONS[OrderStatus.SHIPPED]
        assert valid == {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED}

    def test_out_for_delivery_allowed_transitions(self):
        valid = ALLOWED_TRANSITIONS[OrderStatus.OUT_FOR_DELIVERY]
        assert valid == {OrderStatus.DELIVERED}

    def test_terminal_states_have_no_outward_transitions(self):
        assert ALLOWED_TRANSITIONS[OrderStatus.DELIVERED] == set()
        assert ALLOWED_TRANSITIONS[OrderStatus.CANCELLED] == set()
        assert ALLOWED_TRANSITIONS[OrderStatus.FAILED] == set()

    def test_customer_cancellable_statuses(self):
        assert CUSTOMER_CANCELLABLE_STATUSES == {OrderStatus.PENDING, OrderStatus.CONFIRMED}
        assert OrderStatus.PROCESSING not in CUSTOMER_CANCELLABLE_STATUSES
        assert OrderStatus.SHIPPED not in CUSTOMER_CANCELLABLE_STATUSES
        assert OrderStatus.OUT_FOR_DELIVERY not in CUSTOMER_CANCELLABLE_STATUSES
        assert OrderStatus.DELIVERED not in CUSTOMER_CANCELLABLE_STATUSES


class TestOrderSchemas:
    def test_create_order_request_camel_and_snake(self):
        req1 = CreateOrderRequest.model_validate({"checkoutSessionId": "cs-12345"})
        assert req1.checkout_session_id == "cs-12345"

        req2 = CreateOrderRequest.model_validate({"checkout_session_id": "cs-67890"})
        assert req2.checkout_session_id == "cs-67890"

    def test_order_address_snapshot_alias(self):
        data = {
            "fullName": "Sonu Sharma",
            "phone": "9876543210",
            "addressLine1": "Flat 402, Green Heights",
            "addressLine2": "Sector 62",
            "city": "Noida",
            "state": "Uttar Pradesh",
            "postalCode": "201301",
            "addressType": "HOME",
        }
        snapshot = OrderAddressSnapshot.model_validate(data)
        assert snapshot.recipient_name == "Sonu Sharma"
        assert snapshot.postal_code == "201301"

        dumped = snapshot.model_dump(by_alias=True)
        assert dumped["recipientName"] == "Sonu Sharma"
        assert dumped["postalCode"] == "201301"

    def test_order_item_response_serialization(self):
        item = OrderItemResponse(
            id="item-1",
            product_id="prod-1",
            variant_id="var-1",
            product_name="Aashirvaad Shudh Chakki Atta",
            variant_name="5 kg",
            sku="AASH-ATTA-5KG",
            unit_price=Decimal("245.00"),
            mrp=Decimal("275.00"),
            quantity=2,
            line_total=Decimal("490.00"),
            thumbnail_url="/images/atta.png",
        )
        dumped = item.model_dump(by_alias=True)
        assert dumped["productName"] == "Aashirvaad Shudh Chakki Atta"
        assert dumped["unitPrice"] == Decimal("245.00")
        assert dumped["lineTotal"] == Decimal("490.00")
        assert dumped["sku"] == "AASH-ATTA-5KG"

    def test_order_detail_response_structure(self):
        now = datetime.now(timezone.utc)
        order = OrderDetailResponse(
            id="ord-uuid-1",
            order_number="CRT-20260913-ABCXYZ",
            user_id="usr-123",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            fulfillment_status=FulfillmentStatus.UNFULFILLED,
            subtotal_amount=Decimal("490.00"),
            discount_amount=Decimal("50.00"),
            delivery_fee=Decimal("0.00"),
            tax_amount=Decimal("24.50"),
            total_amount=Decimal("464.50"),
            delivery_slot="Tomorrow, 10:00 AM - 1:00 PM",
            coupon_code="SAVE50",
            address_snapshot=OrderAddressSnapshot(
                recipient_name="Sonu Sharma",
                phone="9876543210",
                address_line_1="Flat 402",
                city="Noida",
                state="UP",
                postal_code="201301",
            ),
            items=[
                OrderItemResponse(
                    id="item-1",
                    product_id="prod-1",
                    variant_id="var-1",
                    product_name="Aashirvaad Shudh Chakki Atta",
                    variant_name="5 kg",
                    sku="AASH-ATTA-5KG",
                    unit_price=Decimal("245.00"),
                    mrp=Decimal("275.00"),
                    quantity=2,
                    line_total=Decimal("490.00"),
                )
            ],
            status_history=[
                OrderStatusHistoryResponse(
                    id="hist-1",
                    order_id="ord-uuid-1",
                    old_status=None,
                    new_status=OrderStatus.PENDING.value,
                    reason="Order placed from checkout",
                    created_at=now,
                )
            ],
            created_at=now,
        )
        dumped = order.model_dump(by_alias=True)
        assert dumped["orderNumber"] == "CRT-20260913-ABCXYZ"
        assert dumped["totalAmount"] == Decimal("464.50")
        assert len(dumped["items"]) == 1
        assert len(dumped["statusHistory"]) == 1
        assert dumped["items"][0]["sku"] == "AASH-ATTA-5KG"

    def test_admin_update_status_request_validation(self):
        req = AdminUpdateOrderStatusRequest(
            status=OrderStatus.CONFIRMED,
            fulfillment_status=FulfillmentStatus.PROCESSING,
            reason="Verified by warehouse team",
        )
        assert req.status == OrderStatus.CONFIRMED
        assert req.fulfillment_status == FulfillmentStatus.PROCESSING
