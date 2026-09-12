"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { useWishlist } from "@/context/WishlistContext";
import { useCart } from "@/context/CartContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { Rating } from "@/components/common/Rating";
import { formatCurrency } from "@/lib/utils";
import { Heart, ShoppingBag, Trash2, ArrowRight } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function WishlistPage() {
  const { wishlistProducts, removeFromWishlist } = useWishlist();
  const { addToCart } = useCart();
  const { showToast } = useToast();

  const handleMoveToCart = (product: (typeof wishlistProducts)[0]) => {
    addToCart(product, 1);
    removeFromWishlist(product.id);
    showToast(`Moved ${product.name} to Cart`, "success");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Breadcrumb items={[{ label: "My Wishlist" }]} />

      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Saved Favorites ({wishlistProducts.length})
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Keep track of your favorite organic groceries and recurring pantry items.
          </p>
        </div>
      </div>

      {wishlistProducts.length === 0 ? (
        <EmptyState
          icon={<Heart className="w-10 h-10 text-rose-500" />}
          title="Your Wishlist is Empty"
          description="Explore our produce, bakery, and dairy items. Tap the heart icon to save products for later."
          actionText="Explore Products"
          actionHref="/products"
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {wishlistProducts.map((product) => (
            <div
              key={product.id}
              className="group flex flex-col rounded-3xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover overflow-hidden transition-all duration-200"
            >
              <div className="relative pt-[85%] bg-slate-50">
                <Image
                  src={product.images[0]}
                  alt={product.name}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <button
                  onClick={() => removeFromWishlist(product.id)}
                  className="absolute top-2.5 right-2.5 p-2 rounded-full bg-white/90 backdrop-blur-xs text-slate-400 hover:text-rose-600 shadow-xs transition-colors"
                  title="Remove from wishlist"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {product.brand}
                  </span>
                  <Link
                    href={`/products/${product.slug || product.id}`}
                    className="block text-xs sm:text-sm font-bold text-slate-800 hover:text-brand-600 transition-colors line-clamp-2 mt-0.5"
                  >
                    {product.name}
                  </Link>
                  <div className="mt-1.5">
                    <Rating rating={product.rating} count={product.ratingCount} size="sm" />
                  </div>
                </div>

                <div>
                  <div className="flex items-baseline gap-2 mb-3">
                    <span className="text-base font-black text-slate-900">
                      {formatCurrency(product.price)}
                    </span>
                    {product.originalPrice > product.price && (
                      <span className="text-xs text-slate-400 line-through">
                        {formatCurrency(product.originalPrice)}
                      </span>
                    )}
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    fullWidth
                    leftIcon={<ShoppingBag className="w-3.5 h-3.5" />}
                    onClick={() => handleMoveToCart(product)}
                  >
                    Move to Cart
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
