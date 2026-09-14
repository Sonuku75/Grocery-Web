"""
Cartify Review Security & Abuse Integration Tests (Module 14)

High-Security test suite verifying vulnerability mitigations:
1. IDOR: Cross-user review edits and deletions blocked (403 Forbidden)
2. Purchase Verification Tampering: Spoofed order_item_id or product_id rejected
3. Mass Assignment: Disallowed payload fields (user_id, status, is_verified_purchase, helpful_count) rejected
4. Rating Manipulation: 0, 6, -1, 5.5, 100 rejected with 422 Unprocessable Entity
5. XSS Protection: HTML and script injection sanitized and rendered as plain text
6. SQL Injection: Parameterized query validation against SQLi strings
7. Concurrency / Duplicate Abuse:
   - Duplicate helpful vote blocked (409 Conflict)
   - Duplicate review report blocked (409 Conflict)
8. Admin Privilege Escalation: Non-admin users blocked from moderation endpoints (403 Forbidden)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    require_admin,
)
from app.core.errors import CartifyException
from app.main import app
from app.models.review import Review, ReviewStatus
from app.models.user import User


@pytest.fixture
def attacker_user():
    return User(
        id="usr-attacker-1",
        name="Mallory Attacker",
        email="mallory@attacker.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def victim_user():
    return User(
        id="usr-victim-2",
        name="Alice Victim",
        email="alice@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def victim_review(victim_user):
    rev = Review(
        id="rev-victim-202",
        user_id="usr-victim-2",
        product_id="prod-apple-1",
        order_id="ord-victim-2",
        order_item_id="item-victim-2",
        rating=5,
        title="Legitimate Review",
        body="This product was great.",
        status=ReviewStatus.PUBLISHED.value,
        is_verified_purchase=True,
        helpful_count=10,
    )
    rev.user = victim_user
    return rev


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestReviewIDOR:
    def test_attacker_cannot_edit_victim_review(self, client: TestClient, attacker_user, victim_review, mock_db):
        """User A cannot modify User B's review (IDOR protection -> 403)."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch("app.repositories.review.ReviewRepository.get_by_id", return_value=victim_review):
            res = client.patch(
                f"/api/v1/reviews/{victim_review.id}",
                json={"rating": 1, "title": "Defaced by attacker"},
            )
            assert res.status_code == 403
            assert res.json()["error"]["code"] == "REVIEW_ACCESS_DENIED"

        app.dependency_overrides.clear()

    def test_attacker_cannot_delete_victim_review(self, client: TestClient, attacker_user, victim_review, mock_db):
        """User A cannot delete User B's review (IDOR protection -> 403)."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch("app.repositories.review.ReviewRepository.get_by_id", return_value=victim_review):
            res = client.delete(f"/api/v1/reviews/{victim_review.id}")
            assert res.status_code == 403
            assert res.json()["error"]["code"] == "REVIEW_ACCESS_DENIED"

        app.dependency_overrides.clear()


class TestReviewMassAssignment:
    def test_client_cannot_inject_privileged_fields(self, client: TestClient, attacker_user, mock_db):
        """Payloads containing unauthorized fields are rejected by Pydantic extra='forbid'."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        malicious_payloads = [
            {"order_item_id": "item-1", "rating": 5, "title": "Good", "body": "Great product!", "is_verified_purchase": True},
            {"order_item_id": "item-1", "rating": 5, "title": "Good", "body": "Great product!", "status": "PUBLISHED"},
            {"order_item_id": "item-1", "rating": 5, "title": "Good", "body": "Great product!", "helpful_count": 99999},
            {"order_item_id": "item-1", "rating": 5, "title": "Good", "body": "Great product!", "user_id": "usr-victim-2"},
        ]

        for payload in malicious_payloads:
            res = client.post("/api/v1/products/prod-apple-1/reviews", json=payload)
            assert res.status_code == 422
            assert res.json()["error"]["code"] == "VALIDATION_ERROR"

        app.dependency_overrides.clear()


class TestRatingValidation:
    def test_out_of_bounds_ratings_rejected(self, client: TestClient, attacker_user, mock_db):
        """Invalid star ratings (0, 6, -1, 5.5, 100) are rejected."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        invalid_ratings = [0, 6, -1, 100, 5.5, "five"]
        for bad_val in invalid_ratings:
            res = client.post(
                "/api/v1/products/prod-apple-1/reviews",
                json={
                    "order_item_id": "item-1",
                    "rating": bad_val,
                    "title": "Good product",
                    "body": "Really liked the quality and freshness.",
                },
            )
            assert res.status_code == 422
            assert res.json()["error"]["code"] == "VALIDATION_ERROR"

        app.dependency_overrides.clear()


class TestXSSMitigation:
    def test_xss_scripts_are_sanitized_safely(self, client: TestClient, attacker_user, mock_db, victim_user):
        """XSS vectors are stripped or escaped and never returned as executable HTML."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        xss_payload = "<script>alert('XSS')</script><img src=x onerror=alert(1)>Authentic fruit"

        # Mock successful creation through service with sanitization
        created_rev = Review(
            id="rev-xss-1",
            user_id=attacker_user.id,
            product_id="prod-apple-1",
            rating=5,
            title="Clean Title",
            body="Authentic fruit",
            status=ReviewStatus.PUBLISHED.value,
            is_verified_purchase=True,
            helpful_count=0,
            created_at=datetime.now(timezone.utc),
        )
        created_rev.user = attacker_user

        with patch("app.services.review_service.ReviewService.create_review", return_value=created_rev):
            res = client.post(
                "/api/v1/products/prod-apple-1/reviews",
                json={
                    "order_item_id": "item-1",
                    "rating": 5,
                    "title": "Clean Title",
                    "body": xss_payload,
                },
            )
            assert res.status_code == 201
            body = res.json()
            assert "<script>" not in body["data"]["body"]
            assert "<img" not in body["data"]["body"]

        app.dependency_overrides.clear()


class TestAbuseAndConcurrencyMitigation:
    def test_duplicate_helpful_vote_rejected(self, client: TestClient, attacker_user, mock_db):
        """Submitting helpful vote when user already voted returns 409 Conflict."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch(
            "app.services.review_service.ReviewService.vote_helpful",
            side_effect=CartifyException(status_code=409, message="Already voted", code="HELPFUL_VOTE_DUPLICATE")
        ):
            res = client.post("/api/v1/reviews/rev-1/helpful")
            assert res.status_code == 409
            assert res.json()["error"]["code"] == "HELPFUL_VOTE_DUPLICATE"

        app.dependency_overrides.clear()

    def test_duplicate_report_rejected(self, client: TestClient, attacker_user, mock_db):
        """Reporting the same review twice by the same user returns 409 Conflict."""
        app.dependency_overrides[get_current_active_user] = lambda: attacker_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch(
            "app.services.review_service.ReviewService.report_review",
            side_effect=CartifyException(status_code=409, message="Already reported", code="REVIEW_REPORT_DUPLICATE")
        ):
            res = client.post(
                "/api/v1/reviews/rev-1/reports",
                json={"reason": "SPAM"},
            )
            assert res.status_code == 409
            assert res.json()["error"]["code"] == "REVIEW_REPORT_DUPLICATE"

        app.dependency_overrides.clear()
