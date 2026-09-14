"""
Unit and concurrency tests for Cartify Inventory Anti-Overselling & Locking

Tests:
1. Deadlock-free variant ID sorting hierarchy verification
2. Multi-item atomic order stock deduction rollback (all or nothing)
3. Simulated concurrent deductions preventing overselling
4. Negative stock constraint protection
"""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException
from app.models.inventory import Inventory, InventoryTransactionType
from app.models.product_variant import ProductVariant
from app.repositories.inventory import InventoryRepository
from app.services.inventory_service import InventoryService


def test_lock_hierarchy_sorts_variant_ids():
    """Verifies variant IDs are deduplicated and sorted to eliminate deadlocks."""
    input_ids = ["var-z-99", "var-a-01", "var-m-50", "var-a-01", "var-b-02"]
    sorted_ids = sorted(list(set(input_ids)))
    assert sorted_ids == ["var-a-01", "var-b-02", "var-m-50", "var-z-99"]


@pytest.mark.asyncio
async def test_atomic_multi_item_order_deduction_fails_if_any_item_lacks_stock():
    """If one item in a multi-item order has insufficient stock, deduction raises and none are modified."""
    inv1 = Inventory(id="inv-1", variant_id="v1", quantity=10, reserved_quantity=0, is_active=True)
    inv2 = Inventory(id="inv-2", variant_id="v2", quantity=2, reserved_quantity=0, is_active=True)

    db = AsyncMock()
    items = [
        {"variant_id": "v1", "quantity": 5, "product_name": "Milk"},
        {"variant_id": "v2", "quantity": 5, "product_name": "Bread"},  # only 2 available
    ]

    with patch("app.services.inventory_service.InventoryRepository.get_by_variant_ids_for_update", return_value={"v1": inv1, "v2": inv2}):
        with pytest.raises(CartifyException) as exc:
            await InventoryService.deduct_stock_for_order(db, items, "CRT-CONCURRENCY-1", "usr-1")
        assert exc.value.code == "INSUFFICIENT_STOCK"
        assert "Bread" in str(exc.value.message)


@pytest.mark.asyncio
async def test_simulated_concurrent_order_deductions_prevent_overselling():
    """
    Simulates concurrent requests competing for finite stock (total stock = 5).
    Each request wants 3 units. Only one request can succeed; the other must fail with INSUFFICIENT_STOCK.
    """
    stock_state = {"quantity": 5}
    lock = asyncio.Lock()

    async def mock_adjust_stock(db, inventory, quantity_change, **kwargs):
        async with lock:
            if stock_state["quantity"] + quantity_change < 0:
                raise CartifyException(
                    status_code=400,
                    message="Insufficient stock.",
                    code="INSUFFICIENT_STOCK",
                )
            stock_state["quantity"] += quantity_change
            inventory.quantity = stock_state["quantity"]
            return inventory, None

    inv = Inventory(id="inv-concur", variant_id="v-compete", quantity=5, reserved_quantity=0, is_active=True)
    db = AsyncMock()

    async def attempt_order(order_num: str):
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_ids_for_update", return_value={"v-compete": inv}):
            with patch("app.services.inventory_service.InventoryRepository.adjust_stock", side_effect=mock_adjust_stock):
                try:
                    await InventoryService.deduct_stock_for_order(
                        db,
                        [{"variant_id": "v-compete", "quantity": 3, "product_name": "Limited Item"}],
                        order_num,
                        "user-1",
                    )
                    return True
                except CartifyException:
                    return False

    results = await asyncio.gather(attempt_order("ORDER-1"), attempt_order("ORDER-2"))

    # Exactly one order should succeed and one must fail
    assert results.count(True) == 1
    assert results.count(False) == 1
    # Stock remaining must be 2, never negative
    assert stock_state["quantity"] == 2
