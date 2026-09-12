"""
Cartify Address Repository (Module 2)

Encapsulates all database operations for customer delivery addresses.
Enforces strict user ownership queries and transactional default-address handling.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.address import Address

class AddressRepository:
    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str) -> List[Address]:
        """
        Lists all addresses for a user, ordered with the default address first,
        followed by the newest created addresses.
        """
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: str) -> int:
        """Returns the total number of addresses owned by the user."""
        stmt = select(func.count(Address.id)).where(Address.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_by_id(
        db: AsyncSession, address_id: str, user_id: Optional[str] = None
    ) -> Optional[Address]:
        """
        Retrieves address by ID. When user_id is provided, guarantees IDOR protection
        by scoping the query to the authenticated owner.
        """
        stmt = select(Address).where(Address.id == address_id)
        if user_id is not None:
            stmt = stmt.where(Address.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession, user_id: str, address_data: Dict[str, Any]
    ) -> Address:
        """Creates a new address for the given user."""
        address = Address(user_id=user_id, **address_data)
        db.add(address)
        await db.commit()
        await db.refresh(address)
        return address

    @staticmethod
    async def update(
        db: AsyncSession, address: Address, update_data: Dict[str, Any]
    ) -> Address:
        """Updates fields of an existing address."""
        for key, value in update_data.items():
            setattr(address, key, value)
        await db.commit()
        await db.refresh(address)
        return address

    @staticmethod
    async def delete(db: AsyncSession, address: Address) -> None:
        """Deletes an address record."""
        await db.delete(address)
        await db.commit()

    @staticmethod
    async def reset_defaults_for_user(db: AsyncSession, user_id: str) -> None:
        """Resets is_default to False for all addresses owned by user."""
        stmt = (
            update(Address)
            .where(Address.user_id == user_id, Address.is_default == True)
            .values(is_default=False)
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def promote_new_default(db: AsyncSession, user_id: str) -> Optional[Address]:
        """
        Promotes the newest remaining address as the default address
        after a default address is deleted.
        """
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate.is_default = True
            await db.commit()
            await db.refresh(candidate)
        return candidate
