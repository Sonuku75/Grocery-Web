"""
Cartify Review Schemas (Module 14)

Pydantic validation models for customer reviews, ratings, helpful voting, reports, and admin moderation:
- Strict field definitions preventing mass-assignment (extra='forbid')
- Integer rating validation bounded between 1 and 5
- Character bounds on title and body
- Privacy-safe public review serialization without exposing PII or internal IDs
- Support for dual snake_case and camelCase aliases for seamless frontend compatibility
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.review import ReviewStatus
from app.models.review_report import ReportReason, ReportStatus


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    order_item_id: str = Field(
        ...,
        description="ID of the delivered order item verifying authentic product purchase",
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Customer rating as integer between 1 and 5",
    )
    title: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Headline or summary of the review",
    )
    body: str = Field(
        ...,
        min_length=5,
        max_length=3000,
        description="Detailed review text content",
    )


class ReviewUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Updated rating as integer between 1 and 5",
    )
    title: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
        description="Updated review headline",
    )
    body: Optional[str] = Field(
        None,
        min_length=5,
        max_length=3000,
        description="Updated review text content",
    )


class ReviewPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    rating: int
    title: str
    body: str
    status: str
    is_verified_purchase: bool
    helpful_count: int
    created_at: datetime
    reviewer_name: str
    user_voted_helpful: bool = False
    is_own_review: bool = False


class ReviewUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str
    product_name: str
    product_slug: Optional[str] = None
    product_image_url: Optional[str] = None
    order_id: Optional[str] = None
    rating: int
    title: str
    body: str
    status: str
    is_verified_purchase: bool
    helpful_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReviewSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    average_rating: float
    total_reviews: int
    distribution: Dict[str, int]


class ReviewListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[ReviewPublicResponse]
    total: int
    next_cursor: Optional[str] = None
    summary: Optional[ReviewSummaryResponse] = None


class ReviewUserListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[ReviewUserResponse]
    total: int
    limit: int
    offset: int


class ReviewHelpfulResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    review_id: str
    helpful_count: int
    user_voted_helpful: bool


class ReviewReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    reason: ReportReason = Field(..., description="Reason category for flagging the review")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional additional details regarding the concern",
    )


class ReviewReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    review_id: str
    reason: str
    description: Optional[str] = None
    status: str
    created_at: datetime


class ReviewableOrderItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_item_id: str
    order_id: str
    order_number: str
    product_id: str
    product_name: str
    variant_name: Optional[str] = None
    delivered_at: Optional[datetime] = None


class ReviewEligibilityResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    can_review: bool
    reason: Optional[str] = None
    reviewable_items: List[ReviewableOrderItem] = []


class AdminReviewStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status: ReviewStatus = Field(..., description="Target review status")
    reason: Optional[str] = Field(None, max_length=500, description="Administrative reasoning")


class AdminReviewDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user_id: str
    product_id: str
    product_name: Optional[str] = None
    order_id: Optional[str] = None
    order_item_id: Optional[str] = None
    rating: int
    title: str
    body: str
    status: str
    is_verified_purchase: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
