import { apiClient } from "@/lib/api";
import {
  ProductReview,
  RatingSummary,
  ReviewEligibility,
  ReviewableItem,
} from "@/types";

export interface ReviewFilterParams {
  rating?: number;
  verifiedOnly?: boolean;
  sort?: "MOST_RECENT" | "MOST_HELPFUL" | "HIGHEST_RATING" | "LOWEST_RATING" | string;
  limit?: number;
  cursor?: string;
}

export interface ReviewListResult {
  items: ProductReview[];
  nextCursor?: string;
  total: number;
  summary?: RatingSummary;
}

export interface CreateReviewPayload {
  orderItemId: string;
  rating: number;
  title: string;
  body: string;
}

export interface UpdateReviewPayload {
  rating?: number;
  title?: string;
  body?: string;
}

export interface ReportReviewPayload {
  reason: "SPAM" | "OFFENSIVE" | "FAKE_REVIEW" | "MISLEADING" | "PERSONAL_INFORMATION" | "OTHER" | string;
  description?: string;
}

export function normalizeReview(raw: any): ProductReview {
  if (!raw) return raw;
  return {
    id: raw.id,
    productId: raw.productId || raw.product_id,
    product_id: raw.product_id || raw.productId,
    userId: raw.userId || raw.user_id,
    user_id: raw.user_id || raw.userId,
    userName: raw.reviewerName || raw.reviewer_name || raw.userName || "Verified Customer",
    reviewerName: raw.reviewerName || raw.reviewer_name || raw.userName || "Verified Customer",
    reviewer_name: raw.reviewer_name || raw.reviewerName || raw.userName || "Verified Customer",
    rating: Number(raw.rating ?? 5),
    title: raw.title || "",
    body: raw.body || raw.comment || "",
    comment: raw.body || raw.comment || "",
    status: raw.status || "PUBLISHED",
    isVerifiedPurchase: Boolean(raw.isVerifiedPurchase ?? raw.is_verified_purchase ?? true),
    is_verified_purchase: Boolean(raw.is_verified_purchase ?? raw.isVerifiedPurchase ?? true),
    helpfulCount: Number(raw.helpfulCount ?? raw.helpful_count ?? 0),
    helpful_count: Number(raw.helpful_count ?? raw.helpfulCount ?? 0),
    userVotedHelpful: Boolean(raw.userVotedHelpful ?? raw.user_voted_helpful ?? false),
    user_voted_helpful: Boolean(raw.user_voted_helpful ?? raw.userVotedHelpful ?? false),
    isOwnReview: Boolean(raw.isOwnReview ?? raw.is_own_review ?? false),
    is_own_review: Boolean(raw.is_own_review ?? raw.isOwnReview ?? false),
    createdAt: raw.createdAt || raw.created_at || new Date().toISOString(),
    created_at: raw.created_at || raw.createdAt || new Date().toISOString(),
    updatedAt: raw.updatedAt || raw.updated_at,
    updated_at: raw.updated_at || raw.updatedAt,
  };
}

