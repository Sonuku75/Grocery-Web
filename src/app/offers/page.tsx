"use client";

import React, { useEffect, useState } from "react";
import { Coupon, Product } from "@/types";
import { couponService } from "@/services/couponService";
import { productService } from "@/services/productService";
import { ProductGrid } from "@/components/products/ProductGrid";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Copy, Check, Tag, Sparkles, Zap, Percent } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function OffersPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [deals, setDeals] = useState<Product[]>([]);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const [c, d] = await Promise.all([
          couponService.getAvailableCoupons(),
          productService.getDeals(),
        ]);
        setCoupons(c);
        setDeals(d);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const copyCoupon = (code: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(code);
      setCopiedCode(code);
      showToast(`Coupon code ${code} copied to clipboard!`, "success");
      setTimeout(() => setCopiedCode(null), 3000);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-10">
      <Breadcrumb items={[{ label: "Offers & Deals" }]} />

      {/* Header Banner */}
      <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-accent-500 via-orange-600 to-amber-600 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-xl space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-xs text-xs font-black uppercase tracking-wider">
            <Zap className="w-3.5 h-3.5 text-amber-200 fill-amber-200" />
            <span>Exclusive Cartify Rewards</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
            Special Discounts & Daily Coupons
          </h1>
          <p className="text-sm text-orange-100 font-medium">
            Save up to 50% on everyday essentials, farm-fresh harvests, and first-order bonuses.
          </p>
        </div>

        <div className="absolute right-4 -bottom-6 w-64 h-64 opacity-20 pointer-events-none">
          <Percent className="w-full h-full" />
        </div>
      </div>

      {/* Active Coupons Grid */}
      <div>
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider mb-4">
          <Tag className="w-4 h-4 text-accent-500" />
          <span>Available Promo Codes</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {coupons.map((coupon) => (
            <div
              key={coupon.id}
              className="relative p-5 rounded-2xl bg-white border border-dashed border-accent-300 shadow-card flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black px-2.5 py-1 rounded-lg bg-accent-50 text-accent-700 border border-accent-200">
                    {coupon.discountType === "percent"
                      ? `${coupon.discountValue}% OFF`
                      : `$${coupon.discountValue} FLAT OFF`}
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium">
                    Min order ${coupon.minOrderAmount}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mt-1">{coupon.code}</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {coupon.description}
                </p>
              </div>

              <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">
                  Expires {coupon.validUntil}
                </span>
                <button
                  onClick={() => copyCoupon(coupon.code)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 text-xs font-bold transition-colors"
                >
                  {copiedCode === coupon.code ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Featured Deals Products */}
      <div className="space-y-6 pt-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Limited Time</span>
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">
            Flash Sale Items
          </h2>
          <p className="text-xs text-slate-500">Deep discounts on high-demand fresh items</p>
        </div>

        <ProductGrid products={deals} isLoading={loading} />
      </div>
    </div>
  );
}
