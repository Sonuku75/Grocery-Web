"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ChevronDown,
  Flag,
  Loader2,
  MessageSquarePlus,
  Pencil,
  RotateCcw,
  Star,
  ThumbsUp,
  Trash2,
  X,
} from "lucide-react";
import { ProductReview, RatingSummary, ReviewEligibility } from "@/types";
import {
  CreateReviewPayload,
  ReportReviewPayload,
  ReviewFilterParams,
  UpdateReviewPayload,
  reviewService,
} from "@/services/reviewService";
import { Rating } from "@/components/common/Rating";
import { Button } from "@/components/common/Button";
import { Modal } from "@/components/common/Modal";
import { StarPicker } from "@/components/common/StarPicker";
import { formatDate } from "@/lib/utils";
import { useToast } from "@/context/ToastContext";

interface ProductReviewsProps {
  productId: string;
  initialRating?: number;
  initialRatingCount?: number;
}

export function ProductReviews({
  productId,
  initialRating = 0,
  initialRatingCount = 0,
}: ProductReviewsProps) {
  const { showToast } = useToast();

  // Review list state
  const [reviews, setReviews] = useState<ProductReview[]>([]);
  const [summary, setSummary] = useState<RatingSummary>({
    averageRating: initialRating,
    totalReviews: initialRatingCount,
    distribution: { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 },
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Filters and Sorting
  const [selectedRatingFilter, setSelectedRatingFilter] = useState<number | undefined>(undefined);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);
  const [sortOption, setSortOption] = useState<string>("MOST_RECENT");

  // Eligibility and Write Review Form
  const [eligibility, setEligibility] = useState<ReviewEligibility | null>(null);
  const [checkingEligibility, setCheckingEligibility] = useState<boolean>(false);
  const [showWriteModal, setShowWriteModal] = useState<boolean>(false);
  const [writeRating, setWriteRating] = useState<number>(5);
  const [writeTitle, setWriteTitle] = useState<string>("");
  const [writeBody, setWriteBody] = useState<string>("");
  const [selectedOrderItemId, setSelectedOrderItemId] = useState<string>("");
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);

  // Edit Review Modal
  const [editingReview, setEditingReview] = useState<ProductReview | null>(null);
  const [editRating, setEditRating] = useState<number>(5);
  const [editTitle, setEditTitle] = useState<string>("");
  const [editBody, setEditBody] = useState<string>("");
  const [updatingReview, setUpdatingReview] = useState<boolean>(false);

  // Delete Review Modal
  const [deletingReviewId, setDeletingReviewId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Report Review Modal
  const [reportingReviewId, setReportingReviewId] = useState<string | null>(null);
  const [reportReason, setReportReason] = useState<string>("SPAM");
  const [reportDescription, setReportDescription] = useState<string>("");
  const [submittingReport, setSubmittingReport] = useState<boolean>(false);

  // Fetch reviews based on active filters & sort
  const fetchReviews = useCallback(
    async (reset: boolean = true) => {
      if (reset) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      try {
        const params: ReviewFilterParams = {
          rating: selectedRatingFilter,
          verifiedOnly,
          sort: sortOption,
          limit: 10,
          cursor: reset ? undefined : nextCursor,
        };

        const result = await reviewService.getProductReviews(productId, params);

        if (reset) {
          setReviews(result.items);
        } else {
          setReviews((prev) => [...prev, ...result.items]);
        }

        setNextCursor(result.nextCursor);
        setTotalCount(result.total);

        if (result.summary) {
          setSummary(result.summary);
        }
      } catch (err) {
        console.error("Failed to fetch product reviews:", err);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [productId, selectedRatingFilter, verifiedOnly, sortOption, nextCursor]
  );

  // Initial load and filter change trigger
  useEffect(() => {
    fetchReviews(true);
  }, [productId, selectedRatingFilter, verifiedOnly, sortOption]);

  // Load rating summary & eligibility on mount
  useEffect(() => {
    reviewService
      .getProductReviewSummary(productId)
      .then((s) => {
        if (s && s.totalReviews > 0) setSummary(s);
      })
      .catch(() => {});

    setCheckingEligibility(true);
    reviewService
      .checkEligibility(productId)
      .then((el) => {
        setEligibility(el);
        if (el.reviewableItems && el.reviewableItems.length > 0) {
          setSelectedOrderItemId(el.reviewableItems[0].orderItemId);
        }
      })
      .catch(() => setEligibility(null))
      .finally(() => setCheckingEligibility(false));
  }, [productId]);

  // Handle Write Review Submission
  const handleCreateReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderItemId) {
      showToast("Please select the purchased order item you are reviewing.", "error");
      return;
    }
    if (!writeTitle.trim() || writeTitle.trim().length < 2) {
      showToast("Review headline must be at least 2 characters.", "error");
      return;
    }
    if (!writeBody.trim() || writeBody.trim().length < 5) {
      showToast("Review text must be at least 5 characters.", "error");
      return;
    }

    setSubmittingReview(true);
    try {
      const payload: CreateReviewPayload = {
        orderItemId: selectedOrderItemId,
        rating: writeRating,
        title: writeTitle.trim(),
        body: writeBody.trim(),
      };

      const newReview = await reviewService.createReview(productId, payload);
      setReviews((prev) => [newReview, ...prev]);
      setShowWriteModal(false);
      setWriteTitle("");
      setWriteBody("");
      setWriteRating(5);
      showToast("Thank you! Your verified review has been submitted.", "success");

      // Refresh summary & eligibility
      const updatedSummary = await reviewService.getProductReviewSummary(productId);
      setSummary(updatedSummary);
      const updatedEligibility = await reviewService.checkEligibility(productId);
      setEligibility(updatedEligibility);
    } catch (err: any) {
      const msg = err?.message || "Failed to submit review. Please check requirements.";
      showToast(msg, "error");
    } finally {
      setSubmittingReview(false);
    }
  };

  // Handle Edit Review Submission
  const handleUpdateReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingReview) return;

    setUpdatingReview(true);
    try {
      const payload: UpdateReviewPayload = {
        rating: editRating,
        title: editTitle.trim(),
        body: editBody.trim(),
      };

      const updated = await reviewService.updateReview(editingReview.id, payload);
      setReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setEditingReview(null);
      showToast("Your review has been updated.", "success");

      const updatedSummary = await reviewService.getProductReviewSummary(productId);
      setSummary(updatedSummary);
    } catch (err: any) {
      const msg = err?.message || "Failed to update review.";
      showToast(msg, "error");
    } finally {
      setUpdatingReview(false);
    }
  };

  // Handle Delete Review Confirmation
  const handleDeleteReview = async () => {
    if (!deletingReviewId) return;

    setIsDeleting(true);
    try {
      await reviewService.deleteReview(deletingReviewId);
      setReviews((prev) => prev.filter((r) => r.id !== deletingReviewId));
      setDeletingReviewId(null);
      showToast("Your review has been removed.", "success");

      const updatedSummary = await reviewService.getProductReviewSummary(productId);
      setSummary(updatedSummary);
    } catch (err: any) {
      const msg = err?.message || "Failed to delete review.";
      showToast(msg, "error");
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle Helpful Vote Toggle
  const handleToggleHelpful = async (review: ProductReview) => {
    const isCurrentlyHelpful = Boolean(review.userVotedHelpful);
    const prevCount = review.helpfulCount || 0;

    // Optimistic UI update
    setReviews((prev) =>
      prev.map((r) =>
        r.id === review.id
          ? {
              ...r,
              userVotedHelpful: !isCurrentlyHelpful,
              helpfulCount: isCurrentlyHelpful ? Math.max(0, prevCount - 1) : prevCount + 1,
            }
          : r
      )
    );

    try {
      if (isCurrentlyHelpful) {
        await reviewService.removeHelpfulVote(review.id);
      } else {
        await reviewService.voteHelpful(review.id);
      }
    } catch (err: any) {
      // Rollback on error
      setReviews((prev) =>
        prev.map((r) =>
          r.id === review.id
            ? {
                ...r,
                userVotedHelpful: isCurrentlyHelpful,
                helpfulCount: prevCount,
              }
            : r
        )
      );
      showToast(err?.message || "Action failed. Please sign in.", "error");
    }
  };

  // Handle Report Review
  const handleReportReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportingReviewId) return;

    setSubmittingReport(true);
    try {
      const payload: ReportReviewPayload = {
        reason: reportReason,
        description: reportDescription.trim() || undefined,
      };
      await reviewService.reportReview(reportingReviewId, payload);
      setReportingReviewId(null);
      setReportDescription("");
      showToast("Thank you. The review has been flagged for moderation.", "success");
    } catch (err: any) {
      showToast(err?.message || "Failed to report review.", "error");
    } finally {
      setSubmittingReport(false);
    }
  };

  // Distribution calculations
  const totalReviews = summary.totalReviews || 0;
  const avgRating = Number(summary.averageRating || 0);

  const getPercentage = (count: number) => {
    if (totalReviews === 0) return 0;
    return Math.round((count / totalReviews) * 100);
  };

  return (
    <div className="space-y-8" id="product-reviews-section">
      {/* ------------------------------------------------------------- */}
      {/* Section Header & Rating Overview */}
      {/* ------------------------------------------------------------- */}
      <div className="rounded-3xl bg-slate-50/80 border border-slate-200/70 p-6 sm:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Rating Summary Box */}
          <div className="lg:col-span-4 flex flex-col items-center sm:items-start text-center sm:text-left space-y-3 sm:border-r sm:border-slate-200/80 sm:pr-8">
            <h3 className="text-base font-bold text-slate-900">Customer Reviews & Ratings</h3>
            <div className="flex items-baseline gap-3">
              <span className="text-5xl font-extrabold tracking-tight text-slate-900">
                {avgRating > 0 ? avgRating.toFixed(1) : "—"}
              </span>
              <span className="text-sm font-semibold text-slate-400">out of 5</span>
            </div>

            <Rating rating={avgRating} showCount={false} size="md" />

            <p className="text-xs text-slate-500">
              {totalReviews > 0 ? (
                <>Based on <span className="font-bold text-slate-700">{totalReviews.toLocaleString()}</span> verified customer reviews</>
              ) : (
                "No reviews yet. Be the first to share your experience!"
              )}
            </p>

            {/* Write Review Action */}
            <div className="pt-2 w-full sm:w-auto">
              {eligibility?.canReview ? (
                <Button
                  variant="primary"
                  leftIcon={<MessageSquarePlus className="w-4 h-4" />}
                  onClick={() => setShowWriteModal(true)}
                  className="w-full sm:w-auto"
                >
                  Write a Review
                </Button>
              ) : eligibility?.reason === "REVIEW_ALREADY_EXISTS" ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" /> You reviewed this item
                </span>
              ) : (
                <Button
                  variant="outline"
                  leftIcon={<MessageSquarePlus className="w-4 h-4" />}
                  onClick={() => {
                    if (eligibility?.reason === "UNAUTHENTICATED") {
                      showToast("Please sign in to review purchased items.", "info");
                    } else {
                      showToast(
                        "Only customers with delivered purchases can review this item.",
                        "info"
                      );
                    }
                  }}
                  className="w-full sm:w-auto"
                >
                  Write a Review
                </Button>
              )}
            </div>
          </div>

          {/* Star Distribution Breakdown */}
          <div className="lg:col-span-8 space-y-2.5">
            {[5, 4, 3, 2, 1].map((star) => {
              const count = Number(summary.distribution?.[String(star)] ?? 0);
              const pct = getPercentage(count);
              const isSelected = selectedRatingFilter === star;

              return (
                <button
                  key={star}
                  type="button"
                  onClick={() => setSelectedRatingFilter(isSelected ? undefined : star)}
                  className={`w-full flex items-center gap-3 text-xs group transition-colors p-1 rounded-lg focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
                    isSelected ? "bg-brand-50/70 font-bold" : "hover:bg-slate-100/60"
                  }`}
                  aria-label={`Filter by ${star} star reviews (${count} reviews, ${pct}%)`}
                >
                  <span className="w-12 text-left font-semibold text-slate-700 flex items-center gap-1">
                    {star} <Star className="w-3 h-3 fill-amber-400 text-amber-400 inline" />
                  </span>
                  <div className="flex-1 h-2.5 rounded-full bg-slate-200/80 overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isSelected ? "bg-brand-600" : "bg-amber-400 group-hover:bg-amber-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-slate-500 font-mono">
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Filters & Sorting Bar */}
      {/* ------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div className="flex flex-wrap items-center gap-2">
          {/* Rating filter pills */}
          <button
            type="button"
            onClick={() => setSelectedRatingFilter(undefined)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
              selectedRatingFilter === undefined
                ? "bg-brand-600 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            All Reviews
          </button>
          {[5, 4, 3, 2, 1].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSelectedRatingFilter(selectedRatingFilter === s ? undefined : s)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1 transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
                selectedRatingFilter === s
                  ? "bg-brand-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s} <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
            </button>
          ))}

          {/* Verified purchase filter toggle */}
          <label className="flex items-center gap-1.5 ml-2 cursor-pointer text-xs font-medium text-slate-700 select-none">
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
              className="rounded-sm border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            Verified Only
          </label>
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <label htmlFor="review-sort" className="text-xs text-slate-500 font-medium">
            Sort by:
          </label>
          <div className="relative">
            <select
              id="review-sort"
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="appearance-none bg-white text-xs font-semibold text-slate-800 border border-slate-200 rounded-xl px-3 py-1.5 pr-8 focus:outline-hidden focus:border-brand-500 shadow-2xs cursor-pointer"
            >
              <option value="MOST_RECENT">Most Recent</option>
              <option value="MOST_HELPFUL">Most Helpful</option>
              <option value="HIGHEST_RATING">Highest Rating</option>
              <option value="LOWEST_RATING">Lowest Rating</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Reviews List */}
      {/* ------------------------------------------------------------- */}
      {loading ? (
        <div className="space-y-4 py-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-6 rounded-2xl bg-white border border-slate-100 animate-pulse space-y-3">
              <div className="flex items-center justify-between">
                <div className="h-4 w-32 bg-slate-200 rounded-md" />
                <div className="h-4 w-20 bg-slate-200 rounded-md" />
              </div>
              <div className="h-3 w-48 bg-slate-100 rounded-md" />
              <div className="h-12 w-full bg-slate-50 rounded-md" />
            </div>
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12 px-4 rounded-3xl bg-slate-50/50 border border-dashed border-slate-200 space-y-3">
          <div className="w-12 h-12 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mx-auto">
            <Star className="w-6 h-6 fill-brand-200" />
          </div>
          <h4 className="text-base font-bold text-slate-800">No reviews found</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {selectedRatingFilter !== undefined || verifiedOnly
              ? "No reviews match the selected filter criteria. Try changing your filters."
              : "No reviews yet. Verified customers will be able to review this item after delivery!"}
          </p>
        </div>
      ) : (
        <div className="space-y-4 divide-y divide-slate-100">
          {reviews.map((rev) => (
            <div key={rev.id} className="pt-5 first:pt-0 space-y-3">
              {/* Review Header */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 font-bold text-xs flex items-center justify-center uppercase">
                    {(rev.reviewerName || rev.userName || "C").charAt(0)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">
                        {rev.reviewerName || rev.userName}
                      </span>
                      {rev.isVerifiedPurchase && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/70">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Verified Purchase
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400">
                      {formatDate(rev.createdAt)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Rating rating={rev.rating} showCount={false} size="sm" />
                  {/* Owner edit & delete controls */}
                  {rev.isOwnReview && (
                    <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingReview(rev);
                          setEditRating(rev.rating);
                          setEditTitle(rev.title || "");
                          setEditBody(rev.body || rev.comment || "");
                        }}
                        className="p-1 text-slate-400 hover:text-brand-600 transition-colors"
                        aria-label="Edit your review"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingReviewId(rev.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                        aria-label="Delete your review"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Review Content */}
              <div className="space-y-1">
                {rev.title && (
                  <h4 className="text-sm font-bold text-slate-900 leading-snug">
                    {rev.title}
                  </h4>
                )}
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                  {rev.body || rev.comment}
                </p>
              </div>

              {/* Review Footer Actions (Helpful & Report) */}
              <div className="flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={() => handleToggleHelpful(rev)}
                  className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
                    rev.userVotedHelpful
                      ? "bg-brand-50 text-brand-700 border-brand-300 font-semibold"
                      : "bg-white text-slate-500 border-slate-200 hover:bg-slate-50"
                  }`}
                  aria-label={`Mark as helpful. Current helpful count: ${rev.helpfulCount || 0}`}
                >
                  <ThumbsUp className={`w-3.5 h-3.5 ${rev.userVotedHelpful ? "fill-brand-600" : ""}`} />
                  <span>Helpful</span>
                  {(rev.helpfulCount || 0) > 0 && (
                    <span className="font-mono text-[11px] font-bold">
                      ({rev.helpfulCount})
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setReportingReviewId(rev.id)}
                  className="text-[11px] text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors"
                  aria-label="Report review for moderation"
                >
                  <Flag className="w-3 h-3" />
                  Report
                </button>
              </div>
            </div>
          ))}

          {/* Load More Pagination */}
          {nextCursor && (
            <div className="pt-6 text-center">
              <Button
                variant="outline"
                onClick={() => fetchReviews(false)}
                disabled={loadingMore}
              >
                {loadingMore ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Loading more...
                  </span>
                ) : (
                  "Load More Reviews"
                )}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Write Review Modal */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={showWriteModal}
        onClose={() => setShowWriteModal(false)}
        title="Write a Verified Review"
        description="Share your genuine feedback on quality, freshness, and delivery."
      >
        <form onSubmit={handleCreateReview} className="space-y-4">
          {/* Order selection if multiple eligible purchases */}
          {eligibility?.reviewableItems && eligibility.reviewableItems.length > 1 && (
            <div>
              <label htmlFor="order-item-select" className="block text-xs font-semibold text-slate-700 mb-1">
                Select Purchase Order
              </label>
              <select
                id="order-item-select"
                value={selectedOrderItemId}
                onChange={(e) => setSelectedOrderItemId(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
                required
              >
                {eligibility.reviewableItems.map((item) => (
                  <option key={item.orderItemId} value={item.orderItemId}>
                    Order #{item.orderNumber} ({item.variantName || item.productName})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Star Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Overall Rating *
            </label>
            <StarPicker value={writeRating} onChange={setWriteRating} size="md" />
          </div>

          {/* Title */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="review-title" className="text-xs font-semibold text-slate-700">
                Headline / Summary *
              </label>
              <span className="text-[10px] text-slate-400 font-mono">
                {writeTitle.length}/150
              </span>
            </div>
            <input
              id="review-title"
              type="text"
              maxLength={150}
              value={writeTitle}
              onChange={(e) => setWriteTitle(e.target.value)}
              placeholder="e.g., Exceptionally fresh and crisp!"
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
              required
            />
          </div>

          {/* Body */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="review-body" className="text-xs font-semibold text-slate-700">
                Detailed Review *
              </label>
              <span className="text-[10px] text-slate-400 font-mono">
                {writeBody.length}/3000
              </span>
            </div>
            <textarea
              id="review-body"
              rows={4}
              maxLength={3000}
              value={writeBody}
              onChange={(e) => setWriteBody(e.target.value)}
              placeholder="Tell other shoppers about the freshness, flavor, packaging, and delivery experience..."
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowWriteModal(false)}
              disabled={submittingReview}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={submittingReview}
            >
              {submittingReview ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Submitting...
                </span>
              ) : (
                "Submit Review"
              )}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------- */}
      {/* Edit Review Modal */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={Boolean(editingReview)}
        onClose={() => setEditingReview(null)}
        title="Edit Your Review"
        description="Update your rating and feedback."
      >
        <form onSubmit={handleUpdateReview} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Rating *
            </label>
            <StarPicker value={editRating} onChange={setEditRating} size="md" />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="edit-title" className="text-xs font-semibold text-slate-700">
                Headline *
              </label>
              <span className="text-[10px] text-slate-400 font-mono">
                {editTitle.length}/150
              </span>
            </div>
            <input
              id="edit-title"
              type="text"
              maxLength={150}
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="edit-body" className="text-xs font-semibold text-slate-700">
                Review *
              </label>
              <span className="text-[10px] text-slate-400 font-mono">
                {editBody.length}/3000
              </span>
            </div>
            <textarea
              id="edit-body"
              rows={4}
              maxLength={3000}
              value={editBody}
              onChange={(e) => setEditBody(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setEditingReview(null)}
              disabled={updatingReview}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={updatingReview}
            >
              {updatingReview ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving...
                </span>
              ) : (
                "Save Changes"
              )}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------- */}
      {/* Delete Review Confirmation Modal */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={Boolean(deletingReviewId)}
        onClose={() => setDeletingReviewId(null)}
        title="Delete Review"
        description="Are you sure you want to remove your review? This action cannot be undone."
        maxWidth="sm"
      >
        <div className="flex justify-end gap-2 pt-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDeletingReviewId(null)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleDeleteReview}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete Review"}
          </Button>
        </div>
      </Modal>

      {/* ------------------------------------------------------------- */}
      {/* Report Review Modal */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={Boolean(reportingReviewId)}
        onClose={() => setReportingReviewId(null)}
        title="Report Inappropriate Content"
        description="Help us keep Cartify reviews authentic, safe, and helpful."
      >
        <form onSubmit={handleReportReview} className="space-y-4">
          <div>
            <label htmlFor="report-reason" className="block text-xs font-semibold text-slate-700 mb-1">
              Reason for reporting *
            </label>
            <select
              id="report-reason"
              value={reportReason}
              onChange={(e) => setReportReason(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
              required
            >
              <option value="SPAM">Spam or advertising</option>
              <option value="OFFENSIVE">Inappropriate or offensive language</option>
              <option value="FAKE_REVIEW">Fake or paid review</option>
              <option value="MISLEADING">Misleading product claims</option>
              <option value="PERSONAL_INFORMATION">Contains personal contact information</option>
              <option value="OTHER">Other violation</option>
            </select>
          </div>

          <div>
            <label htmlFor="report-details" className="block text-xs font-semibold text-slate-700 mb-1">
              Additional Details (Optional)
            </label>
            <textarea
              id="report-details"
              rows={3}
              maxLength={1000}
              value={reportDescription}
              onChange={(e) => setReportDescription(e.target.value)}
              placeholder="Provide any additional context for our moderation team..."
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-hidden focus:border-brand-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setReportingReviewId(null)}
              disabled={submittingReport}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={submittingReport}
            >
              {submittingReport ? "Submitting..." : "Submit Report"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
