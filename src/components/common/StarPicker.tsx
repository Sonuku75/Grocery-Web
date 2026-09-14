"use client";

import React, { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarPickerProps {
  value: number;
  onChange: (rating: number) => void;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const RATING_LABELS: Record<number, string> = {
  1: "1 star — Poor",
  2: "2 stars — Fair",
  3: "3 stars — Average",
  4: "4 stars — Very Good",
  5: "5 stars — Exceptional",
};

export function StarPicker({
  value,
  onChange,
  disabled = false,
  size = "md",
  className,
}: StarPickerProps) {
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);

  const starSizes = {
    sm: "w-5 h-5",
    md: "w-7 h-7",
    lg: "w-9 h-9",
  };

  const activeRating = hoveredStar !== null ? hoveredStar : value;

  const handleKeyDown = (e: React.KeyboardEvent, star: number) => {
    if (disabled) return;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = Math.min(5, star + 1);
      onChange(next);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      e.preventDefault();
      const prev = Math.max(1, star - 1);
      onChange(prev);
    }
  };

  return (
    <div className={cn("space-y-1.5", className)}>
      <div
        role="radiogroup"
        aria-label="Rating out of 5 stars"
        className="flex items-center gap-1.5"
        onMouseLeave={() => setHoveredStar(null)}
      >
        {[1, 2, 3, 4, 5].map((star) => {
          const isFilled = star <= activeRating;
          return (
            <button
              key={star}
              type="button"
              role="radio"
              aria-checked={value === star}
              aria-label={RATING_LABELS[star]}
              disabled={disabled}
              onClick={() => onChange(star)}
              onMouseEnter={() => setHoveredStar(star)}
              onFocus={() => setHoveredStar(star)}
              onBlur={() => setHoveredStar(null)}
              onKeyDown={(e) => handleKeyDown(e, star)}
              className={cn(
                "p-1 rounded-lg transition-transform hover:scale-110 active:scale-95 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
                disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
              )}
            >
              <Star
                className={cn(
                  starSizes[size],
                  "transition-colors",
                  isFilled
                    ? "fill-amber-400 text-amber-400 drop-shadow-xs"
                    : "text-slate-300 fill-slate-100 hover:text-amber-300"
                )}
              />
            </button>
          );
        })}
      </div>
      <p className="text-xs font-medium text-slate-500" aria-live="polite">
        {RATING_LABELS[activeRating] || "Select your rating"}
      </p>
    </div>
  );
}
