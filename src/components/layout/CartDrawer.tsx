"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { X, ShoppingBag, ArrowRight, Trash2, Truck, Tag } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { Button } from "@/components/common/Button";
import { QuantitySelector } from "@/components/common/QuantitySelector";
import { formatCurrency } from "@/lib/utils";

export function CartDrawer() {
  const {
    cart,
    isCartDrawerOpen,
    setIsCartDrawerOpen,
    updateQuantity,
    removeFromCart,
  } = useCart();

  if (!isCartDrawerOpen) return null;

  const freeDeliveryThreshold = 500;
  const remainingForFreeDelivery = Math.max(0, freeDeliveryThreshold - cart.subtotal);
  const progressPercent = Math.min(100, (cart.subtotal / freeDeliveryThreshold) * 100);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 overflow-hidden"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-fade-in"
        onClick={() => setIsCartDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col animate-slide-in-right">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-white">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
                <ShoppingBag className="w-4 h-4" />
              </div>
              <h2 className="text-base font-bold text-slate-800">
                My Cart ({cart.itemCount} {cart.itemCount === 1 ? "item" : "items"})
              </h2>
            </div>
            <button
              onClick={() => setIsCartDrawerOpen(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Close cart"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Free delivery bar */}
          <div className="bg-brand-50/60 px-5 py-3 border-b border-brand-100/60">
            <div className="flex items-center justify-between text-xs font-semibold text-brand-900 mb-1.5">
              <span className="flex items-center gap-1.5">
                <Truck className="w-3.5 h-3.5 text-brand-600" />
                {remainingForFreeDelivery === 0 ? (
                  <span className="text-brand-700 font-bold">You unlocked FREE Delivery! 🎉</span>
                ) : (
                  <span>
                    Add <strong className="text-brand-700">{formatCurrency(remainingForFreeDelivery)}</strong> more for FREE delivery
                  </span>
                )}
              </span>
              <span className="text-slate-500 font-medium">{Math.round(progressPercent)}%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-brand-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Cart Items List */}
          <div className="flex-1 overflow-y-auto px-5 py-4 divide-y divide-slate-100">
            {cart.items.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
                  <ShoppingBag className="w-8 h-8" />
                </div>
                <h3 className="text-base font-bold text-slate-800 mb-1">Your cart is empty</h3>
                <p className="text-xs text-slate-500 max-w-xs mb-6">
                  Explore fresh organic produce, breakfast essentials, and pantry staples.
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsCartDrawerOpen(false)}
                >
                  Start Shopping
                </Button>
              </div>
            ) : (
              cart.items.map((item) => {
                const productObj = (item.product || {}) as any;
                const title = productObj.title || productObj.name || "Grocery Item";
                const unit = item.variant?.unit || productObj.unit || "1 unit";
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
                  <div key={item.id} className="py-3.5 flex gap-3.5 items-center">
                    <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-slate-50 border border-slate-100 shrink-0">
                      <Image
                        src={itemImage}
                        alt={title}
                        fill
                        className="object-cover"
                        sizes="64px"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-slate-800 truncate">
                        {title}
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">{unit}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs font-bold text-slate-900">
                          {formatCurrency(rowTotal)}
                        </span>
                        <QuantitySelector
                          quantity={item.quantity}
                          min={1}
                          max={99}
                          onIncrease={() => updateQuantity(item.id, item.quantity + 1)}
                          onDecrease={() => updateQuantity(item.id, item.quantity - 1)}
                          size="sm"
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => removeFromCart(item.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-500 transition-colors"
                      title="Remove item"
                      aria-label="Remove item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Totals & Checkout Button */}
          {cart.items.length > 0 && (
            <div className="p-5 border-t border-slate-100 bg-slate-50/50 space-y-3">
              <div className="space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span className="font-semibold text-slate-900">{formatCurrency(cart.subtotal)}</span>
                </div>
                {cart.appliedCoupon && (
                  <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 text-[11px] font-semibold">
                    <span className="flex items-center gap-1.5">
                      <Tag className="w-3 h-3 text-emerald-600" />
                      <span>{cart.appliedCoupon.code} applied</span>
                    </span>
                    <span>-{formatCurrency(cart.discount)}</span>
                  </div>
                )}
                {cart.discount > 0 && !cart.appliedCoupon && (
                  <div className="flex justify-between text-emerald-600 font-semibold">
                    <span>Discount</span>
                    <span>-{formatCurrency(cart.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Delivery</span>
                  <span>{cart.deliveryFee === 0 ? <strong className="text-brand-600">FREE</strong> : formatCurrency(cart.deliveryFee)}</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-200/80 text-sm font-bold text-slate-900">
                  <span>Total Amount</span>
                  <span>{formatCurrency(cart.total)}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  href="/cart"
                  onClick={() => setIsCartDrawerOpen(false)}
                  className="w-full"
                >
                  <Button variant="outline" size="md" fullWidth>
                    View Cart
                  </Button>
                </Link>
                <Link
                  href="/checkout"
                  onClick={() => setIsCartDrawerOpen(false)}
                  className="w-full"
                >
                  <Button
                    variant="primary"
                    size="md"
                    fullWidth
                    rightIcon={<ArrowRight className="w-4 h-4" />}
                  >
                    Checkout
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
