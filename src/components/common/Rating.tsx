"use client";

import React from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface RatingProps {
  rating: number;
  count?: number;
  size?: "sm" | "md" | "lg";
  showCount?: boolean;
  className?: string;
}

export function Rating({
  rating,
  count,
  size = "sm",
  showCount = true,
  className,
}: RatingProps) {
  const starSizes = {
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  const textSizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className={cn("inline-flex items-center gap-1.5", className)}>
      <div className="flex items-center text-amber-400">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={cn(
              starSizes[size],
              star <= Math.round(rating)
                ? "fill-amber-400 text-amber-400"
                : "text-slate-200 fill-slate-100"
            )}
          />
        ))}
      </div>
      <span className={cn("font-bold text-slate-800", textSizes[size])}>
        {rating.toFixed(1)}
      </span>
      {showCount && count !== undefined && (
        <span className={cn("text-slate-400 font-normal", textSizes[size])}>
          ({count.toLocaleString()})
        </span>
      )}
    </div>
  );
}
