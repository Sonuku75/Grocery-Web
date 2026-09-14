"""
Cartify Account & Security API Integration Tests (Module 15.2)

Verifies endpoints under /api/v1/account:
- GET /api/v1/account
- PATCH /api/v1/account/profile
- POST /api/v1/account/email-change
- POST /api/v1/account/email-change/verify
- POST /api/v1/account/phone-change
- POST /api/v1/account/phone-change/verify
- POST /api/v1/account/change-password
- GET /api/v1/account/sessions
- DELETE /api/v1/account/sessions/{session_id}
- POST /api/v1/account/sessions/revoke-others
- POST /api/v1/account/sessions/revoke-all
- GET /api/v1/account/security
- GET /api/v1/account/security/events
- POST /api/v1/account/deletion-request
- POST /api/v1/account/deletion-request/cancel
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.main import app
from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus
from app.models.account_security_event import AccountSecurityEvent
from app.models.user import User
from app.schemas.account import (
    AccountDeletionResponse,
    AccountProfileResponse,
    AccountSecuritySummaryResponse,
    UserSessionResponse,
)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def customer_user():
    now = datetime.now(timezone.utc)
    return User(
        id="usr-cust-100",
        name="Sunita Rao",
        email="sunita@cartify.com",
        phone="+919876543210",
        password_hash="$2b$12$e86g5qD/qJ60c2u8D0J/v.2F7q9zD1L5oK4T2w1N0o9P8m7l6k5j4",
        role="customer",
        avatar_url="https://images.cartify.com/avatar.jpg",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(customer_user, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db
    app.dependency_overrides[get_db_writer] = lambda: mock_db
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAccountApi:
    def test_get_account_overview_success(self, client, customer_user):
        """GET /api/v1/account returns safe profile without secrets."""
        mock_profile = AccountProfileResponse(
            id=customer_user.id,
            name=customer_user.name,
            email=customer_user.email,
            phone=customer_user.phone,
            avatar_url=customer_user.avatar_url,
            date_of_birth=date(1992, 5, 10),
            bio="Fresh organic groceries lover",
            is_verified=True,
            created_at=customer_user.created_at,
            has_pending_deletion=False,
        )

        with patch("app.services.profile_service.ProfileService.get_profile", AsyncMock(return_value=mock_profile)):
            response = client.get("/api/v1/account")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == customer_user.id
            assert data["data"]["name"] == "Sunita Rao"
            assert data["data"]["email"] == "sunita@cartify.com"
            # Crucial privacy assertion: no passwords or tokens in response
            assert "password_hash" not in str(response.json())
            assert "password" not in data["data"]

    def test_patch_account_profile_success(self, client, customer_user):
        """PATCH /api/v1/account/profile updates name and phone safely."""
        mock_updated = AccountProfileResponse(
            id=customer_user.id,
            name="Sunita K. Rao",
            email=customer_user.email,
            phone="+919811122233",
            avatar_url=customer_user.avatar_url,
            is_verified=True,
            created_at=customer_user.created_at,
            has_pending_deletion=False,
        )

        with patch("app.services.profile_service.ProfileService.update_profile", AsyncMock(return_value=mock_updated)):
            response = client.patch(
                "/api/v1/account/profile",
                json={"name": "Sunita K. Rao", "phone": "+919811122233"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "Sunita K. Rao"
            assert data["data"]["phone"] == "+919811122233"

    def test_patch_account_profile_rejects_email_injection(self, client):
        """Direct email changes in PATCH /account/profile are forbidden."""
        response = client.patch(
            "/api/v1/account/profile",
            json={"email": "attacker@cartify.com"},
        )
        assert response.status_code == 422  # Extra field forbidden

    def test_email_change_full_flow(self, client):
        """Initiate email change and verify with code."""
        with patch("app.services.account_service.AccountService.initiate_email_change", AsyncMock(return_value="123456")):
            init_res = client.post(
                "/api/v1/account/email-change",
                json={"new_email": "sunita.new@cartify.com", "current_password": "validpassword123"},
            )
            assert init_res.status_code == 200
            assert "Verification code" in init_res.json()["message"]

        with patch("app.services.account_service.AccountService.verify_email_change", AsyncMock(return_value=True)):
            verify_res = client.post(
                "/api/v1/account/email-change/verify",
                json={"token": "123456"},
            )
            assert verify_res.status_code == 200
            assert verify_res.json()["success"] is True

    def test_phone_change_full_flow(self, client):
        """Initiate phone change and verify with OTP."""
        with patch("app.services.account_service.AccountService.initiate_phone_change", AsyncMock(return_value="654321")):
            init_res = client.post(
                "/api/v1/account/phone-change",
                json={"new_phone": "+919899887766", "current_password": "validpassword123"},
            )
            assert init_res.status_code == 200
            assert "OTP" in init_res.json()["message"]

        with patch("app.services.account_service.AccountService.verify_phone_change", AsyncMock(return_value=True)):
            verify_res = client.post(
                "/api/v1/account/phone-change/verify",
                json={"verification_code": "654321"},
            )
            assert verify_res.status_code == 200
            assert verify_res.json()["success"] is True

    def test_change_password_success(self, client):
        """POST /api/v1/account/change-password changes password and invalidates sessions."""
        with patch("app.services.account_service.AccountService.change_password", AsyncMock(return_value=True)):
            response = client.post(
                "/api/v1/account/change-password",
                json={"current_password": "old_password_123", "new_password": "new_secure_password_456"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "terminated" in data["message"].lower() or "changed" in data["message"].lower()

    def test_change_password_rejects_same_password(self, client):
        """Rejects change password when new password is same as current password."""
        response = client.post(
            "/api/v1/account/change-password",
            json={"current_password": "same_password_123", "new_password": "same_password_123"},
        )
        assert response.status_code == 422  # Pydantic validator rejects identical

    def test_sessions_list_and_revocation(self, client):
        """List active sessions and revoke specific/others/all."""
        now = datetime.now(timezone.utc)
        mock_sessions = [
            UserSessionResponse(
                id="sess-10",
                device_name="Chrome on Windows",
                platform="WEB",
                ip_address="192.168.*.*",
                last_seen_at=now,
                created_at=now,
                expires_at=now,
                is_current=True,
            ),
            UserSessionResponse(
                id="sess-20",
                device_name="Safari on iPhone",
                platform="IOS",
                ip_address="10.0.*.*",
                last_seen_at=now,
                created_at=now,
                expires_at=now,
                is_current=False,
            ),
        ]

        with patch("app.services.session_service.SessionService.get_active_sessions", AsyncMock(return_value=mock_sessions)):
            get_res = client.get("/api/v1/account/sessions")
            assert get_res.status_code == 200
            assert len(get_res.json()["data"]) == 2

        with patch("app.services.session_service.SessionService.revoke_session", AsyncMock(return_value=True)):
            del_res = client.delete("/api/v1/account/sessions/sess-20")
            assert del_res.status_code == 200
            assert del_res.json()["success"] is True

        with patch("app.services.session_service.SessionService.revoke_all_sessions", AsyncMock(return_value=1)):
            others_res = client.post("/api/v1/account/sessions/revoke-others")
            assert others_res.status_code == 200
            assert others_res.json()["data"]["revoked_count"] == 1

        with patch("app.services.session_service.SessionService.revoke_all_sessions", AsyncMock(return_value=2)):
            all_res = client.post("/api/v1/account/sessions/revoke-all")
            assert all_res.status_code == 200
            assert all_res.json()["data"]["revoked_count"] == 2

    def test_get_account_security_summary(self, client):
        """GET /api/v1/account/security returns safe security overview."""
        now = datetime.now(timezone.utc)
        mock_summary = AccountSecuritySummaryResponse(
            email_verified=True,
            phone_verified=True,
            active_sessions=2,
            has_pending_deletion=False,
            last_security_event_at=now,
            password_last_changed_at=now,
        )

        with patch("app.services.account_service.AccountService.get_security_summary", AsyncMock(return_value=mock_summary)):
            response = client.get("/api/v1/account/security")
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["email_verified"] is True
            assert data["active_sessions"] == 2
            assert data["has_pending_deletion"] is False

    def test_list_security_events(self, client, customer_user):
        """GET /api/v1/account/security/events returns sanitized audit events."""
        now = datetime.now(timezone.utc)
        events = [
            AccountSecurityEvent(
                id="evt-1",
                user_id=customer_user.id,
                event_type="LOGIN_SUCCESS",
                ip_address="192.168.1.10",
                user_agent="Test Browser Agent",
                created_at=now,
            )
        ]

        with patch("app.repositories.account_security_event.AccountSecurityEventRepository.list_by_user_id", AsyncMock(return_value=events)):
            response = client.get("/api/v1/account/security/events")
            assert response.status_code == 200
            items = response.json()["data"]
            assert len(items) == 1
            assert items[0]["event_type"] == "LOGIN_SUCCESS"
            assert items[0]["ip_address"] == "192.168.*.*"  # Masked!

    def test_account_deletion_scheduling_and_cancellation(self, client):
        """Schedule deletion with grace period and cancel before completion."""
        now = datetime.now(timezone.utc)
        mock_del_res = AccountDeletionResponse(
            id="del-123",
            status="PENDING",
            requested_at=now,
            scheduled_at=now,
            grace_period_days=30,
        )

        with patch("app.services.account_deletion_service.AccountDeletionService.request_deletion", AsyncMock(return_value=mock_del_res)):
            req_res = client.post(
                "/api/v1/account/deletion-request",
                json={"current_password": "valid_password", "reason": "Not using anymore"},
            )
            assert req_res.status_code == 200
            assert req_res.json()["data"]["status"] == "PENDING"
            assert req_res.json()["data"]["grace_period_days"] == 30

        with patch("app.services.account_deletion_service.AccountDeletionService.cancel_deletion", AsyncMock(return_value=True)):
            cancel_res = client.post("/api/v1/account/deletion-request/cancel")
            assert cancel_res.status_code == 200
            assert cancel_res.json()["success"] is True
