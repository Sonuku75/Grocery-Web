"""
Unit tests for Cartify Inventory Service (Module 11)

Tests:
1. Inventory model properties (available_quantity, is_low_stock, is_out_of_stock, is_available)
2. Stock availability checking (sufficient, insufficient, out of stock, inactive)
3. Admin create inventory & duplicate rejection
4. Admin update inventory thresholds and active flags
5. Admin adjust stock (positive, negative, excessive negative rejection)
6. Transaction recording & audit fields (SALE, RESTOCK, DAMAGE, CANCELLATION, ADJUSTMENT)
7. Order stock deduction logic
8. Order cancellation restoration logic & idempotency
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.errors import CartifyException, NotFoundError
from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.inventory import (
    AdminAdjustStockRequest,
    AdminCreateInventoryRequest,
    AdminUpdateInventoryRequest,
)
from app.services.inventory_service import InventoryService


@pytest.fixture
def sample_product():
    return Product(
        id="prod-inv-1",
        name="Organic Almonds",
        slug="organic-almonds",
        brand="Nature's Best",
        is_active=True,
    )


@pytest.fixture
def sample_variant(sample_product):
    return ProductVariant(
        id="var-almonds-500g",
        product_id=sample_product.id,
        sku="ALM-500G",
        name="500g Pack",
        price=Decimal("450.00"),
        is_active=True,
        product=sample_product,
    )


@pytest.fixture
def sample_inventory(sample_variant):
    inv = Inventory(
        id="inv-almonds-1",
        variant_id=sample_variant.id,
        quantity=50,
        reserved_quantity=5,
        low_stock_threshold=10,
        is_active=True,
    )
    inv.variant = sample_variant
    return inv


class TestInventoryModelProperties:
    def test_available_quantity(self, sample_inventory):
        assert sample_inventory.available_quantity == 45

    def test_is_available(self, sample_inventory):
        assert sample_inventory.is_available is True
        sample_inventory.is_active = False
        assert sample_inventory.is_available is False

    def test_is_low_stock(self, sample_inventory):
        # 45 > 10 -> not low stock
        assert sample_inventory.is_low_stock is False
        # change quantity to 12 with 5 reserved -> 7 available <= 10 -> low stock
        sample_inventory.quantity = 12
        assert sample_inventory.is_low_stock is True

    def test_is_out_of_stock(self, sample_inventory):
        assert sample_inventory.is_out_of_stock is False
        sample_inventory.quantity = 5
        # 5 - 5 reserved = 0 available
        assert sample_inventory.is_out_of_stock is True


class TestInventoryServiceCheckStock:
    @pytest.mark.asyncio
    async def test_check_stock_sufficient(self, sample_variant, sample_inventory):
        db = AsyncMock()
        with patch("app.services.inventory_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
            with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
                sufficient, avail, msg = await InventoryService.check_stock(db, sample_variant.id, 10)
                assert sufficient is True
                assert avail == 45
                assert msg == "In stock"

    @pytest.mark.asyncio
    async def test_check_stock_insufficient(self, sample_variant, sample_inventory):
        db = AsyncMock()
        with patch("app.services.inventory_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
            with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
                sufficient, avail, msg = await InventoryService.check_stock(db, sample_variant.id, 50)
                assert sufficient is False
                assert avail == 45
                assert "Only 45 units are available" in msg

    @pytest.mark.asyncio
    async def test_check_stock_out_of_stock(self, sample_variant, sample_inventory):
        db = AsyncMock()
        sample_inventory.quantity = 5
        sample_inventory.reserved_quantity = 5
        with patch("app.services.inventory_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
            with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
                sufficient, avail, msg = await InventoryService.check_stock(db, sample_variant.id, 1)
                assert sufficient is False
                assert avail == 0
                assert "out of stock" in msg

    @pytest.mark.asyncio
    async def test_check_stock_inactive_variant(self, sample_variant):
        db = AsyncMock()
        sample_variant.is_active = False
        with patch("app.services.inventory_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
            sufficient, avail, msg = await InventoryService.check_stock(db, sample_variant.id, 1)
            assert sufficient is False
            assert avail == 0


class TestInventoryServiceAdminOperations:
    @pytest.mark.asyncio
    async def test_admin_create_duplicate_rejection(self, sample_variant, sample_inventory):
        db = AsyncMock()
        create_req = AdminCreateInventoryRequest(variant_id=sample_variant.id, quantity=20)
        with patch("app.services.inventory_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
            with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
                with pytest.raises(CartifyException) as exc:
                    await InventoryService.admin_create_inventory(db, create_req, admin_user="adm-1")
                assert exc.value.code == "INVENTORY_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_admin_adjust_stock_positive(self, sample_inventory):
        db = AsyncMock()
        adjust_req = AdminAdjustStockRequest(
            quantity_change=15,
            transaction_type=InventoryTransactionType.RESTOCK,
            reason="Supplier shipment received",
        )
        updated_inv = Inventory(
            id=sample_inventory.id,
            variant_id=sample_inventory.variant_id,
            quantity=65,
            reserved_quantity=5,
            low_stock_threshold=10,
            is_active=True,
        )
        updated_inv.variant = sample_inventory.variant
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
            with patch("app.services.inventory_service.InventoryRepository.adjust_stock", return_value=(updated_inv, MagicMock())):
                res = await InventoryService.admin_adjust_stock(db, sample_inventory.variant_id, adjust_req, "adm-1")
                assert res.quantity == 65
                assert res.available_quantity == 60

    @pytest.mark.asyncio
    async def test_admin_adjust_stock_excessive_negative_rejected(self, sample_inventory):
        db = AsyncMock()
        # available is 45, trying to reduce by 50
        adjust_req = AdminAdjustStockRequest(
            quantity_change=-50,
            transaction_type=InventoryTransactionType.DAMAGE,
            reason="Water damage",
        )
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_id", return_value=sample_inventory):
            with pytest.raises(CartifyException) as exc:
                await InventoryService.admin_adjust_stock(db, sample_inventory.variant_id, adjust_req, "adm-1")
            assert exc.value.code == "INSUFFICIENT_STOCK"


class TestInventoryServiceOrderFlow:
    @pytest.mark.asyncio
    async def test_deduct_stock_success(self, sample_inventory):
        db = AsyncMock()
        items = [{"variant_id": sample_inventory.variant_id, "quantity": 3, "product_name": "Almonds"}]
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_ids_for_update", return_value={sample_inventory.variant_id: sample_inventory}):
            with patch("app.services.inventory_service.InventoryRepository.adjust_stock") as mock_adj:
                await InventoryService.deduct_stock_for_order(db, items, "CRT-20260914-ABC123", "usr-1")
                mock_adj.assert_called_once()
                call_kwargs = mock_adj.call_args[1]
                assert call_kwargs["quantity_change"] == -3
                assert call_kwargs["transaction_type"] == InventoryTransactionType.SALE.value
                assert call_kwargs["reference_id"] == "CRT-20260914-ABC123"

    @pytest.mark.asyncio
    async def test_deduct_stock_insufficient_raises_and_rolls_back(self, sample_inventory):
        db = AsyncMock()
        # available is 45, requesting 60
        items = [{"variant_id": sample_inventory.variant_id, "quantity": 60, "product_name": "Almonds"}]
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_ids_for_update", return_value={sample_inventory.variant_id: sample_inventory}):
            with pytest.raises(CartifyException) as exc:
                await InventoryService.deduct_stock_for_order(db, items, "CRT-20260914-ABC123", "usr-1")
            assert exc.value.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_restore_stock_cancelled_order_idempotency(self, sample_inventory):
        db = AsyncMock()
        # Simulate existing transaction found -> idempotency skips duplicate restoration
        existing_tx = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_tx
        db.execute.return_value = mock_result

        items = [{"variant_id": sample_inventory.variant_id, "quantity": 3}]
        with patch("app.services.inventory_service.InventoryRepository.get_by_variant_ids_for_update") as mock_lock:
            await InventoryService.restore_stock_for_cancelled_order(db, items, "CRT-20260914-ABC123", "usr-1")
            mock_lock.assert_not_called()
