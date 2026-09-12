"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { QuantitySelector } from "@/components/common/QuantitySelector";
import { Button } from "@/components/common/Button";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { EmptyState } from "@/components/common/EmptyState";
import { formatCurrency } from "@/lib/utils";
import {
  ShoppingBag,
  Trash2,
  Heart,
  ArrowRight,
  Truck,
  Tag,
  CheckCircle2,
  ShieldCheck,
  X,
} from "lucide-react";

export default function CartPage() {
  const router = useRouter();
  const {
    cart,
    updateQuantity,
    removeFromCart,
    applyCoupon,
    removeCoupon,
  } = useCart();
  const { toggleWishlist } = useWishlist();

  const [couponCode, setCouponCode] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);

  const freeDeliveryThreshold = 35;
  const remainingForFreeDelivery = Math.max(0, freeDeliveryThreshold - cart.subtotal);
  const progressPercent = Math.min(100, (cart.subtotal / freeDeliveryThreshold) * 100);

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    try {
      await applyCoupon(couponCode);
      setCouponCode("");
    } finally {
      setCouponLoading(false);
    }
  };

  const handleSaveForLater = (product: (typeof cart.items)[0]["product"], itemId: string) => {
    toggleWishlist(product);
    removeFromCart(itemId);
  };

  if (cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <Breadcrumb items={[{ label: "Shopping Cart" }]} />
        <div className="py-12">
          <EmptyState
            icon={<ShoppingBag className="w-10 h-10" />}
            title="Your Cart is Empty"
            description="Looks like you haven't added any fresh groceries yet. Explore farm produce, dairy, and bakery treats."
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

      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Shopping Cart
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {cart.itemCount} {cart.itemCount === 1 ? "item" : "items"} selected for delivery
          </p>
        </div>
        <Link
          href="/products"
          className="text-xs font-bold text-brand-600 hover:text-brand-700 hidden sm:inline"
        >
          + Add more items
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Cart Items List */}
        <div className="lg:col-span-8 space-y-4">
          {/* Free delivery bar */}
          <div className="p-4 rounded-2xl bg-brand-50/70 border border-brand-100">
            <div className="flex items-center justify-between text-xs font-bold text-brand-900 mb-2">
              <span className="flex items-center gap-1.5">
                <Truck className="w-4 h-4 text-brand-600" />
                {remainingForFreeDelivery === 0 ? (
                  <span>Congratulations! You qualify for FREE 15-min delivery. 🎉</span>
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
            {cart.items.map((item) => (
              <div
                key={item.id}
                className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50/40 transition-colors"
              >
                <div className="flex items-center gap-4 min-w-0 flex-1">
                  <div className="relative w-20 h-20 rounded-2xl overflow-hidden bg-slate-50 border border-slate-100 shrink-0">
                    <Image
                      src={item.product.images[0]}
                      alt={item.product.name}
                      fill
                      className="object-cover"
                      sizes="80px"
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      {item.product.brand}
                    </span>
                    <Link
                      href={`/products/${item.product.slug || item.product.id}`}
                      className="block text-sm font-bold text-slate-900 hover:text-brand-600 transition-colors truncate"
                    >
                      {item.product.name}
                    </Link>
                    <span className="text-xs text-slate-500 block mt-0.5">
                      {item.product.unit} • {formatCurrency(item.product.price)} each
                    </span>

                    {/* Actions on mobile/desktop */}
                    <div className="flex items-center gap-3 mt-2">
                      <button
                        onClick={() => handleSaveForLater(item.product, item.id)}
                        className="text-[11px] font-semibold text-slate-500 hover:text-brand-600 flex items-center gap-1 transition-colors"
                      >
                        <Heart className="w-3.5 h-3.5" />
                        <span>Save for Later</span>
                      </button>
                      <span className="text-slate-200">•</span>
                      <button
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
                    {formatCurrency(item.product.price * item.quantity)}
                  </span>
                  <QuantitySelector
                    quantity={item.quantity}
                    onIncrease={() => updateQuantity(item.id, item.quantity + 1)}
                    onDecrease={() => updateQuantity(item.id, item.quantity - 1)}
                    size="sm"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Order Summary Card */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-5">
            <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
              Order Summary
            </h2>

            {/* Coupon Code Input */}
            <div>
              {cart.appliedCoupon ? (
                <div className="p-3 rounded-2xl bg-brand-50 border border-brand-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Tag className="w-4 h-4 text-brand-600" />
                    <div>
                      <span className="text-xs font-bold text-brand-800 uppercase">
                        {cart.appliedCoupon.code} applied
                      </span>
                      <p className="text-[10px] text-brand-600">
                        {cart.appliedCoupon.description}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={removeCoupon}
                    className="p-1 text-slate-400 hover:text-rose-500"
                    aria-label="Remove coupon"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <form onSubmit={handleApplyCoupon} className="flex gap-2">
                  <input
                    type="text"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    placeholder="Coupon code (e.g. CARTIFY50)"
                    className="flex-1 px-3 py-2 text-xs uppercase font-semibold rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:border-brand-500"
                  />
                  <Button
                    type="submit"
                    variant="outline"
                    size="sm"
                    isLoading={couponLoading}
                  >
                    Apply
                  </Button>
                </form>
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
                <span>Estimated Taxes (7%)</span>
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
