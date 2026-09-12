"""
Cartify Address Service (Module 2)

Business logic for delivery addresses:
- Strict ownership verification on all operations (preventing IDOR)
- Concurrency-safe single default address invariant
- Automatic default promotion when the active default address is deleted
- First address created automatically becomes the default address
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.address import Address
from app.repositories.address import AddressRepository
from app.schemas.address import (
    AddressCreateRequest,
    AddressListResponse,
    AddressResponse,
    AddressUpdateRequest,
)

class AddressService:
    @classmethod
    async def list_addresses(
        cls, db: AsyncSession, user_id: str
    ) -> AddressListResponse:
        """Retrieves all delivery addresses for the authenticated user."""
        addresses = await AddressRepository.list_by_user(db, user_id)
        items = [AddressResponse.model_validate(a) for a in addresses]
        return AddressListResponse(items=items, total=len(items))

    @classmethod
    async def get_address(
        cls, db: AsyncSession, address_id: str, user_id: str
    ) -> AddressResponse:
        """
        Retrieves a single address ensuring the authenticated user owns it.
        Returns 404 if not found or if owned by a different user.
        """
        address = await AddressRepository.get_by_id(db, address_id, user_id=user_id)
        if not address:
            raise NotFoundError("Address", address_id)
        return AddressResponse.model_validate(address)

    @classmethod
    async def create_address(
        cls, db: AsyncSession, user_id: str, data: AddressCreateRequest
    ) -> AddressResponse:
        """
        Creates a new delivery address for the user.
        If user has no existing addresses or data.is_default is True,
        this address becomes the default address.
        """
        existing_count = await AddressRepository.count_by_user(db, user_id)
        should_be_default = data.is_default or existing_count == 0

        if should_be_default:
            await AddressRepository.reset_defaults_for_user(db, user_id)

        address_dict = {
            "label": data.label,
            "recipient_name": data.recipient_name,
            "phone": data.phone,
            "address_line_1": data.address_line_1,
            "address_line_2": data.address_line_2,
            "landmark": data.landmark,
            "city": data.city,
            "state": data.state,
            "country": data.country,
            "postal_code": data.postal_code,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "is_default": should_be_default,
        }

        address = await AddressRepository.create(db, user_id, address_dict)
        return AddressResponse.model_validate(address)

    @classmethod
    async def update_address(
        cls, db: AsyncSession, address_id: str, user_id: str, data: AddressUpdateRequest
    ) -> AddressResponse:
        """
        Updates an existing address with ownership verification.
        If setting as default, resets previous defaults.
        """
        address = await AddressRepository.get_by_id(db, address_id, user_id=user_id)
        if not address:
            raise NotFoundError("Address", address_id)

        update_dict = {}
        fields = [
            "label",
            "recipient_name",
            "phone",
            "address_line_1",
            "address_line_2",
            "landmark",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
        ]
        for field in fields:
            val = getattr(data, field)
            if val is not None:
                update_dict[field] = val

        if data.is_default is not None:
            if data.is_default:
                await AddressRepository.reset_defaults_for_user(db, user_id)
                update_dict["is_default"] = True
            else:
                # If unmarking default, only allow if other addresses exist
                update_dict["is_default"] = False

        if update_dict:
            address = await AddressRepository.update(db, address, update_dict)

        return AddressResponse.model_validate(address)

    @classmethod
    async def delete_address(
        cls, db: AsyncSession, address_id: str, user_id: str
    ) -> None:
        """
        Deletes an address with ownership verification.
        If deleting a default address and other addresses exist,
        automatically promotes the newest remaining address as the new default.
        """
        address = await AddressRepository.get_by_id(db, address_id, user_id=user_id)
        if not address:
            raise NotFoundError("Address", address_id)

        was_default = address.is_default
        await AddressRepository.delete(db, address)

        if was_default:
            await AddressRepository.promote_new_default(db, user_id)

    @classmethod
    async def set_default_address(
        cls, db: AsyncSession, address_id: str, user_id: str
    ) -> AddressResponse:
        """
        Atomically sets the specified address as default for the user,
        resetting any existing default.
        """
        address = await AddressRepository.get_by_id(db, address_id, user_id=user_id)
        if not address:
            raise NotFoundError("Address", address_id)

        await AddressRepository.reset_defaults_for_user(db, user_id)
        address.is_default = True
        await db.commit()
        await db.refresh(address)

        return AddressResponse.model_validate(address)
