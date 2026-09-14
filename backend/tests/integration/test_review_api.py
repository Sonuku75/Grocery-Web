"""
Cartify Review API Integration Tests (Module 14)

Covers customer and admin review endpoints:
1. GET /api/v1/products/{product_id}/reviews (Public, cursor pagination, filtering, sorting)
2. GET /api/v1/products/{product_id}/review-summary (Public star distribution & average)
3. GET /api/v1/products/{product_id}/eligibility (Authenticated customer purchase check)
4. POST /api/v1/products/{product_id}/reviews (Authenticated, purchase-verified review creation)
5. GET /api/v1/reviews/{review_id} (Public access to published review)
6. PATCH /api/v1/reviews/{review_id} (Owner edit)
7. DELETE /api/v1/reviews/{review_id} (Owner soft delete)
8. POST /api/v1/reviews/{review_id}/helpful (Helpful vote)
9. DELETE /api/v1/reviews/{review_id}/helpful (Remove vote)
10. POST /api/v1/reviews/{review_id}/reports (Abuse reporting)
11. GET /api/v1/users/me/reviews (Customer review history)
12. Admin review endpoints authorization and status moderation
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    get_optional_user,
    require_admin,
)
from app.main import app
from app.models.order import OrderItem
from app.models.review import Review, ReviewStatus
from app.models.user import User


@pytest.fixture
def customer_user():
    return User(
        id="usr-cust-1",
        name="Deepak Kumar",
        email="deepak@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def other_customer_user():
    return User(
        id="usr-cust-2",
        name="Sneha Roy",
        email="sneha@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-1",
        name="Admin User",
        email="admin@cartify.com",
        role="admin",
        is_active=True,
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_review(customer_user):
    rev = Review(
        id="rev-101",
        user_id="usr-cust-1",
        product_id="prod-101",
        order_id="ord-101",
        order_item_id="item-101",
        rating=5,
        title="Super fresh apples",
        body="Crisp, sweet, and delivered quickly.",
        status=ReviewStatus.PUBLISHED.value,
        is_verified_purchase=True,
        helpful_count=3,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    rev.user = customer_user
    return rev


class TestReviewPublicAPI:
    def test_list_product_reviews_public(self, client: TestClient, mock_db, sample_review):
        """Public users can view published reviews without authentication."""
        app.dependency_overrides[get_db_reader] = lambda: mock_db
        app.dependency_overrides[get_optional_user] = lambda: None

        mock_result = {
            "items": [
                {
                    "id": "rev-101",
                    "rating": 5,
                    "title": "Super fresh apples",
                    "body": "Crisp, sweet, and delivered quickly.",
                    "status": "PUBLISHED",
                    "is_verified_purchase": True,
                    "helpful_count": 3,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "reviewer_name": "Deepak K.",
                    "user_voted_helpful": False,
                    "is_own_review": False,
                }
            ],
            "next_cursor": None,
            "total": 1,
            "summary": {
                "average_rating": 5.0,
                "total_reviews": 1,
                "distribution": {"5": 1, "4": 0, "3": 0, "2": 0, "1": 0},
            },
        }

        with patch("app.services.review_service.ReviewService.list_product_reviews", return_value=mock_result):
            res = client.get("/api/v1/products/prod-101/reviews")
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert len(body["data"]["items"]) == 1
            assert body["data"]["items"][0]["reviewer_name"] == "Deepak K."
            # Crucial privacy assertion: No email or internal user_id in response
            assert "deepak@cartify.com" not in str(body)

        app.dependency_overrides.clear()

    def test_get_product_review_summary_public(self, client: TestClient, mock_db):
        """Public callers can retrieve star ratings and distributions."""
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        mock_summary = {
            "average_rating": 4.6,
            "total_reviews": 12,
            "distribution": {"5": 8, "4": 3, "3": 1, "2": 0, "1": 0},
        }

        with patch("app.services.review_aggregation_service.ReviewAggregationService.get_summary_for_product", return_value=mock_summary):
            res = client.get("/api/v1/products/prod-101/review-summary")
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert body["data"]["average_rating"] == 4.6
            assert body["data"]["total_reviews"] == 12

        app.dependency_overrides.clear()


class TestCustomerReviewOperations:
    def test_create_review_unauthenticated_returns_401(self, client: TestClient):
        """Unauthenticated review creation attempt is rejected."""
        res = client.post(
            "/api/v1/products/prod-101/reviews",
            json={
                "order_item_id": "item-101",
                "rating": 5,
                "title": "Great quality",
                "body": "Really liked the quality and freshness.",
            },
        )
        assert res.status_code == 401

    def test_create_review_authenticated_success(self, client: TestClient, customer_user, mock_db, sample_review):
        """Authenticated customer with valid purchase can submit review."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch("app.services.review_service.ReviewService.create_review", return_value=sample_review):
            res = client.post(
                "/api/v1/products/prod-101/reviews",
                json={
                    "order_item_id": "item-101",
                    "rating": 5,
                    "title": "Super fresh apples",
                    "body": "Crisp, sweet, and delivered quickly.",
                },
            )
            assert res.status_code == 201
            body = res.json()
            assert body["success"] is True
            assert body["data"]["rating"] == 5
            assert body["data"]["is_verified_purchase"] is True

        app.dependency_overrides.clear()

    def test_check_eligibility_authenticated(self, client: TestClient, customer_user, mock_db):
        """Authenticated customer checks purchase review eligibility."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        with patch("app.services.review_eligibility_service.ReviewEligibilityService.can_review_product", return_value=(True, None, [])):
            res = client.get("/api/v1/products/prod-101/eligibility")
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert body["data"]["can_review"] is True

        app.dependency_overrides.clear()

    def test_update_review_authenticated(self, client: TestClient, customer_user, mock_db, sample_review):
        """Author can update review rating, title, or body."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        updated_rev = sample_review
        updated_rev.rating = 4
        updated_rev.title = "Updated title"

        with patch("app.services.review_service.ReviewService.update_review", return_value=updated_rev):
            res = client.patch(
                "/api/v1/reviews/rev-101",
                json={"rating": 4, "title": "Updated title"},
            )
            assert res.status_code == 200
            body = res.json()
            assert body["data"]["rating"] == 4
            assert body["data"]["title"] == "Updated title"

        app.dependency_overrides.clear()

    def test_delete_review_authenticated(self, client: TestClient, customer_user, mock_db):
        """Author can soft delete their own review."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch("app.services.review_service.ReviewService.delete_review", return_value=None):
            res = client.delete("/api/v1/reviews/rev-101")
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert body["data"]["deleted"] is True

        app.dependency_overrides.clear()

    def test_vote_helpful_and_remove(self, client: TestClient, customer_user, mock_db):
        """Customer can mark review as helpful and remove vote."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        with patch("app.services.review_service.ReviewService.vote_helpful", return_value={"review_id": "rev-101", "helpful_count": 4, "user_voted_helpful": True}):
            res = client.post("/api/v1/reviews/rev-101/helpful")
            assert res.status_code == 200
            body = res.json()
            assert body["data"]["helpful_count"] == 4
            assert body["data"]["user_voted_helpful"] is True

        with patch("app.services.review_service.ReviewService.remove_helpful_vote", return_value={"review_id": "rev-101", "helpful_count": 3, "user_voted_helpful": False}):
            res = client.delete("/api/v1/reviews/rev-101/helpful")
            assert res.status_code == 200
            body = res.json()
            assert body["data"]["helpful_count"] == 3
            assert body["data"]["user_voted_helpful"] is False

        app.dependency_overrides.clear()

    def test_report_review(self, client: TestClient, customer_user, mock_db):
        """Customer can submit moderation report for an offensive or spam review."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        mock_report = AsyncMock()
        mock_report.id = "rep-1"
        mock_report.review_id = "rev-101"
        mock_report.reason = "SPAM"
        mock_report.description = "Suspicious promotional link"
        mock_report.status = "PENDING"
        mock_report.created_at = datetime.now(timezone.utc)

        with patch("app.services.review_service.ReviewService.report_review", return_value=mock_report):
            res = client.post(
                "/api/v1/reviews/rev-101/reports",
                json={"reason": "SPAM", "description": "Suspicious promotional link"},
            )
            assert res.status_code == 201
            body = res.json()
            assert body["success"] is True
            assert body["data"]["reason"] == "SPAM"

        app.dependency_overrides.clear()


class TestAdminReviewModerationAPI:
    def test_admin_list_reviews_forbidden_for_regular_user(self, client: TestClient, customer_user):
        """Non-admin customer receives 403 Forbidden on admin review queue."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user

        res = client.get("/api/v1/admin/reviews")
        assert res.status_code == 403

        app.dependency_overrides.clear()

    def test_admin_list_reviews_allowed_for_admin(self, client: TestClient, admin_user, mock_db):
        """Admin user can list reviews across all statuses."""
        app.dependency_overrides[get_current_active_user] = lambda: admin_user
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        with patch("app.repositories.review.ReviewRepository.list_admin_reviews", return_value=([], 0)):
            res = client.get("/api/v1/admin/reviews")
            assert res.status_code == 200
            assert res.json()["success"] is True

        app.dependency_overrides.clear()

    def test_admin_moderate_status_transition(self, client: TestClient, admin_user, mock_db, sample_review):
        """Admin can transition review status via PATCH /admin/reviews/{id}/status."""
        app.dependency_overrides[get_current_active_user] = lambda: admin_user
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        sample_review.status = ReviewStatus.HIDDEN.value

        with patch("app.repositories.review.ReviewRepository.get_by_id", return_value=sample_review), \
             patch("app.services.review_moderation_service.ReviewModerationService.transition_status", return_value=sample_review):
            res = client.patch(
                "/api/v1/admin/reviews/rev-101/status",
                json={"status": "HIDDEN", "reason": "Violates community policy"},
            )
            assert res.status_code == 200
            body = res.json()
            assert body["data"]["status"] == "HIDDEN"

        app.dependency_overrides.clear()
