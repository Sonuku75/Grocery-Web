"""
Unit tests for Cartify UserService (Module 1)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException, NotFoundError
from app.core.security import UserRole, get_password_hash
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserUpdateRequest
from app.services.user import UserService

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def sample_user():
    return User(
        id="usr-user-service-1",
        name="Elena Rostova",
        email="elena@example.com",
        phone="+1234567899",
        password_hash=get_password_hash("ElenaPass123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

@pytest.mark.asyncio
async def test_get_profile_success(mock_db, sample_user):
    with patch("app.services.user.UserRepository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=sample_user)
        profile = await UserService.get_profile(mock_db, "usr-user-service-1")

        assert profile.name == "Elena Rostova"
        assert profile.email == "elena@example.com"
        assert profile.role == UserRole.CUSTOMER

@pytest.mark.asyncio
async def test_get_profile_not_found(mock_db):
    with patch("app.services.user.UserRepository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await UserService.get_profile(mock_db, "nonexistent")

@pytest.mark.asyncio
async def test_update_profile_allowed_fields(mock_db, sample_user):
    with patch("app.services.user.UserRepository") as mock_repo:
        mock_repo.get_by_phone = AsyncMock(return_value=None)

        async def fake_update(db, user, updates):
            for k, v in updates.items():
                setattr(user, k, v)
            return user

        mock_repo.update = AsyncMock(side_effect=fake_update)

        update_payload = UserUpdateRequest(
            name="Elena Updated",
            phone="+1999888777",
            avatar_url="https://example.com/avatar.jpg",
        )

        res = await UserService.update_profile(mock_db, sample_user, update_payload)
        assert res.name == "Elena Updated"
        assert res.phone == "+1999888777"
        assert res.avatar_url == "https://example.com/avatar.jpg"
        assert res.role == UserRole.CUSTOMER

@pytest.mark.asyncio
async def test_change_password_success(mock_db, sample_user):
    with patch("app.services.user.UserRepository") as mock_repo:
        mock_repo.revoke_all_user_tokens = AsyncMock()

        req = ChangePasswordRequest(
            current_password="ElenaPass123!",
            new_password="NewElenaPass456!",
        )
        await UserService.change_password(mock_db, sample_user, req)

        mock_repo.revoke_all_user_tokens.assert_called_once_with(mock_db, sample_user.id)

@pytest.mark.asyncio
async def test_change_password_wrong_current(mock_db, sample_user):
    req = ChangePasswordRequest(
        current_password="WrongCurrentPassword!",
        new_password="NewElenaPass456!",
    )
    with pytest.raises(CartifyException) as exc_info:
        await UserService.change_password(mock_db, sample_user, req)
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "INVALID_CURRENT_PASSWORD"
