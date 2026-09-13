"use client";

import React from "react";
import Link from "next/link";
import { useWishlist } from "@/context/WishlistContext";
import { useAuth } from "@/context/AuthContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { ProductCard } from "@/components/products/ProductCard";
import { Heart, Lock, ArrowRight, Sparkles } from "lucide-react";

export default function WishlistPage() {
  const { wishlistProducts, count, loading } = useWishlist();
  const { isAuthenticated, loading: authLoading } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Navigation Breadcrumb */}
        <Breadcrumb items={[{ label: "My Wishlist" }]} />

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-2xl bg-rose-50 border border-rose-100/80 flex items-center justify-center text-rose-500 shadow-xs">
                <Heart className="w-5 h-5 fill-rose-500" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                My Saved Favorites
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Organize your everyday pantry staples, fresh produce, and organic groceries in one place.
            </p>
          </div>

          {isAuthenticated && !loading && (
            <div className="flex items-center gap-2 self-start sm:self-center">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200/80 shadow-2xs text-xs font-bold text-slate-700">
                <Sparkles className="w-3.5 h-3.5 text-rose-500" />
                {count} {count === 1 ? "Product" : "Products"} Saved
              </span>
            </div>
          )}
        </div>

        {/* Unauthenticated State */}
        {!authLoading && !isAuthenticated ? (
          <div className="py-12 px-4 sm:px-6 max-w-xl mx-auto text-center space-y-6 bg-white rounded-3xl border border-slate-100 shadow-card">
            <div className="w-16 h-16 rounded-3xl bg-slate-100 flex items-center justify-center mx-auto text-slate-700 shadow-xs">
              <Lock className="w-7 h-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Sign In to View Your Wishlist
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
                Your wishlist is saved privately to your account. Sign in to access your saved items
                across your phone, tablet, and computer.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <Link href="/login?redirect=/wishlist" className="w-full sm:w-auto">
                <Button variant="primary" size="md" fullWidth rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Sign In to Cartify
                </Button>
              </Link>
              <Link href="/products" className="w-full sm:w-auto">
                <Button variant="outline" size="md" fullWidth>
                  Browse Catalog
                </Button>
              </Link>
            </div>
          </div>
        ) : loading ? (
          /* Loading Skeletons Grid */
          <div
            aria-busy="true"
            aria-label="Loading saved wishlist items"
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3.5 sm:gap-6"
          >
            {Array.from({ length: 8 }).map((_, idx) => (
              <div
                key={idx}
                className="flex flex-col rounded-3xl bg-white border border-slate-100 shadow-card p-3 space-y-3 animate-pulse"
              >
                <div className="pt-[85%] rounded-2xl bg-slate-100" />
                <div className="space-y-2 pt-1">
                  <div className="h-3 w-1/3 bg-slate-100 rounded-md" />
                  <div className="h-4 w-5/6 bg-slate-100 rounded-md" />
                  <div className="h-3 w-1/2 bg-slate-100 rounded-md" />
                </div>
                <div className="pt-2 flex items-center justify-between border-t border-slate-50">
                  <div className="h-5 w-16 bg-slate-100 rounded-md" />
                  <div className="h-8 w-8 bg-slate-100 rounded-xl" />
                </div>
              </div>
            ))}
          </div>
        ) : wishlistProducts.length === 0 ? (
          /* Empty State */
          <div className="py-8">
            <EmptyState
              icon={<Heart className="w-12 h-12 text-rose-500" />}
              title="Your Wishlist is Empty"
              description="Explore our farm-fresh produce, artisanal bakery, and dairy items. Tap the heart icon on any product to save it here for quick access."
              actionText="Explore Products"
              actionHref="/products"
            />
          </div>
        ) : (
          /* Wishlist Products Grid */
          <div className="space-y-6">
            <div
              className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3.5 sm:gap-6"
              role="region"
              aria-label="Saved products"
            >
              {wishlistProducts.map((product) => (
                <div
                  key={product.id}
                  className="transition-all duration-300 transform motion-reduce:transform-none"
                >
                  <ProductCard product={product} />
                </div>
              ))}
            </div>

            {/* Bottom Catalog Discovery Callout */}
            <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-50 to-emerald-50 border border-brand-100 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Looking for more organic essentials?
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Browse over 5,000 seasonal fruits, farm dairy, and pantry goods.
                </p>
              </div>
              <Link href="/products">
                <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                  Explore All Products
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
