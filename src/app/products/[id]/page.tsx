"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { Product, ProductReview } from "@/types";
import { productService } from "@/services/productService";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
import { useLocation } from "@/context/LocationContext";
import { ProductGallery } from "@/components/products/ProductGallery";
import { ProductReviews } from "@/components/products/ProductReviews";
import { ProductGrid } from "@/components/products/ProductGrid";
import { QuantitySelector } from "@/components/common/QuantitySelector";
import { Button } from "@/components/common/Button";
import { Rating } from "@/components/common/Rating";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { formatCurrency } from "@/lib/utils";
import {
  Heart,
  ShoppingBag,
  Zap,
  Truck,
  RotateCcw,
  ShieldCheck,
  Share2,
  CheckCircle2,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

interface ProductPageProps {
  params: Promise<{ id: string }>;
}

export default function ProductDetailsPage({ params }: ProductPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { addToCart, setIsCartDrawerOpen } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const { location } = useLocation();
  const { showToast } = useToast();

  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<ProductReview[]>([]);
  const [relatedProducts, setRelatedProducts] = useState<Product[]>([]);
  const [quantity, setQuantity] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"description" | "specifications" | "reviews">("description");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const prod = await productService.getProductById(id);
        if (prod) {
          setProduct(prod);
          const [revs, related] = await Promise.all([
            productService.getProductReviews(prod.id),
            productService.getRelatedProducts(prod.categoryId, prod.id),
          ]);
          setReviews(revs);
          setRelatedProducts(related);
        }
      } catch (err) {
        console.error("Error loading product details", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <div className="inline-block w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-500">Loading product details...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Product Not Found</h2>
        <p className="text-sm text-slate-500 mb-6">
          The grocery item you are looking for is currently unavailable or has been discontinued.
        </p>
        <Button variant="primary" onClick={() => router.push("/products")}>
          Browse All Products
        </Button>
      </div>
    );
  }

  const isWished = isInWishlist(product.id);

  const handleAddToCart = () => {
    addToCart(product, quantity);
  };

  const handleBuyNow = () => {
    addToCart(product, quantity);
    setIsCartDrawerOpen(false);
    router.push("/checkout");
  };

  const handleShare = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast("Product link copied to clipboard!", "info");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-12">
      <Breadcrumb
        items={[
          { label: "Products", href: "/products" },
          { label: product.categoryName || "Category", href: `/products?category=${product.categoryId}` },
          { label: product.name },
        ]}
      />

      {/* Main Showcase Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
        {/* Left: Images */}
        <div className="lg:col-span-6">
          <ProductGallery images={product.images} productName={product.name} />
        </div>

        {/* Right: Info & Actions */}
        <div className="lg:col-span-6 space-y-6">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-700 bg-brand-50 px-2.5 py-1 rounded-lg">
                {product.brand}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleShare}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                  title="Share product"
                >
                  <Share2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => toggleWishlist(product)}
                  className={`p-2 rounded-xl border transition-colors ${
                    isWished
                      ? "border-rose-200 bg-rose-50 text-rose-600"
                      : "border-slate-200 hover:bg-slate-50 text-slate-500"
                  }`}
                  title={isWished ? "In wishlist" : "Add to wishlist"}
                >
                  <Heart className={`w-4 h-4 ${isWished ? "fill-rose-600" : ""}`} />
                </button>
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-2 leading-tight">
              {product.name}
            </h1>

            <div className="flex items-center gap-3 mt-2.5">
              <Rating rating={product.rating} count={product.ratingCount} size="sm" />
              <span className="text-slate-300">•</span>
              <span className="text-xs font-medium text-slate-500">{product.unit}</span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> In Stock
              </span>
            </div>
          </div>

          {/* Pricing Box */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-black text-slate-900">
                {formatCurrency(product.price)}
              </span>
              {product.originalPrice > product.price && (
                <>
                  <span className="text-base text-slate-400 line-through">
                    {formatCurrency(product.originalPrice)}
                  </span>
                  <span className="px-2 py-0.5 rounded-lg bg-accent-500 text-white text-xs font-extrabold uppercase">
                    {product.discountPercent}% OFF
                  </span>
                </>
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Inclusive of all taxes. Free delivery on orders over $35.
            </p>
          </div>

          {/* Delivery Promise Box */}
          <div className="p-4 rounded-2xl bg-brand-50/40 border border-brand-100 flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center shrink-0">
              <Zap className="w-5 h-5 text-brand-600 fill-brand-600" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-brand-900">
                Delivery in {location.estimatedDeliveryTime} to {location.area} ({location.pincode})
              </h4>
              <p className="text-[11px] text-brand-700 mt-0.5">
                Dispatched from Cartify Cold-Chain Hub #12 with insulated temperature control.
              </p>
            </div>
          </div>

          {/* Quantity & Actions */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-4">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Quantity:
              </span>
              <QuantitySelector
                quantity={quantity}
                onIncrease={() => setQuantity((q) => q + 1)}
                onDecrease={() => setQuantity((q) => Math.max(1, q - 1))}
                size="md"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <Button
                variant="primary"
                size="lg"
                leftIcon={<ShoppingBag className="w-5 h-5" />}
                onClick={handleAddToCart}
                fullWidth
              >
                Add to Cart
              </Button>
              <Button
                variant="accent"
                size="lg"
                onClick={handleBuyNow}
                fullWidth
              >
                Buy Now
              </Button>
            </div>
          </div>

          {/* Value props */}
          <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-100 text-center">
            <div className="flex flex-col items-center">
              <Truck className="w-5 h-5 text-brand-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">15-Min Delivery</span>
            </div>
            <div className="flex flex-col items-center">
              <RotateCcw className="w-5 h-5 text-brand-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">Easy Returns</span>
            </div>
            <div className="flex flex-col items-center">
              <ShieldCheck className="w-5 h-5 text-brand-600 mb-1" />
              <span className="text-[11px] font-bold text-slate-800">100% Quality</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs: Description, Specs, Reviews */}
      <div className="border-t border-slate-100 pt-8">
        <div className="flex border-b border-slate-200 gap-6">
          <button
            onClick={() => setActiveTab("description")}
            className={`pb-3 text-sm font-bold transition-all relative ${
              activeTab === "description"
                ? "text-brand-600 border-b-2 border-brand-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Product Overview
          </button>
          <button
            onClick={() => setActiveTab("specifications")}
            className={`pb-3 text-sm font-bold transition-all relative ${
              activeTab === "specifications"
                ? "text-brand-600 border-b-2 border-brand-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Specifications & Origin
          </button>
          <button
            onClick={() => setActiveTab("reviews")}
            className={`pb-3 text-sm font-bold transition-all relative ${
              activeTab === "reviews"
                ? "text-brand-600 border-b-2 border-brand-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Customer Reviews ({reviews.length})
          </button>
        </div>

        <div className="pt-6">
          {activeTab === "description" && (
            <div className="max-w-3xl space-y-4 text-sm text-slate-600 leading-relaxed">
              <p>{product.description}</p>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 mt-4">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Key Highlights
                </h4>
                <ul className="list-disc pl-5 space-y-1 text-xs text-slate-600">
                  <li>Directly sourced under strict cold-chain quality supervision</li>
                  <li>Standard packaging preserved in 100% recyclable materials</li>
                  <li>Inspected individually for optimal maturity and freshness</li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === "specifications" && (
            <div className="max-w-2xl">
              <div className="rounded-2xl border border-slate-200 overflow-hidden divide-y divide-slate-100">
                {Object.entries(product.specifications).map(([key, val]) => (
                  <div key={key} className="grid grid-cols-3 p-3 text-xs">
                    <span className="font-bold text-slate-700">{key}</span>
                    <span className="col-span-2 text-slate-600">{val}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "reviews" && (
            <div className="max-w-3xl">
              <ProductReviews
                reviews={reviews}
                rating={product.rating}
                ratingCount={product.ratingCount}
              />
            </div>
          )}
        </div>
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <div className="pt-8 border-t border-slate-100">
          <h2 className="text-xl font-bold text-slate-900 mb-6">
            You Might Also Like
          </h2>
          <ProductGrid products={relatedProducts} />
        </div>
      )}
    </div>
  );
}
