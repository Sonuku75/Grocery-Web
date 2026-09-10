"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ProductReview } from "@/types";
import { Rating } from "@/components/common/Rating";
import { Button } from "@/components/common/Button";
import { formatDate } from "@/lib/utils";
import { MessageSquarePlus, CheckCircle2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

interface ProductReviewsProps {
  reviews: ProductReview[];
  rating: number;
  ratingCount: number;
}

export function ProductReviews({ reviews: initialReviews, rating, ratingCount }: ProductReviewsProps) {
  const [reviews, setReviews] = useState<ProductReview[]>(initialReviews);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [name, setName] = useState("");
  const [newRating, setNewRating] = useState(5);
  const [comment, setComment] = useState("");
  const { showToast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !comment.trim()) {
      showToast("Please provide your name and review details", "error");
      return;
    }

    const newRev: ProductReview = {
      id: "rev-" + Date.now(),
      productId: "curr",
      userId: "usr-me",
      userName: name.trim(),
      rating: newRating,
      comment: comment.trim(),
      createdAt: new Date().toISOString(),
    };

    setReviews([newRev, ...reviews]);
    setName("");
    setComment("");
    setShowReviewForm(false);
    showToast("Thank you for your feedback! Review published.", "success");
  };

  return (
    <div className="space-y-6">
      {/* Rating summary bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 p-6 rounded-2xl bg-slate-50 border border-slate-100">
        <div className="flex items-center gap-4">
          <div className="text-4xl font-extrabold text-slate-900">{rating.toFixed(1)}</div>
          <div>
            <Rating rating={rating} showCount={false} size="md" />
            <p className="text-xs text-slate-500 mt-1">Based on {ratingCount} verified customer reviews</p>
          </div>
        </div>

        <Button
          variant="outline"
          leftIcon={<MessageSquarePlus className="w-4 h-4" />}
          onClick={() => setShowReviewForm(!showReviewForm)}
        >
          Write a Review
        </Button>
      </div>

      {/* Review submission form */}
      {showReviewForm && (
        <form onSubmit={handleSubmit} className="p-6 rounded-2xl border border-brand-200 bg-brand-50/30 space-y-4 animate-fade-in">
          <h4 className="text-sm font-bold text-slate-800">Share your experience with this product</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Your Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Alex R."
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-none focus:border-brand-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Your Rating</label>
              <select
                value={newRating}
                onChange={(e) => setNewRating(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-none focus:border-brand-500"
              >
                <option value={5}>⭐⭐⭐⭐⭐ (5 - Exceptional)</option>
                <option value={4}>⭐⭐⭐⭐ (4 - Very Good)</option>
                <option value={3}>⭐⭐⭐ (3 - Average)</option>
                <option value={2}>⭐⭐ (2 - Below Average)</option>
                <option value={1}>⭐ (1 - Poor)</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Review Comments</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              placeholder="How was the freshness, taste, packaging, and delivery speed?"
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-none focus:border-brand-500"
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => setShowReviewForm(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Submit Review
            </Button>
          </div>
        </form>
      )}

      {/* Review list */}
      <div className="divide-y divide-slate-100">
        {reviews.map((rev) => (
          <div key={rev.id} className="py-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 font-bold text-xs flex items-center justify-center uppercase">
                  {rev.userName.charAt(0)}
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    {rev.userName}
                    <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded-md flex items-center gap-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5" /> Verified Purchase
                    </span>
                  </span>
                  <span className="text-[10px] text-slate-400">{formatDate(rev.createdAt)}</span>
                </div>
              </div>
              <Rating rating={rev.rating} showCount={false} size="sm" />
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">{rev.comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
