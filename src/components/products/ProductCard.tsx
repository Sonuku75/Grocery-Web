"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Heart, Plus, Minus } from "lucide-react";
import { Product } from "@/types";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { Rating } from "@/components/common/Rating";
import { formatCurrency } from "@/lib/utils";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const { cart, addToCart, updateQuantity, getItemQuantity } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();

  const quantity = getItemQuantity(product.id);
  const isWished = isInWishlist(product.id);

  const productUrl = `/products/${product.slug || product.id}`;
  const displayImage =
    (product.images && product.images.length > 0 && product.images[0]) ||
    product.imageUrl ||
    "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800";

  const discount = product.discountPercentage ?? product.discountPercent ?? 0;
  const price = product.price;
  const originalPrice = product.originalPrice ?? product.mrp ?? price;

  const handleAdd = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    addToCart(product, 1);
  };

  const handleIncrease = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const cartItem = cart.items.find((i) => i.productId === product.id);
    if (cartItem) {
      updateQuantity(cartItem.id, quantity + 1);
    } else {
      addToCart(product, 1);
    }
  };

  const handleDecrease = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const cartItem = cart.items.find((i) => i.productId === product.id);
    if (cartItem) {
      updateQuantity(cartItem.id, quantity - 1);
    }
  };

  const handleWishlistToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleWishlist(product);
  };

  return (
    <div className="group relative flex flex-col rounded-3xl bg-white border border-slate-100/80 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-300 overflow-hidden motion-reduce:transition-none motion-reduce:hover:translate-y-0">
      {/* Top badges & Wishlist */}
      <div className="absolute top-2.5 left-2.5 right-2.5 z-10 flex items-center justify-between pointer-events-none">
        {discount > 0 ? (
          <span className="bg-emerald-600 text-white text-[10px] font-extrabold px-2 py-0.5 rounded-lg shadow-xs uppercase tracking-wider">
            {discount}% OFF
          </span>
        ) : (
          <span />
        )}

        <button
          onClick={handleWishlistToggle}
          type="button"
          className="pointer-events-auto w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 backdrop-blur-xs border border-slate-100 flex items-center justify-center text-slate-400 hover:text-rose-500 hover:scale-105 active:scale-95 transition-all shadow-xs"
          title={isWished ? "Remove from wishlist" : "Add to wishlist"}
          aria-label={isWished ? "Remove from wishlist" : "Add to wishlist"}
        >
          <Heart
            className={`w-3.5 h-3.5 sm:w-4 sm:h-4 transition-colors ${
              isWished ? "fill-rose-500 text-rose-500" : ""
            }`}
          />
        </button>
      </div>

      {/* Product Image */}
      <Link
        href={productUrl}
        className="relative block w-full pt-[85%] bg-slate-50/50 overflow-hidden cursor-pointer"
      >
        <Image
          src={displayImage}
          alt={product.name}
          fill
          className="object-cover object-center group-hover:scale-105 transition-transform duration-500 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
        />
      </Link>

      {/* Content */}
      <div className="flex-1 flex flex-col p-3 sm:p-4">
        {/* Brand & Unit */}
        <div className="flex items-center justify-between text-[10px] sm:text-[11px] text-slate-400 font-medium mb-1 gap-1">
          <span className="truncate max-w-[100px] sm:max-w-[120px]">{product.brand}</span>
          <span className="shrink-0 bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-md text-[9px] sm:text-[10px] font-semibold">
            {product.unit}
          </span>
        </div>

        {/* Title */}
        <Link
          href={productUrl}
          className="text-xs sm:text-sm font-semibold text-slate-800 hover:text-brand-600 transition-colors line-clamp-2 leading-snug mb-1.5 min-h-[2rem] sm:min-h-[2.5rem]"
        >
          {product.name}
        </Link>

        {/* Rating */}
        <div className="mb-2.5 sm:mb-3">
          <Rating rating={product.rating} count={product.ratingCount} size="sm" />
        </div>

        {/* Price & Quantity / Add Button */}
        <div className="mt-auto pt-2 border-t border-slate-100 flex items-center justify-between gap-1.5 sm:gap-2">
          <div className="min-w-0">
            <div className="flex items-baseline gap-1 sm:gap-1.5 flex-wrap">
              <span className="text-sm sm:text-base font-extrabold text-slate-900">
                {formatCurrency(price)}
              </span>
              {originalPrice > price && (
                <span className="text-[10px] sm:text-xs text-slate-400 line-through">
                  {formatCurrency(originalPrice)}
                </span>
              )}
            </div>
            <span className="text-[9px] sm:text-[10px] text-emerald-600 font-semibold block">
              In Stock
            </span>
          </div>

          {/* Cart Control */}
          {quantity === 0 ? (
            <button
              onClick={handleAdd}
              type="button"
              className="h-7 sm:h-8 px-2.5 sm:px-3 rounded-xl bg-brand-50 hover:bg-brand-600 text-brand-700 hover:text-white border border-brand-200 hover:border-brand-600 text-xs font-bold transition-all flex items-center gap-1 active:scale-95 shadow-xs shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          ) : (
            <div className="flex items-center rounded-xl bg-brand-600 text-white p-0.5 shadow-sm shrink-0">
              <button
                onClick={handleDecrease}
                type="button"
                className="w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center rounded-lg hover:bg-brand-700 active:scale-90 transition-all"
                aria-label="Decrease quantity"
              >
                <Minus className="w-3 h-3" />
              </button>
              <span className="w-5 sm:w-6 text-center text-xs font-extrabold select-none">
                {quantity}
              </span>
              <button
                onClick={handleIncrease}
                type="button"
                className="w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center rounded-lg hover:bg-brand-700 active:scale-90 transition-all"
                aria-label="Increase quantity"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
