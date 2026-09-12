"""
Unit tests for Cartify AddressService and Schemas (Module 2)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import NotFoundError
from app.models.address import Address
from app.schemas.address import (
    AddressCreateRequest,
    AddressUpdateRequest,
)
from app.services.address import AddressService

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def sample_address():
    return Address(
        id="addr-101",
        user_id="usr-test-1",
        label="Home",
        recipient_name="Sonu Kumar",
        phone="9876543210",
        address_line_1="123 Civil Lines",
        address_line_2="Near Raj Mandir",
        landmark="Opposite Metro Station",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302001",
        latitude=26.9124,
        longitude=75.7873,
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

# ----------------- Validation Tests -----------------

def test_pincode_validation_success():
    req = AddressCreateRequest(
        recipient_name="Sonu Kumar",
        phone="9876543210",
        address_line_1="123 Civil Lines",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302001",
    )
    assert req.postal_code == "302001"

def test_pincode_validation_failure_short():
    with pytest.raises(ValueError) as exc:
        AddressCreateRequest(
            recipient_name="Sonu Kumar",
            phone="9876543210",
            address_line_1="123 Civil Lines",
            city="Jaipur",
            state="Rajasthan",
            country="India",
            postal_code="30200",  # Only 5 digits
        )
    assert "Invalid Indian PIN code" in str(exc.value)

def test_pincode_validation_failure_leading_zero():
    with pytest.raises(ValueError) as exc:
        AddressCreateRequest(
            recipient_name="Sonu Kumar",
            phone="9876543210",
            address_line_1="123 Civil Lines",
            city="Jaipur",
            state="Rajasthan",
            country="India",
            postal_code="012345",  # Starts with 0
        )
    assert "Invalid Indian PIN code" in str(exc.value)

def test_phone_validation_success_indian():
    req = AddressCreateRequest(
        recipient_name="Sonu Kumar",
        phone="+91 98765 43210",
        address_line_1="123 Civil Lines",
        city="Jaipur",
        state="Rajasthan",
        postal_code="302001",
    )
    assert req.phone == "+919876543210"

def test_phone_validation_failure():
    with pytest.raises(ValueError) as exc:
        AddressCreateRequest(
            recipient_name="Sonu Kumar",
            phone="98765abcde",  # Letters in phone number
            address_line_1="123 Civil Lines",
            city="Jaipur",
            state="Rajasthan",
            postal_code="302001",
        )
    assert "Invalid phone number format" in str(exc.value)

# ----------------- Service Logic Tests -----------------

@pytest.mark.asyncio
async def test_first_address_automatically_default(mock_db, sample_address):
    with patch("app.services.address.AddressRepository") as mock_repo:
        # User has 0 existing addresses
        mock_repo.count_by_user = AsyncMock(return_value=0)
        mock_repo.reset_defaults_for_user = AsyncMock()
        mock_repo.create = AsyncMock(return_value=sample_address)

        req = AddressCreateRequest(
            recipient_name="Sonu Kumar",
            phone="9876543210",
            address_line_1="123 Civil Lines",
            city="Jaipur",
            state="Rajasthan",
            postal_code="302001",
            is_default=False,  # User didn't check default, but it's their 1st address
        )

        res = await AddressService.create_address(mock_db, "usr-test-1", req)

        # In create_address, should_be_default is True
        call_args = mock_repo.create.call_args[0][2]
        assert call_args["is_default"] is True
        mock_repo.reset_defaults_for_user.assert_called_once_with(mock_db, "usr-test-1")

@pytest.mark.asyncio
async def test_subsequent_non_default_address(mock_db, sample_address):
    with patch("app.services.address.AddressRepository") as mock_repo:
        # User already has 1 address
        mock_repo.count_by_user = AsyncMock(return_value=1)
        mock_repo.create = AsyncMock(return_value=sample_address)

        req = AddressCreateRequest(
            recipient_name="Sonu Kumar",
            phone="9876543210",
            address_line_1="Office Park",
            city="Jaipur",
            state="Rajasthan",
            postal_code="302001",
            is_default=False,
        )

        await AddressService.create_address(mock_db, "usr-test-1", req)
        call_args = mock_repo.create.call_args[0][2]
        assert call_args["is_default"] is False

@pytest.mark.asyncio
async def test_get_address_owner_protection(mock_db, sample_address):
    with patch("app.services.address.AddressRepository") as mock_repo:
        # Owner access succeeds
        mock_repo.get_by_id = AsyncMock(return_value=sample_address)
        res = await AddressService.get_address(mock_db, "addr-101", "usr-test-1")
        assert res.id == "addr-101"

        # Non-owner access raises 404 (IDOR protected)
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await AddressService.get_address(mock_db, "addr-101", "other-user-999")

@pytest.mark.asyncio
async def test_delete_default_address_promotes_remaining(mock_db, sample_address):
    with patch("app.services.address.AddressRepository") as mock_repo:
        # Address to delete was default
        sample_address.is_default = True
        mock_repo.get_by_id = AsyncMock(return_value=sample_address)
        mock_repo.delete = AsyncMock()
        mock_repo.promote_new_default = AsyncMock()

        await AddressService.delete_address(mock_db, "addr-101", "usr-test-1")

        mock_repo.delete.assert_called_once_with(mock_db, sample_address)
        # Verified: promote_new_default is called
        mock_repo.promote_new_default.assert_called_once_with(mock_db, "usr-test-1")

@pytest.mark.asyncio
async def test_set_default_address_atomic(mock_db, sample_address):
    with patch("app.services.address.AddressRepository") as mock_repo:
        sample_address.is_default = False
        mock_repo.get_by_id = AsyncMock(return_value=sample_address)
        mock_repo.reset_defaults_for_user = AsyncMock()

        res = await AddressService.set_default_address(mock_db, "addr-101", "usr-test-1")

        mock_repo.reset_defaults_for_user.assert_called_once_with(mock_db, "usr-test-1")
        assert sample_address.is_default is True
