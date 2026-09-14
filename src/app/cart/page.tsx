"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { useToast } from "@/context/ToastContext";
import { QuantitySelector } from "@/components/common/QuantitySelector";
import { Button } from "@/components/common/Button";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { EmptyState } from "@/components/common/EmptyState";
import { formatCurrency } from "@/lib/utils";
import { couponService } from "@/services/couponService";
import { Coupon } from "@/types";
import {
  ShoppingBag,
  Trash2,
  Heart,
  ArrowRight,
  Truck,
  Tag,
  ShieldCheck,
  X,
  AlertTriangle,
  Check,
  Sparkles,
} from "lucide-react";

export default function CartPage() {
  const router = useRouter();
  const {
    cart,
    loading,
    updateQuantity,
    removeFromCart,
    clearCart,
    applyCoupon,
    removeCoupon,
  } = useCart();
  const { toggleWishlist } = useWishlist();
  const { showToast } = useToast();

  const [couponCode, setCouponCode] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [availableCoupons, setAvailableCoupons] = useState<Coupon[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function fetchOffers() {
      try {
        const offers = await couponService.getAvailableCoupons();
        if (isMounted) setAvailableCoupons(offers);
      } catch (err) {
        console.warn("Failed to load available coupons", err);
      }
    }
    fetchOffers();
    return () => {
      isMounted = false;
    };
  }, []);

  const freeDeliveryThreshold = 500;
  const remainingForFreeDelivery = Math.max(0, freeDeliveryThreshold - cart.subtotal);
  const progressPercent = Math.min(100, (cart.subtotal / freeDeliveryThreshold) * 100);

  const handleApplyCoupon = async (e?: React.FormEvent, codeToApply?: string) => {
    if (e) e.preventDefault();
    const code = (codeToApply || couponCode).trim();
    if (!code) return;
    setCouponLoading(true);
    try {
      const res = await applyCoupon(code);
      if (res.success) {
        showToast(res.message, "success");
        setCouponCode("");
      } else {
        showToast(res.message, "error");
      }
    } catch (err: any) {
      showToast(err?.message || "Failed to apply coupon.", "error");
    } finally {
      setCouponLoading(false);
    }
  };

  const handleRemoveCoupon = async () => {
    await removeCoupon();
    showToast("Coupon removed from cart.", "info");
  };

  const handleSaveForLater = (product: any, itemId: string) => {
    toggleWishlist(product);
    removeFromCart(itemId);
  };

  if (loading && cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        <div className="h-4 w-40 bg-slate-200 rounded-md" />
        <div className="h-10 w-64 bg-slate-200 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-28 bg-slate-100 rounded-3xl" />
            ))}
          </div>
          <div className="lg:col-span-4 h-80 bg-slate-100 rounded-3xl" />
        </div>
      </div>
    );
  }

  if (cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <Breadcrumb items={[{ label: "Shopping Cart" }]} />
        <div className="py-12">
          <EmptyState
            icon={<ShoppingBag className="w-10 h-10" />}
            title="Your Cart is Empty"
            description="Looks like you haven't added any fresh groceries yet. Explore farm produce, dairy, snacks, and daily essentials."
            actionText="Start Shopping"
            actionHref="/products"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb items={[{ label: "Shopping Cart" }]} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Shopping Cart
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {cart.itemCount} {cart.itemCount === 1 ? "item" : "items"} selected for delivery
          </p>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            className="text-xs font-bold text-rose-600 hover:text-rose-700 transition-colors flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Cart</span>
          </button>
          <span className="text-slate-200 hidden sm:inline">•</span>
          <Link
            href="/products"
            className="text-xs font-bold text-brand-600 hover:text-brand-700 hidden sm:inline"
          >
            + Add more items
          </Link>
        </div>
      </div>

      {/* Clear Cart Confirmation Dialog */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl border border-slate-100 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Clear Shopping Cart?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to remove all items from your cart? This action cannot be undone.
              </p>
            </div>
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowClearConfirm(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="bg-rose-600 hover:bg-rose-700 text-white"
                onClick={async () => {
                  await clearCart();
                  setShowClearConfirm(false);
                }}
              >
                Yes, Clear All
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Cart Items List */}
        <div className="lg:col-span-8 space-y-4">
          {/* Free delivery bar */}
          <div className="p-4 rounded-2xl bg-brand-50/70 border border-brand-100">
            <div className="flex items-center justify-between text-xs font-bold text-brand-900 mb-2">
              <span className="flex items-center gap-1.5">
                <Truck className="w-4 h-4 text-brand-600" />
                {remainingForFreeDelivery === 0 ? (
                  <span>Congratulations! You qualify for FREE Delivery. 🎉</span>
                ) : (
                  <span>
                    Add <strong>{formatCurrency(remainingForFreeDelivery)}</strong> more to get FREE Delivery
                  </span>
                )}
              </span>
              <span>{Math.round(progressPercent)}%</span>
            </div>
            <div className="w-full bg-slate-200/80 h-2 rounded-full overflow-hidden">
              <div
                className="bg-brand-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Items Card List */}
          <div className="rounded-3xl bg-white border border-slate-100 shadow-card divide-y divide-slate-100 overflow-hidden">
            {cart.items.map((item) => {
              const productObj = (item.product || {}) as any;
              const title = productObj.title || productObj.name || "Grocery Item";
              const brand = productObj.brand || "Cartify";
              const unit = item.variant?.unit || productObj.unit || "1 pc";
              const unitPrice = item.unitPrice ?? item.variant?.price ?? productObj.price ?? 0;
              const rowTotal = item.lineTotal ?? unitPrice * item.quantity;
              const itemImage =
                (productObj.images && productObj.images.length > 0 && productObj.images[0]) ||
                productObj.thumbnailUrl ||
                productObj.thumbnail_url ||
                productObj.imageUrl ||
                productObj.image_url ||
                "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800";

              return (
                <div
                  key={item.id}
                  className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50/40 transition-colors"
                >
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="relative w-20 h-20 rounded-2xl overflow-hidden bg-slate-50 border border-slate-100 shrink-0">
                      <Image
                        src={itemImage}
                        alt={title}
                        fill
                        className="object-cover"
                        sizes="80px"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        {brand}
                      </span>
                      <Link
                        href={`/products/${productObj.slug || productObj.id}`}
                        className="block text-sm font-bold text-slate-900 hover:text-brand-600 transition-colors truncate"
                      >
                        {title}
                      </Link>
                      <span className="text-xs text-slate-500 block mt-0.5">
                        {unit} • {formatCurrency(unitPrice)} each
                      </span>

                      {/* Actions */}
                      <div className="flex items-center gap-3 mt-2">
                        <button
                          type="button"
                          onClick={() => handleSaveForLater(productObj, item.id)}
                          className="text-[11px] font-semibold text-slate-500 hover:text-brand-600 flex items-center gap-1 transition-colors"
                        >
                          <Heart className="w-3.5 h-3.5" />
                          <span>Save for Later</span>
                        </button>
                        <span className="text-slate-200">•</span>
                        <button
                          type="button"
                          onClick={() => removeFromCart(item.id)}
                          className="text-[11px] font-semibold text-slate-400 hover:text-rose-600 flex items-center gap-1 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Remove</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Quantity & Row Total */}
                  <div className="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto gap-3 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                    <span className="text-base font-black text-slate-900">
                      {formatCurrency(rowTotal)}
                    </span>
                    {(() => {
                      const stock = item.variant?.stockQuantity ?? item.variant?.stock_quantity ?? 99;
                      const isOutOfStock = stock <= 0;
                      const isLowStock = stock > 0 && stock <= 5;
                      return (
                        <div className="flex flex-col items-end gap-1">
                          <QuantitySelector
                            quantity={item.quantity}
                            min={1}
                            max={Math.max(1, stock)}
                            onIncrease={() => updateQuantity(item.id, item.quantity + 1)}
                            onDecrease={() => updateQuantity(item.id, item.quantity - 1)}
                            size="sm"
                          />
                          {isOutOfStock ? (
                            <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded">
                              Out of Stock
                            </span>
                          ) : isLowStock ? (
                            <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                              Only {stock} left
                            </span>
                          ) : null}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Order Summary Card */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-5">
            <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
              Order Summary
            </h2>

            {/* Coupon Code Input & Available Offers */}
            <div className="space-y-3">
              {cart.appliedCoupon ? (
                <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200/80 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700 shrink-0">
                      <Tag className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-black text-emerald-900 uppercase">
                          {cart.appliedCoupon.code}
                        </span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-200/70 text-emerald-800">
                          Applied
                        </span>
                      </div>
                      <p className="text-[11px] text-emerald-700 font-medium">
                        Saving {formatCurrency(cart.discount)} on this order
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleRemoveCoupon}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    aria-label="Remove coupon"
                    title="Remove coupon"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <form onSubmit={(e) => handleApplyCoupon(e)} className="flex gap-2">
                  <input
                    type="text"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    placeholder="Enter promo code (e.g. SAVE20)"
                    className="flex-1 px-3.5 py-2 text-xs uppercase font-bold tracking-wider rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:border-brand-500 transition-colors"
                  />
                  <Button
                    type="submit"
                    variant="outline"
                    size="sm"
                    isLoading={couponLoading}
                    disabled={!couponCode.trim() || couponLoading}
                  >
                    Apply
                  </Button>
                </form>
              )}

              {/* Quick-Apply Available Offers */}
              {!cart.appliedCoupon && availableCoupons.length > 0 && (
                <div className="space-y-2 pt-1 border-t border-slate-100">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      Available Offers
                    </span>
                    <Link
                      href="/offers"
                      className="text-[11px] font-bold text-brand-600 hover:text-brand-700 transition-colors"
                    >
                      View All
                    </Link>
                  </div>
                  <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                    {availableCoupons.slice(0, 3).map((coup) => {
                      const minVal = coup.minOrderAmount || coup.minimumOrderValue || 0;
                      const isEligible = cart.subtotal >= minVal;
                      return (
                        <div
                          key={coup.id}
                          className="p-2.5 rounded-xl border border-dashed border-slate-200 hover:border-brand-300 bg-slate-50/60 flex items-center justify-between gap-2 transition-colors"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs font-black text-slate-900 tracking-wide">
                                {coup.code}
                              </span>
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                                {coup.discountType === "percent" || coup.discountType === "PERCENTAGE"
                                  ? `${coup.discountValue}% OFF`
                                  : `₹${coup.discountValue} OFF`}
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-500 truncate mt-0.5">
                              {minVal > 0 ? `On orders above ₹${minVal}` : "No minimum order"}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleApplyCoupon(undefined, coup.code)}
                            disabled={couponLoading}
                            className={`px-2.5 py-1 text-[11px] font-bold rounded-lg transition-colors shrink-0 ${
                              isEligible
                                ? "bg-brand-600 hover:bg-brand-700 text-white shadow-xs"
                                : "bg-slate-200 text-slate-500 hover:bg-slate-300"
                            }`}
                          >
                            Apply
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Calculations Breakdown */}
            <div className="space-y-2.5 text-xs text-slate-600 pt-2 border-t border-slate-100">
              <div className="flex justify-between">
                <span>Items Subtotal</span>
                <span className="font-bold text-slate-900">{formatCurrency(cart.subtotal)}</span>
              </div>

              {cart.discount > 0 && (
                <div className="flex justify-between text-brand-600 font-bold">
                  <span>Coupon Discount</span>
                  <span>-{formatCurrency(cart.discount)}</span>
                </div>
              )}

              <div className="flex justify-between">
                <span>Delivery Fee</span>
                <span>
                  {cart.deliveryFee === 0 ? (
                    <strong className="text-brand-600 font-bold">FREE</strong>
                  ) : (
                    formatCurrency(cart.deliveryFee)
                  )}
                </span>
              </div>

              <div className="flex justify-between">
                <span>Estimated Taxes</span>
                <span>{formatCurrency(cart.tax)}</span>
              </div>

              <div className="flex justify-between pt-3 border-t border-slate-200 text-base font-black text-slate-900">
                <span>Total Amount</span>
                <span>{formatCurrency(cart.total)}</span>
              </div>
            </div>

            {/* Checkout CTA */}
            <Button
              variant="primary"
              size="lg"
              fullWidth
              rightIcon={<ArrowRight className="w-4 h-4" />}
              onClick={() => router.push("/checkout")}
            >
              Proceed to Checkout
            </Button>

            {/* Guarantee note */}
            <div className="pt-2 text-center text-[11px] text-slate-400 flex items-center justify-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Safe & Encrypted Checkout</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
