"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  ShieldCheck,
  Truck,
  RotateCcw,
  CheckCircle2,
  Heart,
  Share2,
  Package,
  Layers,
  ShoppingBag,
  Plus,
  Minus,
} from "lucide-react";
import { Product, ProductVariant } from "@/types";
import { productService } from "@/services/productService";
import { ProductGallery } from "@/components/products/ProductGallery";
import { VariantSelector } from "@/components/products/VariantSelector";
import { Rating } from "@/components/common/Rating";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { ErrorState } from "@/components/common/ErrorState";
import { formatCurrency } from "@/lib/utils";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { useToast } from "@/context/ToastContext";

interface ProductSlugPageProps {
  params: Promise<{ slug: string }>;
}

export default function ProductSlugPage({ params }: ProductSlugPageProps) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;
  const router = useRouter();

  const [product, setProduct] = useState<Product | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"description" | "specifications">("description");

  const { isInWishlist, toggleWishlist } = useWishlist();
  const { cart, addToCart, updateQuantity, setIsCartDrawerOpen } = useCart();
  const { showToast } = useToast();

  useEffect(() => {
    async function loadProduct() {
      setLoading(true);
      setError(null);
      try {
        const prod = await productService.getProductBySlug(slug);
        if (prod) {
          setProduct(prod);
          // Set initial variant (primary variant or first variant)
          if (prod.variants && prod.variants.length > 0) {
            setSelectedVariant(prod.primaryVariant || prod.variants[0]);
          }
        } else {
          setError("The requested grocery item is not available or has been discontinued.");
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Unable to load product.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }

    loadProduct();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        <div className="h-4 w-48 bg-slate-200 rounded-md" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
          <div className="lg:col-span-6 aspect-square bg-slate-100 rounded-3xl" />
          <div className="lg:col-span-6 space-y-5">
            <div className="h-4 w-28 bg-slate-200 rounded-md" />
            <div className="h-8 w-3/4 bg-slate-200 rounded-lg" />
            <div className="h-5 w-32 bg-slate-200 rounded-md" />
            <div className="h-10 w-44 bg-slate-200 rounded-xl" />
            <div className="h-20 w-full bg-slate-100 rounded-2xl" />
            <div className="h-12 w-full bg-slate-200 rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20">
        <ErrorState
          title="Product Not Available"
          message={error || "We couldn't locate this grocery item in our catalog."}
          onRetry={() => router.push("/products")}
          retryLabel="Browse All Products"
        />
      </div>
    );
  }

  const isWished = isInWishlist(product.id);

  // Dynamic pricing based on selected variant
  const currentPrice = selectedVariant ? selectedVariant.price : product.price;
  const currentMrp = selectedVariant ? selectedVariant.mrp : (product.originalPrice ?? product.mrp ?? currentPrice);
  const currentDiscount = selectedVariant
    ? (selectedVariant.discountPercentage ?? selectedVariant.discount_percentage ?? 0)
    : (product.discountPercentage ?? product.discountPercent ?? 0);
  const currentUnit = selectedVariant
    ? `${selectedVariant.unitValue ?? selectedVariant.unit_value ?? ""} ${selectedVariant.unitType ?? selectedVariant.unit_type ?? ""}`.trim()
    : product.unit;

  const handleShare = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast("Link copied to clipboard!", "success");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8 animate-fade-in">
      {/* Breadcrumb Hierarchy */}
      <Breadcrumb
        items={[
          { label: "Products", href: "/products" },
          ...(product.categorySlug || product.category_slug
            ? [{ label: product.categoryName || product.category_name || "Category", href: `/categories/${product.categorySlug || product.category_slug}` }]
            : []),
          { label: product.name },
        ]}
      />

      {/* Main Two-Column Layout (Gallery on Left, Actions on Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
        {/* Left: Responsive Image Gallery */}
        <div className="lg:col-span-7">
          <ProductGallery
            images={product.images}
            productName={product.name}
          />
        </div>

        {/* Right: Product Purchase & Specification Panel */}
        <div className="lg:col-span-5 flex flex-col space-y-6">
          {/* Header Metadata */}
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2.5 py-1 rounded-lg">
                {product.brand}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleShare}
                  aria-label="Share product"
                  className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 transition-colors"
                >
                  <Share2 className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => toggleWishlist(product)}
                  aria-label={isWished ? "Remove from wishlist" : "Add to wishlist"}
                  className={`w-8 h-8 rounded-full border flex items-center justify-center transition-all ${
                    isWished
                      ? "bg-rose-50 border-rose-200 text-rose-500"
                      : "bg-white border-slate-200 text-slate-400 hover:text-rose-500"
                  }`}
                >
                  <Heart className={`w-4 h-4 ${isWished ? "fill-rose-500" : ""}`} />
                </button>
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
              {product.name}
            </h1>

            {product.shortDescription && (
              <p className="text-xs sm:text-sm text-slate-500 mt-1.5 leading-relaxed">
                {product.shortDescription}
              </p>
            )}

            {/* Rating placeholder */}
            <div className="flex items-center gap-3 mt-3">
              <Rating rating={product.rating} count={product.ratingCount} size="md" />
              <span className="text-slate-300">|</span>
              <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Verified Genuine
              </span>
            </div>
          </div>

          {/* Pricing Block */}
          <div className="p-4 sm:p-5 rounded-3xl bg-slate-50 border border-slate-100 flex flex-col space-y-2">
            <div className="flex items-baseline gap-2.5 flex-wrap">
              <span className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                {formatCurrency(currentPrice)}
              </span>
              {currentMrp > currentPrice && (
                <span className="text-sm sm:text-base text-slate-400 line-through font-medium">
                  {formatCurrency(currentMrp)}
                </span>
              )}
              {currentDiscount > 0 && (
                <span className="bg-emerald-600 text-white text-xs font-black px-2.5 py-0.5 rounded-lg shadow-xs uppercase tracking-wider">
                  {currentDiscount}% OFF
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              Inclusive of all taxes. Standard unit: <span className="font-semibold text-slate-700">{currentUnit}</span>
            </p>
          </div>

          {/* Variant Selector */}
          {product.variants && product.variants.length > 0 && (
            <VariantSelector
              variants={product.variants}
              selectedVariant={selectedVariant}
              onSelectVariant={(v) => setSelectedVariant(v)}
            />
          )}

          {/* Live Add to Cart CTA + Wishlist Action */}
          {(() => {
            const cartItem = product
              ? cart.items.find((i) =>
                  selectedVariant ? i.variantId === selectedVariant.id : i.productId === product.id
                )
              : undefined;
            const cartQuantity = cartItem ? cartItem.quantity : 0;

            return (
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-3">
                  {cartQuantity === 0 ? (
                    <button
                      type="button"
                      onClick={() => product && addToCart(product, 1, selectedVariant || undefined)}
                      className="flex-1 py-3.5 px-6 rounded-2xl bg-brand-600 hover:bg-brand-700 active:scale-95 text-white font-bold text-sm sm:text-base shadow-sm transition-all flex items-center justify-center gap-2"
                    >
                      <ShoppingBag className="w-4 h-4" />
                      <span>Add to Cart</span>
                    </button>
                  ) : (
                    <div className="flex-1 flex items-center gap-3">
                      <div className="flex items-center rounded-2xl bg-brand-600 text-white p-1 shadow-sm">
                        <button
                          type="button"
                          onClick={() => cartItem && updateQuantity(cartItem.id, cartQuantity - 1)}
                          className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-brand-700 active:scale-90 transition-all"
                          aria-label="Decrease quantity"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <span className="w-8 text-center text-sm font-extrabold select-none">
                          {cartQuantity}
                        </span>
                        <button
                          type="button"
                          onClick={() => cartItem && updateQuantity(cartItem.id, cartQuantity + 1)}
                          className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-brand-700 active:scale-90 transition-all"
                          aria-label="Increase quantity"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsCartDrawerOpen(true)}
                        className="px-4 py-3 rounded-2xl bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-xs sm:text-sm border border-brand-200 transition-all"
                      >
                        View in Cart
                      </button>
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => product && toggleWishlist(product)}
                    className={`p-3.5 rounded-2xl border transition-all duration-200 flex items-center justify-center shrink-0 ${
                      product && isInWishlist(product.id)
                        ? "bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-rose-500"
                    }`}
                    aria-label={
                      product && isInWishlist(product.id)
                        ? `Remove ${product.name} from wishlist`
                        : `Add ${product?.name ?? "product"} to wishlist`
                    }
                    title={product && isInWishlist(product.id) ? "Remove from wishlist" : "Add to wishlist"}
                  >
                    <Heart
                      className={`w-5 h-5 transition-transform active:scale-90 ${
                        product && isInWishlist(product.id) ? "fill-rose-500 text-rose-500" : ""
                      }`}
                    />
                  </button>
                </div>
              </div>
            );
          })()}


          {/* Trust Guarantees */}
          <div className="grid grid-cols-3 gap-2.5 pt-4 border-t border-slate-100 text-center">
            <div className="p-3 rounded-2xl bg-slate-50/70 border border-slate-100 flex flex-col items-center">
              <Truck className="w-4 h-4 text-brand-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">Fast Delivery</span>
              <span className="text-[10px] text-slate-400">10-15 minutes</span>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50/70 border border-slate-100 flex flex-col items-center">
              <ShieldCheck className="w-4 h-4 text-emerald-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">Fresh Quality</span>
              <span className="text-[10px] text-slate-400">100% Guaranteed</span>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50/70 border border-slate-100 flex flex-col items-center">
              <RotateCcw className="w-4 h-4 text-amber-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">Easy Return</span>
              <span className="text-[10px] text-slate-400">Doorstep policy</span>
            </div>
          </div>
        </div>
      </div>

      {/* Description & Specifications Section */}
      <div className="pt-8 border-t border-slate-100 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex gap-4 border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab("description")}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === "description"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Product Overview
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("specifications")}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === "specifications"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Specifications & Details
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "description" ? (
          <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-600 leading-relaxed space-y-4">
            <p>{product.description}</p>
          </div>
        ) : (
          <div className="bg-slate-50 rounded-3xl p-5 border border-slate-100 max-w-2xl">
            <dl className="divide-y divide-slate-200/60 text-xs sm:text-sm">
              <div className="py-2.5 grid grid-cols-3">
                <dt className="font-semibold text-slate-500">Brand</dt>
                <dd className="col-span-2 text-slate-900 font-medium">{product.brand}</dd>
              </div>
              <div className="py-2.5 grid grid-cols-3">
                <dt className="font-semibold text-slate-500">Selected Size</dt>
                <dd className="col-span-2 text-slate-900 font-medium">{currentUnit}</dd>
              </div>
              {selectedVariant?.sku && (
                <div className="py-2.5 grid grid-cols-3">
                  <dt className="font-semibold text-slate-500">SKU</dt>
                  <dd className="col-span-2 font-mono text-slate-900">{selectedVariant.sku}</dd>
                </div>
              )}
              {Object.entries(product.specifications || {}).map(([key, value]) => (
                <div key={key} className="py-2.5 grid grid-cols-3">
                  <dt className="font-semibold text-slate-500 capitalize">{key.replace(/_/g, " ")}</dt>
                  <dd className="col-span-2 text-slate-900 font-medium">{String(value)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
