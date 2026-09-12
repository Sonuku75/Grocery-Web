"use client";

import React from "react";
import { Check } from "lucide-react";
import { ProductVariant } from "@/types";
import { formatCurrency } from "@/lib/utils";

interface VariantSelectorProps {
  variants: ProductVariant[];
  selectedVariant: ProductVariant | null;
  onSelectVariant: (variant: ProductVariant) => void;
}

export function VariantSelector({
  variants,
  selectedVariant,
  onSelectVariant,
}: VariantSelectorProps) {
  if (!variants || variants.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
        <span>Select Pack / Size:</span>
        {selectedVariant && (
          <span className="text-slate-400 font-normal">
            SKU: <span className="font-mono text-slate-600">{selectedVariant.sku}</span>
          </span>
        )}
      </div>

      <div
        role="radiogroup"
        aria-label="Product size and pack options"
        className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-2.5"
      >
        {variants.map((v) => {
          const isSelected = selectedVariant?.id === v.id;
          const discount = v.discountPercentage ?? v.discount_percentage ?? 0;
          const displayUnit = `${v.unitValue ?? v.unit_value ?? ""} ${v.unitType ?? v.unit_type ?? ""}`.trim() || v.name;

          return (
            <button
              key={v.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => onSelectVariant(v)}
              className={`relative flex flex-col p-2.5 sm:p-3 rounded-2xl border text-left transition-all duration-200 min-h-[48px] focus:outline-none focus:ring-2 focus:ring-brand-500/20 active:scale-[0.98] ${
                isSelected
                  ? "border-brand-600 bg-brand-50/40 shadow-xs ring-1 ring-brand-600"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/60"
              }`}
            >
              {/* Top Row: Unit Name & Selected Icon */}
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className={`text-xs font-bold truncate ${isSelected ? "text-brand-900" : "text-slate-800"}`}>
                  {displayUnit}
                </span>
                {isSelected && (
                  <span className="shrink-0 w-4 h-4 rounded-full bg-brand-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  </span>
                )}
              </div>

              {/* Price & MRP Row */}
              <div className="flex items-baseline gap-1.5 flex-wrap mt-auto">
                <span className="text-xs sm:text-sm font-extrabold text-slate-900">
                  {formatCurrency(v.price)}
                </span>
                {v.mrp > v.price && (
                  <span className="text-[10px] text-slate-400 line-through">
                    {formatCurrency(v.mrp)}
                  </span>
                )}
              </div>

              {/* Discount Tag */}
              {discount > 0 && (
                <span className="inline-block mt-1 text-[9px] font-extrabold text-emerald-600 uppercase tracking-tight">
                  Save {discount}%
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
