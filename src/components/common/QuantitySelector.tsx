"use client";

import React from "react";
import { Plus, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuantitySelectorProps {
  quantity: number;
  onIncrease: () => void;
  onDecrease: () => void;
  max?: number;
  min?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function QuantitySelector({
  quantity,
  onIncrease,
  onDecrease,
  max = 99,
  min = 1,
  size = "md",
  className,
}: QuantitySelectorProps) {
  const sizeStyles = {
    sm: {
      btn: "h-7 w-7 text-xs",
      text: "w-8 text-xs font-semibold",
      container: "p-0.5",
    },
    md: {
      btn: "h-8 w-8 text-sm",
      text: "w-10 text-sm font-semibold",
      container: "p-1",
    },
    lg: {
      btn: "h-10 w-10 text-base",
      text: "w-12 text-base font-bold",
      container: "p-1.5",
    },
  };

  const currentSize = sizeStyles[size];

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-xl bg-slate-50 border border-slate-200 shadow-xs",
        currentSize.container,
        className
      )}
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onDecrease();
        }}
        disabled={quantity <= min}
        className={cn(
          "flex items-center justify-center rounded-lg bg-white text-slate-700 hover:bg-slate-100 active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all shadow-xs",
          currentSize.btn
        )}
        aria-label="Decrease quantity"
      >
        <Minus className="w-3.5 h-3.5" />
      </button>

      <span className={cn("text-center text-slate-900 select-none", currentSize.text)}>
        {quantity}
      </span>

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onIncrease();
        }}
        disabled={quantity >= max}
        className={cn(
          "flex items-center justify-center rounded-lg bg-brand-600 text-white hover:bg-brand-700 active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all shadow-xs",
          currentSize.btn
        )}
        aria-label="Increase quantity"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
