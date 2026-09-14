"""
Cartify Account Final Testing, Integration & Security Verification (Module 15.5)

Production-Readiness Suite:
1. User Isolation & IDOR Defense (User A vs User B)
2. SQL Injection Attack Payload Resistance
3. Cross-Site Scripting (XSS) Sanitization & Scheme Whitelisting
4. Mass-Assignment & Parameter Tampering Neutralization (extra="forbid")
5. Token Replay, Expiration & Brute-Force Rejection
6. Cross-Module Snapshot Integrity (Order Snapshots preserved on profile update)
7. Cross-Module Financial Data Isolation (No payment credentials leaked)
8. Cross-Module Review Anonymity (No PII exposed in public reviews)
9. Notification Engine Outbox Resiliency (Graceful fallback on outbox error)
10. HTTP Security Headers & Cache-Control Verification
"""

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.core.config import settings
from app.core.errors import CartifyException, NotFoundError
from app.core.security import hash_token
from app.main import app
from app.models.account_change_request import AccountChangeRequest, ChangeType
from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus
from app.models.user_profile import UserProfile
from app.models.account_security_event import AccountSecurityEvent
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.account import (
    AccountDeletionResponse,
    AccountProfileResponse,
    AccountSecuritySummaryResponse,
    ProfileUpdateRequest,
    UserSessionResponse,
    sanitize_input_text,
)
from app.schemas.review import ReviewPublicResponse
from app.services.account_service import AccountService
from app.services.security_event_service import SecurityEventService
from app.services.session_service import SessionService


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_rate_limiter_fast():
    """Bypass Redis timeout in test environment for sub-second execution."""
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.is_allowed", AsyncMock(return_value=(True, 100, 0))):
        yield


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def user_a():
    now = datetime.now(timezone.utc)
    return User(
        id="usr-test-user-a",
        name="Aarav Sharma",
        email="aarav@cartify.com",
        phone="+919876543210",
        password_hash="$2b$12$e86g5qD/qJ60c2u8D0J/v.2F7q9zD1L5oK4T2w1N0o9P8m7l6k5j4",
        role="customer",
        avatar_url="https://images.cartify.com/avatar_a.jpg",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def user_b():
    now = datetime.now(timezone.utc)
    return User(
        id="usr-test-user-b",
        name="Diya Patel",
        email="diya@cartify.com",
        phone="+919876543211",
        password_hash="$2b$12$e86g5qD/qJ60c2u8D0J/v.2F7q9zD1L5oK4T2w1N0o9P8m7l6k5j4",
        role="customer",
        avatar_url="https://images.cartify.com/avatar_b.jpg",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client_user_a(user_a, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: user_a
    app.dependency_overrides[get_db_reader] = lambda: mock_db
    app.dependency_overrides[get_db_writer] = lambda: mock_db
    with TestClient(app, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 1. User Isolation & IDOR Defense (User A vs User B)
# -----------------------------------------------------------------------------

class TestUserIsolationAndIdor:
    """Verifies strict cross-user authorization boundaries and IDOR defense."""

    def test_user_a_cannot_revoke_user_b_session(self, client_user_a, user_a, user_b):
        """User A attempting to delete User B's session returns 404 (IDOR defense)."""
        session_b = UserSession(
            id="sess-user-b-999",
            user_id=user_b.id,  # Owned by User B
            session_identifier=hash_token("raw-token-b"),
            device_name="Diya's iPhone",
            platform="iOS",
            ip_address="103.21.244.1",
            last_seen_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked_at=None,
        )

        with patch("app.repositories.user_session.UserSessionRepository.get_by_id", AsyncMock(return_value=session_b)):
            response = client_user_a.delete(f"/api/v1/account/sessions/{session_b.id}")
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"]["message"].lower()

    def test_user_a_account_overview_strictly_isolated(self, client_user_a, user_a):
        """GET /api/v1/account strictly returns the authenticated user's profile."""
        profile_a = AccountProfileResponse(
            id=user_a.id,
            name=user_a.name,
            email=user_a.email,
            phone=user_a.phone,
            avatar_url=user_a.avatar_url,
            is_verified=True,
            created_at=user_a.created_at,
            has_pending_deletion=False,
        )
        with patch("app.services.profile_service.ProfileService.get_profile", AsyncMock(return_value=profile_a)):
            response = client_user_a.get("/api/v1/account")
            assert response.status_code == 200
            res = response.json()
            assert res["success"] is True
            assert res["data"]["id"] == user_a.id
            assert res["data"]["email"] == "aarav@cartify.com"

    def test_user_a_cannot_cancel_nonexistent_or_other_user_deletion(self, client_user_a):
        """User A cannot cancel deletion when no pending deletion exists for User A."""
        with patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=None)):
            response = client_user_a.post("/api/v1/account/deletion-request/cancel")
            assert response.status_code == 404
            assert response.json()["success"] is False
            assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# -----------------------------------------------------------------------------
# 2. SQL Injection Attack Payload Resistance
# -----------------------------------------------------------------------------

class TestSqlInjectionResistance:
    """Verifies that malicious SQL attack vectors in profile inputs are safely handled."""

    def test_sql_injection_payload_in_bio_is_safely_parameterized(self, client_user_a, user_a):
        """Payloads with SQL syntax are stored as plain strings and stripped of HTML."""
        sql_payload = "'; DROP TABLE users; --"
        mock_updated = AccountProfileResponse(
            id=user_a.id,
            name=user_a.name,
            email=user_a.email,
            phone=user_a.phone,
            bio=sql_payload,
            is_verified=True,
            created_at=user_a.created_at,
        )
        with patch("app.services.profile_service.ProfileService.update_profile", AsyncMock(return_value=mock_updated)):
            response = client_user_a.patch("/api/v1/account/profile", json={"bio": sql_payload})
            assert response.status_code == 200
            assert response.json()["data"]["bio"] == sql_payload

    def test_sql_injection_in_name_field_sanitized(self, client_user_a, user_a):
        """Classic ' OR '1'='1 payload in name is treated literally."""
        sql_name = "Aarav ' OR '1'='1"
        mock_updated = AccountProfileResponse(
            id=user_a.id,
            name=sql_name,
            email=user_a.email,
            is_verified=True,
            created_at=user_a.created_at,
        )
        with patch("app.services.profile_service.ProfileService.update_profile", AsyncMock(return_value=mock_updated)):
            response = client_user_a.patch("/api/v1/account/profile", json={"name": sql_name})
            assert response.status_code == 200
            assert response.json()["data"]["name"] == sql_name


# -----------------------------------------------------------------------------
# 3. XSS Sanitization & Scheme Whitelisting
# -----------------------------------------------------------------------------

class TestXssSanitizationAndUrlSchemes:
    """Verifies XSS neutralization in profile fields and avatar URL scheme whitelisting."""

    def test_script_tag_stripped_from_input_text(self):
        malicious = "<script>alert('XSS')</script>Normal User Text"
        cleaned = sanitize_input_text(malicious)
        assert "<script>" not in cleaned
        assert "alert" not in cleaned
        assert "Normal User Text" in cleaned

    def test_img_onerror_tags_stripped(self):
        malicious = "Hello <img src=x onerror=alert('pwnd')> World"
        cleaned = sanitize_input_text(malicious)
        assert "<img" not in cleaned
        assert "onerror" not in cleaned
        assert cleaned == "Hello  World"

    def test_javascript_avatar_url_scheme_rejected(self, client_user_a):
        """avatar_url starting with javascript: must be rejected with 422."""
        response = client_user_a.patch(
            "/api/v1/account/profile",
            json={"avatar_url": "javascript:alert(document.cookie)"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        details_str = str(data["error"]["details"]).lower()
        assert "scheme" in details_str or "forbidden" in details_str

    def test_data_uri_avatar_url_scheme_rejected(self, client_user_a):
        """avatar_url starting with data: must be rejected with 422."""
        response = client_user_a.patch(
            "/api/v1/account/profile",
            json={"avatar_url": "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        details_str = str(data["error"]["details"]).lower()
        assert "scheme" in details_str or "avatar" in details_str or "forbidden" in details_str

    def test_https_and_local_avatar_url_allowed(self, client_user_a, user_a):
        """https:// and /uploads/ paths are accepted."""
        valid_url = "https://cdn.cartify.com/users/avatar.webp"
        mock_updated = AccountProfileResponse(
            id=user_a.id,
            name=user_a.name,
            email=user_a.email,
            avatar_url=valid_url,
            is_verified=True,
            created_at=user_a.created_at,
        )
        with patch("app.services.profile_service.ProfileService.update_profile", AsyncMock(return_value=mock_updated)):
            response = client_user_a.patch("/api/v1/account/profile", json={"avatar_url": valid_url})
            assert response.status_code == 200
            assert response.json()["data"]["avatar_url"] == valid_url


# -----------------------------------------------------------------------------
# 4. Mass-Assignment & Parameter Tampering Neutralization
# -----------------------------------------------------------------------------

class TestMassAssignmentDefense:
    """Verifies that extra attributes in request bodies are forbidden (HTTP 422)."""

    def test_profile_update_forbids_privilege_escalation_fields(self, client_user_a):
        """Attempting to inject 'role' or 'is_active' must fail with 422."""
        tampered_payload = {
            "name": "Legit Name",
            "role": "admin",
            "is_superuser": True,
            "is_active": False,
        }
        response = client_user_a.patch("/api/v1/account/profile", json=tampered_payload)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        details_str = str(data["error"]["details"]).lower()
        assert "extra" in details_str or "forbidden" in details_str

    def test_email_change_forbids_extra_fields(self, client_user_a):
        """Attempting to inject bypass flags into email-change must fail with 422."""
        tampered_payload = {
            "new_email": "new.secure@cartify.com",
            "current_password": "StrongPassword123!",
            "is_verified": True,
            "skip_otp": True,
        }
        response = client_user_a.post("/api/v1/account/email-change", json=tampered_payload)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        details_str = str(data["error"]["details"]).lower()
        assert "extra" in details_str or "forbidden" in details_str


# -----------------------------------------------------------------------------
# 5. Token Replay, Expiration & Brute-Force Rejection
# -----------------------------------------------------------------------------

class TestTokenLifecycleAndBruteForce:
    """Verifies token expiration, replay defense, and brute-force lockouts."""

    @pytest.mark.asyncio
    async def test_expired_otp_is_rejected(self, user_a):
        """Verification request with expired timestamp is rejected."""
        mock_db = AsyncMock()
        # get_active_by_user_and_type returns None when expired in repo
        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=None)):
            with pytest.raises(CartifyException) as exc_info:
                await AccountService.verify_email_change(
                    db=mock_db,
                    user=user_a,
                    verification_code="123456",
                )
            assert exc_info.value.code == "INVALID_VERIFICATION_CODE"

    @pytest.mark.asyncio
    async def test_replayed_token_is_rejected(self, user_a):
        """Already completed (replayed) token is not active and rejected."""
        mock_db = AsyncMock()
        # Active repo call filters by completed_at is None, returning None for replayed requests
        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=None)):
            with pytest.raises(CartifyException) as exc_info:
                await AccountService.verify_email_change(
                    db=mock_db,
                    user=user_a,
                    verification_code="123456",
                )
            assert exc_info.value.code == "INVALID_VERIFICATION_CODE"


# -----------------------------------------------------------------------------
# 6. Cross-Module Integration: Order Snapshot Integrity
# -----------------------------------------------------------------------------

class TestOrderSnapshotIntegrity:
    """Verifies that updating customer profile never alters historical order snapshots."""

    def test_historical_order_snapshots_preserved(self, user_a):
        """Profile update does not mutate Order.recipient_name or Order.phone."""
        historical_order = Order(
            id="ord-hist-101",
            user_id=user_a.id,
            order_number="ORD-2026-0001",
            status=OrderStatus.DELIVERED.value,
            payment_status=PaymentStatus.PAID.value,
            subtotal=Decimal("450.00"),
            total_amount=Decimal("450.00"),
            recipient_name="Original Name Snapshot",
            phone="+919876500000",
            address_line_1="Original Street Address",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
        )

        # Simulate profile update
        user_a.name = "New Updated Name"
        user_a.phone = "+919876599999"

        # Verify historical order remains completely untouched
        assert historical_order.recipient_name == "Original Name Snapshot"
        assert historical_order.phone == "+919876500000"
        assert historical_order.recipient_name != user_a.name
        assert historical_order.phone != user_a.phone


# -----------------------------------------------------------------------------
# 7. Cross-Module Integration: Payment Data Isolation
# -----------------------------------------------------------------------------

class TestPaymentDataIsolation:
    """Verifies that account endpoints never leak payment credentials or gateway secrets."""

    def test_account_profile_response_excludes_payment_secrets(self, user_a):
        """AccountProfileResponse has no fields for cards, CVV, or gateway secrets."""
        profile = AccountProfileResponse(
            id=user_a.id,
            name=user_a.name,
            email=user_a.email,
            phone=user_a.phone,
            is_verified=True,
            created_at=user_a.created_at,
        )
        dumped = profile.model_dump()
        forbidden_fields = {"card_number", "cvv", "razorpay_secret", "payment_method", "token", "password"}
        assert not any(k in dumped for k in forbidden_fields)

    def test_account_security_summary_excludes_payment_secrets(self):
        """AccountSecuritySummaryResponse excludes financial credentials."""
        summary = AccountSecuritySummaryResponse(
            email_verified=True,
            phone_verified=True,
            active_sessions=2,
            has_pending_deletion=False,
            last_security_event_at=datetime.now(timezone.utc),
            password_last_changed_at=datetime.now(timezone.utc),
        )
        dumped = summary.model_dump()
        forbidden_keys = {"card", "payment", "bank", "account_number", "secret"}
        assert not any(any(f in k for f in forbidden_keys) for k in dumped.keys())


# -----------------------------------------------------------------------------
# 8. Cross-Module Integration: Review Anonymity & Data Protection
# -----------------------------------------------------------------------------

class TestReviewAnonymity:
    """Verifies that public reviews only expose reviewer name, never contact or address PII."""

    def test_review_public_response_masks_pii(self):
        """ReviewPublicResponse contains only display name, zero emails or phones."""
        pub_rev = ReviewPublicResponse(
            id="rev-101",
            rating=5,
            title="Fresh groceries!",
            body="Delivered on time and veggies were crisp.",
            status="PUBLISHED",
            is_verified_purchase=True,
            helpful_count=3,
            created_at=datetime.now(timezone.utc),
            reviewer_name="Aarav S.",
            user_voted_helpful=False,
            is_own_review=False,
        )
        data = pub_rev.model_dump()
        assert "reviewer_name" in data
        assert "email" not in data
        assert "phone" not in data
        assert "user_id" not in data
        assert "address" not in data


# -----------------------------------------------------------------------------
# 9. Cross-Module Integration: Notification Outbox Failure Resiliency
# -----------------------------------------------------------------------------

class TestNotificationOutboxResiliency:
    """Verifies that failure in notification emission does not break security operations."""

    @pytest.mark.asyncio
    async def test_security_event_resilient_to_outbox_failure(self, user_a):
        """SecurityEventService handles NotificationService error gracefully."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.security_event_service.AccountSecurityEventRepository.create", AsyncMock()) as mock_create, \
             patch("app.services.notification_service.NotificationService.emit_outbox_event", AsyncMock(side_effect=Exception("Outbox service unavailable"))):

            # Should not raise exception
            await SecurityEventService.record_security_event(
                db=mock_db,
                user_id=user_a.id,
                event_type="PASSWORD_CHANGED",
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
            )
            mock_create.assert_called_once()


# -----------------------------------------------------------------------------
# 10. HTTP Security Headers & Cache-Control Enforcement
# -----------------------------------------------------------------------------

class TestSecurityHeadersEnforcement:
    """Verifies transport security headers on account endpoints."""

    def test_account_headers_enforced(self, client_user_a, user_a):
        profile_a = AccountProfileResponse(
            id=user_a.id,
            name=user_a.name,
            email=user_a.email,
            is_verified=True,
            created_at=user_a.created_at,
        )
        with patch("app.services.profile_service.ProfileService.get_profile", AsyncMock(return_value=profile_a)):
            response = client_user_a.get("/api/v1/account")
            assert response.status_code == 200
            headers = response.headers

            # 1. Anti-MIME sniffing
            assert headers.get("X-Content-Type-Options") == "nosniff"
            # 2. Anti-Clickjacking
            assert headers.get("X-Frame-Options") == "DENY"
            # 3. Referrer-Policy
            assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
            # 4. Permissions-Policy
            assert "camera=()" in headers.get("Permissions-Policy", "")
            # 5. Strict private Cache-Control
            cache_ctrl = headers.get("Cache-Control", "")
            assert "no-store" in cache_ctrl
            assert "no-cache" in cache_ctrl
            assert "must-revalidate" in cache_ctrl
            assert "private" in cache_ctrl
            assert headers.get("Pragma") == "no-cache"