export const reviewService = {
  /**
   * Retrieves published, paginated reviews for a product with filters and sorting.
   */
  async getProductReviews(
    productId: string,
    params: ReviewFilterParams = {}
  ): Promise<ReviewListResult> {
    try {
      const queryParams: Record<string, string | number | boolean | undefined> = {};
      if (params.rating) queryParams.rating = params.rating;
      if (params.verifiedOnly) queryParams.verified_only = true;
      if (params.sort) queryParams.sort = params.sort;
      if (params.limit) queryParams.limit = params.limit;
      if (params.cursor) queryParams.cursor = params.cursor;

      const res = await apiClient.get<any>(`/products/${productId}/reviews`, {
        params: queryParams,
      });

      const data = res.data;
      const items = Array.isArray(data?.items) ? data.items.map(normalizeReview) : [];
      const summary = data?.summary
        ? {
            averageRating: Number(data.summary.average_rating ?? data.summary.averageRating ?? 0),
            totalReviews: Number(data.summary.total_reviews ?? data.summary.totalReviews ?? 0),
            distribution: data.summary.distribution || { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 },
          }
        : undefined;

      return {
        items,
        nextCursor: data?.next_cursor,
        total: Number(data?.total ?? items.length),
        summary,
      };
    } catch (err) {
      console.warn(`reviewService.getProductReviews failed for ${productId}:`, err);
      return { items: [], total: 0 };
    }
  },

  /**
   * Retrieves public rating summary and star distribution for a product.
   */
  async getProductReviewSummary(productId: string): Promise<RatingSummary> {
    try {
      const res = await apiClient.get<any>(`/products/${productId}/review-summary`);
      const raw = res.data;
      return {
        averageRating: Number(raw?.average_rating ?? raw?.averageRating ?? 0),
        totalReviews: Number(raw?.total_reviews ?? raw?.totalReviews ?? 0),
        distribution: raw?.distribution || { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 },
      };
    } catch (err) {
      console.warn(`reviewService.getProductReviewSummary failed for ${productId}:`, err);
      return {
        averageRating: 0,
        totalReviews: 0,
        distribution: { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 },
      };
    }
  },

  /**
   * Checks if authenticated user has eligible delivered purchase items to review.
   */
  async checkEligibility(productId: string): Promise<ReviewEligibility> {
    try {
      const res = await apiClient.get<any>(`/products/${productId}/eligibility`);
      const data = res.data;
      const reviewableItems: ReviewableItem[] = (data?.reviewable_items || []).map((it: any) => ({
        orderItemId: it.order_item_id || it.orderItemId,
        orderId: it.order_id || it.orderId,
        orderNumber: it.order_number || it.orderNumber || "",
        productId: it.product_id || it.productId || productId,
        productName: it.product_name || it.productName || "Product",
        variantName: it.variant_name || it.variantName,
        deliveredAt: it.delivered_at || it.deliveredAt,
      }));

      return {
        canReview: Boolean(data?.can_review),
        reason: data?.reason,
        reviewableItems,
      };
    } catch (err) {
      console.warn(`reviewService.checkEligibility failed for ${productId}:`, err);
      return { canReview: false, reason: "UNAUTHENTICATED", reviewableItems: [] };
    }
  },

  /**
   * Submits a new verified review for a product.
   */
  async createReview(
    productId: string,
    payload: CreateReviewPayload
  ): Promise<ProductReview> {
    const res = await apiClient.post<any>(`/products/${productId}/reviews`, {
      order_item_id: payload.orderItemId,
      rating: payload.rating,
      title: payload.title,
      body: payload.body,
    });
    return normalizeReview(res.data);
  },

  /**
   * Edits an existing review (rating, title, body).
   */
  async updateReview(
    reviewId: string,
    payload: UpdateReviewPayload
  ): Promise<ProductReview> {
    const bodyObj: Record<string, any> = {};
    if (payload.rating !== undefined) bodyObj.rating = payload.rating;
    if (payload.title !== undefined) bodyObj.title = payload.title;
    if (payload.body !== undefined) bodyObj.body = payload.body;

    const res = await apiClient.patch<any>(`/reviews/${reviewId}`, bodyObj);
    return normalizeReview(res.data);
  },

  /**
   * Soft-deletes a review.
   */
  async deleteReview(reviewId: string): Promise<boolean> {
    const res = await apiClient.delete<any>(`/reviews/${reviewId}`);
    return Boolean(res.success);
  },

  /**
   * Marks a review as helpful.
   */
  async voteHelpful(reviewId: string): Promise<{ helpfulCount: number; userVotedHelpful: boolean }> {
    const res = await apiClient.post<any>(`/reviews/${reviewId}/helpful`, {});
    return {
      helpfulCount: Number(res.data?.helpful_count ?? res.data?.helpfulCount ?? 0),
      userVotedHelpful: true,
    };
  },

  /**
   * Removes helpful vote from a review.
   */
  async removeHelpfulVote(reviewId: string): Promise<{ helpfulCount: number; userVotedHelpful: boolean }> {
    const res = await apiClient.delete<any>(`/reviews/${reviewId}/helpful`);
    return {
      helpfulCount: Number(res.data?.helpful_count ?? res.data?.helpfulCount ?? 0),
      userVotedHelpful: false,
    };
  },

  /**
   * Reports an inappropriate review for moderation.
   */
  async reportReview(
    reviewId: string,
    payload: ReportReviewPayload
  ): Promise<boolean> {
    const res = await apiClient.post<any>(`/reviews/${reviewId}/reports`, {
      reason: payload.reason,
      description: payload.description || undefined,
    });
    return Boolean(res.success);
  },

  /**
   * Retrieves all reviews written by the currently authenticated user.
   */
  async getMyReviews(params: { limit?: number; offset?: number } = {}): Promise<{
    items: ProductReview[];
    total: number;
  }> {
    const res = await apiClient.get<any>("/users/me/reviews", {
      params: {
        limit: params.limit || 20,
        offset: params.offset || 0,
      },
    });
    const data = res.data;
    const items = Array.isArray(data?.items) ? data.items.map(normalizeReview) : [];
    return {
      items,
      total: Number(data?.total ?? items.length),
    };
  },
};
