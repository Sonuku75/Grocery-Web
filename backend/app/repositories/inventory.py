"""
Cartify Inventory Repository (Module 11)

Data-access layer for inventory and audit transactions:
- PostgreSQL-backed queries with row-level locking (with_for_update)
- Deadlock-free batch row locking via sorted variant IDs
- Filtering across variants, products, low-stock, and out-of-stock
- Atomic adjustment and transaction creation
"""

import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import CartifyException
from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.product import Product
from app.models.product_variant import ProductVariant

logger = logging.getLogger("cartify.inventory")


class InventoryRepository:
    @staticmethod
    async def get_by_variant_id(
        db: AsyncSession, variant_id: str, for_update: bool = False
    ) -> Optional[Inventory]:
        """
        Retrieves inventory record by variant_id with optional row-level lock.
        """
        stmt = (
            select(Inventory)
            .where(Inventory.variant_id == variant_id)
            .options(
                selectinload(Inventory.variant).selectinload(ProductVariant.product)
            )
        )
        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        val = result.scalar_one_or_none()
        import inspect
        if inspect.isawaitable(val):
            val = await val
        return val

    @staticmethod
    async def get_by_variant_ids_for_update(
        db: AsyncSession, variant_ids: List[str]
    ) -> Dict[str, Inventory]:
        """
        Batch row-locks inventory records for multiple variants.
        Crucial for preventing race conditions and overselling.
        Sorts variant IDs to guarantee a deterministic lock acquisition order,
        eliminating database deadlocks.
        """
        if not variant_ids:
            return {}

        sorted_ids = sorted(list(set(variant_ids)))
        stmt = (
            select(Inventory)
            .where(Inventory.variant_id.in_(sorted_ids))
            .options(
                selectinload(Inventory.variant).selectinload(ProductVariant.product)
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        return {inv.variant_id: inv for inv in records}

    @staticmethod
    async def get_by_id(
        db: AsyncSession, inventory_id: str, for_update: bool = False
    ) -> Optional[Inventory]:
        """
        Retrieves inventory record by inventory.id with optional row-level lock.
        """
        stmt = (
            select(Inventory)
            .where(Inventory.id == inventory_id)
            .options(
                selectinload(Inventory.variant).selectinload(ProductVariant.product)
            )
        )
        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        variant_id: str,
        quantity: int = 0,
        low_stock_threshold: int = 5,
        is_active: bool = True,
        created_by_user_id: Optional[str] = None,
    ) -> Inventory:
        """
        Initializes an inventory row and writes an initial transaction audit entry.
        """
        inventory = Inventory(
            variant_id=variant_id,
            quantity=quantity,
            reserved_quantity=0,
            low_stock_threshold=low_stock_threshold,
            is_active=is_active,
        )
        db.add(inventory)
        await db.flush()

        initial_tx = InventoryTransaction(
            inventory_id=inventory.id,
            variant_id=variant_id,
            transaction_type=InventoryTransactionType.INITIAL.value,
            quantity_change=quantity,
            quantity_before=0,
            quantity_after=quantity,
            reference_type="INITIAL_SETUP",
            reference_id=None,
            reason="Initial inventory creation",
            created_by_user_id=created_by_user_id,
        )
        db.add(initial_tx)
        await db.flush()

        # Re-fetch with relationships loaded
        return await InventoryRepository.get_by_id(db, inventory.id) or inventory

    @staticmethod
    async def update(
        db: AsyncSession,
        inventory: Inventory,
        low_stock_threshold: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Inventory:
        """
        Updates non-quantity operational settings.
        """
        if low_stock_threshold is not None:
            inventory.low_stock_threshold = low_stock_threshold
        if is_active is not None:
            inventory.is_active = is_active

        await db.flush()
        return inventory

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        inventory: Inventory,
        quantity_change: int,
        transaction_type: str,
        reason: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
    ) -> Tuple[Inventory, InventoryTransaction]:
        """
        Atomically mutates inventory total quantity and creates an audit transaction.
        Enforces that quantity never falls below 0 or below reserved_quantity.
        """
        qty_before = inventory.quantity
        qty_after = qty_before + quantity_change

        if qty_after < 0:
            raise CartifyException(
                status_code=400,
                message=f"Stock adjustment would result in negative quantity ({qty_after}). Current quantity is {qty_before}.",
                code="NEGATIVE_STOCK",
            )

        if qty_after < inventory.reserved_quantity:
            raise CartifyException(
                status_code=400,
                message=f"Stock adjustment to {qty_after} would violate reserved quantity of {inventory.reserved_quantity}.",
                code="NEGATIVE_STOCK",
            )

        inventory.quantity = qty_after

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            variant_id=inventory.variant_id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            quantity_before=qty_before,
            quantity_after=qty_after,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
            created_by_user_id=created_by_user_id,
        )
        db.add(tx)
        await db.flush()
        return inventory, tx

    @staticmethod
    async def list_admin_inventory(
        db: AsyncSession,
        variant_id: Optional[str] = None,
        product_id: Optional[str] = None,
        low_stock: Optional[bool] = None,
        out_of_stock: Optional[bool] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Inventory], int]:
        """
        Lists inventory records across variants with comprehensive filters.
        """
        stmt = (
            select(Inventory)
            .join(Inventory.variant)
            .options(
                selectinload(Inventory.variant).selectinload(ProductVariant.product)
            )
        )
        count_stmt = select(func.count(Inventory.id)).join(Inventory.variant)

        if variant_id:
            stmt = stmt.where(Inventory.variant_id == variant_id)
            count_stmt = count_stmt.where(Inventory.variant_id == variant_id)

        if product_id:
            stmt = stmt.where(ProductVariant.product_id == product_id)
            count_stmt = count_stmt.where(ProductVariant.product_id == product_id)

        if is_active is not None:
            stmt = stmt.where(Inventory.is_active == is_active)
            count_stmt = count_stmt.where(Inventory.is_active == is_active)

        if low_stock is True:
            # available_quantity <= low_stock_threshold
            cond = (Inventory.quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        if out_of_stock is True:
            # available_quantity <= 0 or not active
            cond = (Inventory.quantity - Inventory.reserved_quantity) <= 0
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(Inventory.updated_at.desc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        records = res.scalars().all()

        return list(records), total

    @staticmethod
    async def list_transactions(
        db: AsyncSession,
        variant_id: Optional[str] = None,
        inventory_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[InventoryTransaction], int]:
        """
        Lists paginated audit transactions for a variant or inventory record.
        """
        stmt = select(InventoryTransaction)
        count_stmt = select(func.count(InventoryTransaction.id))

        if variant_id:
            stmt = stmt.where(InventoryTransaction.variant_id == variant_id)
            count_stmt = count_stmt.where(InventoryTransaction.variant_id == variant_id)

        if inventory_id:
            stmt = stmt.where(InventoryTransaction.inventory_id == inventory_id)
            count_stmt = count_stmt.where(InventoryTransaction.inventory_id == inventory_id)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(InventoryTransaction.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        records = res.scalars().all()

        return list(records), total
