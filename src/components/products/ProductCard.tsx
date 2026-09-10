"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Heart, Plus, Minus, Check } from "lucide-react";
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
    <div className="group relative flex flex-col rounded-2xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover transition-all duration-200 overflow-hidden">
      {/* Top badges & Wishlist */}
      <div className="absolute top-2.5 left-2.5 right-2.5 z-10 flex items-center justify-between pointer-events-none">
        {product.discountPercent > 0 ? (
          <span className="bg-accent-500 text-white text-[10px] font-extrabold px-2 py-0.5 rounded-lg shadow-xs uppercase tracking-wider">
            {product.discountPercent}% OFF
          </span>
        ) : (
          <span />
        )}

        <button
          onClick={handleWishlistToggle}
          className="pointer-events-auto w-8 h-8 rounded-full bg-white/90 backdrop-blur-xs border border-slate-100 flex items-center justify-center text-slate-400 hover:text-rose-500 hover:scale-105 transition-all shadow-xs"
          title={isWished ? "Remove from wishlist" : "Add to wishlist"}
          aria-label={isWished ? "Remove from wishlist" : "Add to wishlist"}
        >
          <Heart
            className={`w-4 h-4 ${
              isWished ? "fill-rose-500 text-rose-500" : ""
            }`}
          />
        </button>
      </div>

      {/* Product Image */}
      <Link
        href={`/products/${product.id}`}
        className="relative block w-full pt-[85%] bg-slate-50/50 overflow-hidden cursor-pointer"
      >
        <Image
          src={product.images[0]}
          alt={product.name}
          fill
          className="object-cover object-center group-hover:scale-105 transition-transform duration-300"
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
        />
      </Link>

      {/* Content */}
      <div className="flex-1 flex flex-col p-3.5 sm:p-4">
        {/* Brand & Unit */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium mb-1">
          <span className="truncate max-w-[120px]">{product.brand}</span>
          <span className="shrink-0 bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-md text-[10px] font-semibold">
            {product.unit}
          </span>
        </div>

        {/* Title */}
        <Link
          href={`/products/${product.id}`}
          className="text-sm font-semibold text-slate-800 hover:text-brand-600 transition-colors line-clamp-2 leading-snug mb-1.5"
        >
          {product.name}
        </Link>

        {/* Rating */}
        <div className="mb-3">
          <Rating rating={product.rating} count={product.ratingCount} size="sm" />
        </div>

        {/* Price & Quantity / Add Button */}
        <div className="mt-auto pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-base font-bold text-slate-900">
                {formatCurrency(product.price)}
              </span>
              {product.originalPrice > product.price && (
                <span className="text-xs text-slate-400 line-through">
                  {formatCurrency(product.originalPrice)}
                </span>
              )}
            </div>
            <span className="text-[10px] text-emerald-600 font-semibold block">
              In Stock
            </span>
          </div>

          {/* Cart Control */}
          {quantity === 0 ? (
            <button
              onClick={handleAdd}
              className="h-8 px-3 rounded-xl bg-brand-50 hover:bg-brand-600 text-brand-700 hover:text-white border border-brand-200 hover:border-brand-600 text-xs font-bold transition-all flex items-center gap-1 active:scale-95 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          ) : (
            <div className="flex items-center rounded-xl bg-brand-600 text-white p-0.5 shadow-sm">
              <button
                onClick={handleDecrease}
                className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-brand-700 active:scale-90 transition-all"
                aria-label="Decrease quantity"
              >
                <Minus className="w-3 h-3" />
              </button>
              <span className="w-6 text-center text-xs font-extrabold select-none">
                {quantity}
              </span>
              <button
                onClick={handleIncrease}
                className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-brand-700 active:scale-90 transition-all"
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
