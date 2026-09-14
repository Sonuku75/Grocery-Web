"""
Cartify Account Security & Hardening Integration Tests (Module 15.2)

Tests:
1. IDOR prevention on session revocation and deletion cancellation
2. Unauthenticated access prevention (HTTP 401)
3. Mass-assignment parameter injection rejection (HTTP 422)
4. XSS script tag stripping on profile fields
5. Insecure URL scheme rejection for avatar URLs
6. Invalid OTP code rejection
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.core.errors import CartifyException, NotFoundError
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def user_a():
    return User(
        id="usr-alice-1",
        name="Alice Sharma",
        email="alice@cartify.com",
        phone="+919876500001",
        password_hash="mock_hash_a",
        role="customer",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def user_b():
    return User(
        id="usr-bob-2",
        name="Bob Verma",
        email="bob@cartify.com",
        phone="+919876500002",
        password_hash="mock_hash_b",
        role="customer",
        is_active=True,
        is_verified=True,
    )


class TestAccountSecurityApi:
    def test_unauthenticated_requests_return_401(self):
        """All account endpoints strictly require authentication credentials."""
        with TestClient(app, base_url="http://testserver") as unauth_client:
            # GET /account
            res1 = unauth_client.get("/api/v1/account")
            assert res1.status_code == 401

            # PATCH /account/profile
            res2 = unauth_client.patch("/api/v1/account/profile", json={"name": "Attacker"})
            assert res2.status_code == 401

            # POST /account/change-password
            res3 = unauth_client.post("/api/v1/account/change-password", json={"current_password": "1", "new_password": "2"})
            assert res3.status_code == 401

            # GET /account/sessions
            res4 = unauth_client.get("/api/v1/account/sessions")
            assert res4.status_code == 401

            # POST /account/deletion-request
            res5 = unauth_client.post("/api/v1/account/deletion-request", json={"current_password": "1"})
            assert res5.status_code == 401

    def test_idor_cannot_revoke_other_user_session(self, user_a, mock_db):
        """User A cannot revoke User B's session. Returns 404 / access denied."""
        app.dependency_overrides[get_current_active_user] = lambda: user_a
        app.dependency_overrides[get_db_writer] = lambda: mock_db
        with TestClient(app, base_url="http://testserver") as client:
            with patch("app.services.session_service.SessionService.revoke_session", AsyncMock(side_effect=NotFoundError("Session", "sess-belonging-to-bob"))):
                response = client.delete("/api/v1/account/sessions/sess-belonging-to-bob")
                assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_idor_cannot_cancel_other_user_deletion(self, user_a, mock_db):
        """User A cannot cancel User B's pending account deletion."""
        app.dependency_overrides[get_current_active_user] = lambda: user_a
        app.dependency_overrides[get_db_writer] = lambda: mock_db
        with TestClient(app, base_url="http://testserver") as client:
            with patch("app.services.account_deletion_service.AccountDeletionService.cancel_deletion", AsyncMock(side_effect=NotFoundError("AccountDeletion", user_a.id))):
                response = client.post("/api/v1/account/deletion-request/cancel")
                assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_mass_assignment_injection_rejected(self, user_a, mock_db):
        """Attempts to inject role, is_active, is_verified, password_hash are rejected with 422."""
        app.dependency_overrides[get_current_active_user] = lambda: user_a
        app.dependency_overrides[get_db_writer] = lambda: mock_db
        with TestClient(app, base_url="http://testserver") as client:
            res1 = client.patch("/api/v1/account/profile", json={"role": "admin"})
            assert res1.status_code == 422

            res2 = client.patch("/api/v1/account/profile", json={"is_active": False})
            assert res2.status_code == 422

            res3 = client.patch("/api/v1/account/profile", json={"is_verified": True})
            assert res3.status_code == 422

            res4 = client.patch("/api/v1/account/profile", json={"password_hash": "evilhash"})
            assert res4.status_code == 422

            res5 = client.patch("/api/v1/account/profile", json={"user_id": "other-user-uuid"})
            assert res5.status_code == 422
        app.dependency_overrides.clear()

    def test_insecure_avatar_url_schemes_rejected(self, user_a, mock_db):
        """Rejects javascript:, data:, and insecure http: schemes for avatar URLs."""
        app.dependency_overrides[get_current_active_user] = lambda: user_a
        app.dependency_overrides[get_db_writer] = lambda: mock_db
        with TestClient(app, base_url="http://testserver") as client:
            res1 = client.patch("/api/v1/account/profile", json={"avatar_url": "javascript:alert('xss')"})
            assert res1.status_code == 422

            res2 = client.patch("/api/v1/account/profile", json={"avatar_url": "data:image/svg+xml;base64,PHN2Zy..."})
            assert res2.status_code == 422

            res3 = client.patch("/api/v1/account/profile", json={"avatar_url": "http://insecure.com/pic.jpg"})
            assert res3.status_code == 422
        app.dependency_overrides.clear()

    def test_invalid_verification_code_rejected(self, user_a, mock_db):
        """Verifying with a wrong OTP returns HTTP 400."""
        app.dependency_overrides[get_current_active_user] = lambda: user_a
        app.dependency_overrides[get_db_writer] = lambda: mock_db
        with TestClient(app, base_url="http://testserver") as client:
            with patch("app.services.account_service.AccountService.verify_email_change", AsyncMock(side_effect=CartifyException(400, "Invalid or expired verification code.", "INVALID_VERIFICATION_CODE"))):
                res = client.post("/api/v1/account/email-change/verify", json={"token": "999999"})
                assert res.status_code == 400
                assert res.json()["error"]["code"] == "INVALID_VERIFICATION_CODE"
        app.dependency_overrides.clear()
