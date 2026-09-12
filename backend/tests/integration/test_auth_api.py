"""
Integration tests for Cartify Auth and User Endpoints (Module 1)
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db_reader, get_db_writer
from app.core.security import UserRole, create_access_token
from app.main import app
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def test_client(mock_session):
    app.dependency_overrides[get_db_writer] = lambda: mock_session
    app.dependency_overrides[get_db_reader] = lambda: mock_session
    with TestClient(app, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

def test_register_endpoint_success(test_client):
    fake_user_resp = UserResponse(
        id="usr-test-1",
        name="Test User",
        email="test@cartify.com",
        phone="+1234567890",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=False,
        created_at="2026-09-11T12:00:00Z",
        updated_at="2026-09-11T12:00:00Z",
    )
    fake_token_resp = TokenResponse(
        access_token="mock_access_token_123",
        refresh_token="mock_refresh_token_456",
        token_type="bearer",
        user=fake_user_resp,
    )

    with patch("app.api.v1.endpoints.auth.AuthService.register", new_callable=AsyncMock) as mock_reg:
        mock_reg.return_value = (fake_token_resp, "mock_raw_refresh_token_789")

        res = test_client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@cartify.com",
                "phone": "+1234567890",
                "password": "SecurePassword123!",
            },
        )

        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "mock_access_token_123"
        assert data["data"]["user"]["role"] == UserRole.CUSTOMER
        # Check HttpOnly cookie
        assert "cartify_refresh_token" in res.cookies

def test_login_endpoint_success(test_client):
    fake_user_resp = UserResponse(
        id="usr-login-1",
        name="Login User",
        email="login@cartify.com",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at="2026-09-11T12:00:00Z",
        updated_at="2026-09-11T12:00:00Z",
    )
    fake_token_resp = TokenResponse(
        access_token="valid_access_token",
        refresh_token="valid_refresh_token",
        token_type="bearer",
        user=fake_user_resp,
    )

    with patch("app.api.v1.endpoints.auth.AuthService.login", new_callable=AsyncMock) as mock_login:
        mock_login.return_value = (fake_token_resp, "raw_cookie_token")

        res = test_client.post(
            "/api/v1/auth/login",
            json={"email": "login@cartify.com", "password": "Password123!"},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "valid_access_token"
        assert "cartify_refresh_token" in res.cookies

def test_refresh_endpoint_success(test_client):
    fake_user_resp = UserResponse(
        id="usr-refresh-1",
        name="Refresh User",
        email="refresh@cartify.com",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at="2026-09-11T12:00:00Z",
        updated_at="2026-09-11T12:00:00Z",
    )
    fake_token_resp = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        user=fake_user_resp,
    )

    with patch("app.api.v1.endpoints.auth.AuthService.refresh", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = (fake_token_resp, "new_cookie_refresh")

        # Test refresh via request body
        res = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "client_refresh_token"},
        )

        assert res.status_code == 200
        assert res.json()["data"]["access_token"] == "new_access_token"
        assert "cartify_refresh_token" in res.cookies

def test_logout_endpoint(test_client):
    with patch("app.api.v1.endpoints.auth.AuthService.logout", new_callable=AsyncMock) as mock_logout:
        res = test_client.post(
            "/api/v1/auth/logout",
            cookies={"cartify_refresh_token": "active_token"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_logout.assert_called_once()

def test_forgot_password_endpoint(test_client):
    with patch("app.api.v1.endpoints.auth.AuthService.forgot_password", new_callable=AsyncMock):
        res = test_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "anyone@cartify.com"},
        )
        assert res.status_code == 200
        assert "password reset link has been sent" in res.json()["message"]

def test_reset_password_endpoint(test_client):
    with patch("app.api.v1.endpoints.auth.AuthService.reset_password", new_callable=AsyncMock):
        res = test_client.post(
            "/api/v1/auth/reset-password",
            json={"token": "valid_token_abc", "new_password": "NewSecurePassword123!"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

def test_get_profile_unauthorized(test_client):
    res = test_client.get("/api/v1/users/me")
    assert res.status_code == 401

def test_get_profile_authorized(test_client):
    from datetime import datetime, timezone
    from app.api.deps import get_current_active_user

    fake_user = User(
        id="usr-test-me",
        name="Current User",
        email="me@cartify.com",
        phone="+1234567890",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_user

    try:
        with patch("app.services.user.UserService.get_profile", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = UserResponse.model_validate(fake_user)
            res = test_client.get(
                "/api/v1/users/me",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert res.status_code == 200
            assert res.json()["data"]["email"] == "me@cartify.com"
    finally:
        del app.dependency_overrides[get_current_active_user]

def test_patch_profile_endpoint(test_client):
    from datetime import datetime, timezone
    from app.api.deps import get_current_active_user

    fake_user = User(
        id="usr-patch-me",
        name="Original Name",
        email="patch@cartify.com",
        phone="+1234567890",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_user

    try:
        with patch("app.services.user.UserService.update_profile", new_callable=AsyncMock) as mock_update:
            updated_user = User(
                id="usr-patch-me",
                name="Updated Name",
                email="patch@cartify.com",
                phone="+1999888777",
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_update.return_value = UserResponse.model_validate(updated_user)

            res = test_client.patch(
                "/api/v1/users/me",
                headers={"Authorization": "Bearer valid_token"},
                json={"name": "Updated Name", "phone": "+1999888777"},
            )
            assert res.status_code == 200
            assert res.json()["data"]["name"] == "Updated Name"
    finally:
        del app.dependency_overrides[get_current_active_user]

def test_change_password_endpoint(test_client):
    from datetime import datetime, timezone
    from app.api.deps import get_current_active_user

    fake_user = User(
        id="usr-pwd-change",
        name="Pwd User",
        email="pwd@cartify.com",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_user

    try:
        with patch("app.services.user.UserService.change_password", new_callable=AsyncMock):
            res = test_client.post(
                "/api/v1/users/me/change-password",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "current_password": "OldPassword123!",
                    "new_password": "NewPassword456!",
                },
            )
            assert res.status_code == 200
            assert res.json()["success"] is True
    finally:
        del app.dependency_overrides[get_current_active_user]

