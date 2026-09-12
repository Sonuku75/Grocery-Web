"""
Unit tests for Cartify AuthService (Module 1)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.errors import CartifyException, UnauthorizedError
from app.core.security import UserRole, get_password_hash
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import AuthService

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_register_success(mock_db):
    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email = AsyncMock(return_value=None)
        mock_repo.get_by_phone = AsyncMock(return_value=None)

        fake_user = User(
            id="usr-123",
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            password_hash="hashed_pw",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_repo.create = AsyncMock(return_value=fake_user)
        mock_repo.create_refresh_token = AsyncMock(return_value=MagicMock())

        payload = RegisterRequest(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            password="SecurePassword123!",
        )

        token_resp, raw_refresh = await AuthService.register(mock_db, payload)

        assert token_resp.user.email == "john@example.com"
        assert token_resp.user.role == UserRole.CUSTOMER
        assert token_resp.access_token is not None
        assert token_resp.refresh_token == raw_refresh
        call_args = mock_repo.create.call_args[0][1]
        assert call_args["role"] == UserRole.CUSTOMER

@pytest.mark.asyncio
async def test_register_duplicate_email(mock_db):
    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email = AsyncMock(return_value=MagicMock(id="existing-1"))
        mock_repo.get_by_phone = AsyncMock(return_value=None)

        payload = RegisterRequest(
            name="John Doe",
            email="existing@example.com",
            password="SecurePassword123!",
        )

        with pytest.raises(CartifyException) as exc_info:
            await AuthService.register(mock_db, payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "EMAIL_ALREADY_EXISTS"

@pytest.mark.asyncio
async def test_register_duplicate_phone(mock_db):
    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email = AsyncMock(return_value=None)
        mock_repo.get_by_phone = AsyncMock(return_value=MagicMock(id="existing-2"))

        payload = RegisterRequest(
            name="John Doe",
            email="unique@example.com",
            phone="+1999999999",
            password="SecurePassword123!",
        )

        with pytest.raises(CartifyException) as exc_info:
            await AuthService.register(mock_db, payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "PHONE_ALREADY_EXISTS"

@pytest.mark.asyncio
async def test_login_success(mock_db):
    pw_hash = get_password_hash("CorrectPassword123!")
    fake_user = User(
        id="usr-login-1",
        name="Alice",
        email="alice@example.com",
        phone="+1234567891",
        password_hash=pw_hash,
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email_or_phone = AsyncMock(return_value=fake_user)
        mock_repo.create_refresh_token = AsyncMock(return_value=MagicMock())

        payload = LoginRequest(email="alice@example.com", password="CorrectPassword123!")
        token_resp, raw_refresh = await AuthService.login(mock_db, payload)

        assert token_resp.user.email == "alice@example.com"
        assert token_resp.access_token is not None
        assert token_resp.refresh_token == raw_refresh

@pytest.mark.asyncio
async def test_login_wrong_password(mock_db):
    pw_hash = get_password_hash("CorrectPassword123!")
    fake_user = User(
        id="usr-login-1",
        name="Alice",
        email="alice@example.com",
        password_hash=pw_hash,
        role=UserRole.CUSTOMER,
        is_active=True,
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email_or_phone = AsyncMock(return_value=fake_user)

        payload = LoginRequest(email="alice@example.com", password="WrongPassword!")
        with pytest.raises(UnauthorizedError) as exc_info:
            await AuthService.login(mock_db, payload)
        assert "Invalid email or password" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_nonexistent_user(mock_db):
    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email_or_phone = AsyncMock(return_value=None)

        payload = LoginRequest(email="nobody@example.com", password="SomePassword123!")
        with pytest.raises(UnauthorizedError) as exc_info:
            await AuthService.login(mock_db, payload)
        assert "Invalid email or password" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_deactivated_user(mock_db):
    pw_hash = get_password_hash("CorrectPassword123!")
    fake_user = User(
        id="usr-deactivated",
        name="Bob",
        email="bob@example.com",
        password_hash=pw_hash,
        role=UserRole.CUSTOMER,
        is_active=False,
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_by_email_or_phone = AsyncMock(return_value=fake_user)

        payload = LoginRequest(email="bob@example.com", password="CorrectPassword123!")
        with pytest.raises(CartifyException) as exc_info:
            await AuthService.login(mock_db, payload)
        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ACCOUNT_DEACTIVATED"

@pytest.mark.asyncio
async def test_refresh_token_rotation(mock_db):
    fake_user = User(
        id="usr-refresh",
        name="Charlie",
        email="charlie@example.com",
        password_hash="hash",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    token_record = RefreshToken(
        id="tok-1",
        user_id="usr-refresh",
        token_hash="some_hash",
        family_id="fam-100",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        revoked_at=None,
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_refresh_token_by_hash = AsyncMock(return_value=token_record)
        mock_repo.get_by_id = AsyncMock(return_value=fake_user)
        mock_repo.revoke_refresh_token = AsyncMock()
        mock_repo.create_refresh_token = AsyncMock(return_value=MagicMock())

        token_resp, new_raw = await AuthService.refresh(mock_db, "valid_raw_token")

        assert token_resp.access_token is not None
        assert token_resp.refresh_token == new_raw
        mock_repo.revoke_refresh_token.assert_called_once_with(mock_db, token_record)

@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(mock_db):
    token_record = RefreshToken(
        id="tok-revoked",
        user_id="usr-refresh",
        token_hash="stolen_hash",
        family_id="fam-compromised",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        revoked_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_refresh_token_by_hash = AsyncMock(return_value=token_record)
        mock_repo.revoke_token_family = AsyncMock()

        with pytest.raises(UnauthorizedError) as exc_info:
            await AuthService.refresh(mock_db, "stolen_raw_token")

        assert "Revoked refresh token presented" in str(exc_info.value.detail)
        mock_repo.revoke_token_family.assert_called_once_with(mock_db, "fam-compromised")

@pytest.mark.asyncio
async def test_forgot_password_safe_enumeration(mock_db):
    with patch("app.services.auth.UserRepository") as mock_repo:
        # 1. User does not exist
        mock_repo.get_by_email = AsyncMock(return_value=None)
        result = await AuthService.forgot_password(mock_db, "nonexistent@example.com")
        assert result is None

        # 2. User exists
        mock_repo.get_by_email = AsyncMock(return_value=User(id="usr-pwd", is_active=True))
        mock_repo.invalidate_existing_reset_tokens = AsyncMock()
        mock_repo.create_password_reset_token = AsyncMock(return_value=MagicMock())
        result2 = await AuthService.forgot_password(mock_db, "existing@example.com")
        assert result2 is not None
        assert isinstance(result2, str)

@pytest.mark.asyncio
async def test_reset_password_success(mock_db):
    user = User(id="usr-pwd-reset", password_hash="old_hash")
    reset_record = PasswordResetToken(
        id="rst-1",
        user_id="usr-pwd-reset",
        token_hash="hash_token",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=None,
    )

    with patch("app.services.auth.UserRepository") as mock_repo:
        mock_repo.get_valid_password_reset_token = AsyncMock(return_value=reset_record)
        mock_repo.get_by_id = AsyncMock(return_value=user)
        mock_repo.mark_password_reset_token_used = AsyncMock()
        mock_repo.revoke_all_user_tokens = AsyncMock()

        await AuthService.reset_password(mock_db, "valid_reset_token", "BrandNewPassword123!")

        mock_repo.mark_password_reset_token_used.assert_called_once_with(mock_db, reset_record)
        mock_repo.revoke_all_user_tokens.assert_called_once_with(mock_db, "usr-pwd-reset")
        assert user.password_hash != "old_hash"
