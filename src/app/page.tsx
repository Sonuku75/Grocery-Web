"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  Sparkles,
  Zap,
  TrendingUp,
  Clock,
  ShieldCheck,
  Percent,
  Leaf,
  ChevronRight,
} from "lucide-react";
import { Product, Category } from "@/types";
import { productService } from "@/services/productService";
import { categoryService } from "@/services/categoryService";
import { ProductGrid } from "@/components/products/ProductGrid";
import { CategoryGrid } from "@/components/categories/CategoryGrid";
import { Button } from "@/components/common/Button";

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [popularProducts, setPopularProducts] = useState<Product[]>([]);
  const [dealProducts, setDealProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadHomeData() {
      try {
        const [cats, featured, deals] = await Promise.all([
          categoryService.getCategories(),
          productService.getFeaturedProducts(),
          productService.getDeals(),
        ]);
        setCategories(cats);
        setPopularProducts(featured);
        setDealProducts(deals);
      } catch (err) {
        console.error("Error loading home page data", err);
      } finally {
        setLoading(false);
      }
    }
    loadHomeData();
  }, []);

  return (
    <div className="space-y-10 sm:space-y-14 md:space-y-16 pb-12">
      {/* 1. HERO PROMOTIONAL SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 sm:pt-6">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-emerald-950 text-white shadow-xl min-h-[420px] sm:min-h-[480px] flex items-center">
          {/* Subtle background overlay patterns */}
          <div className="absolute inset-0 bg-[radial-gradient(#34d399_1px,transparent_1px)] [background-size:20px_20px] opacity-10 pointer-events-none" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center p-6 sm:p-10 lg:p-14 w-full">
            <div className="lg:col-span-7 space-y-4 sm:space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-700/80 border border-brand-500/40 text-brand-200 text-xs font-semibold backdrop-blur-xs">
                <Zap className="w-3.5 h-3.5 text-accent-400 fill-accent-400" />
                <span>Lightning 15-Minute Grocery Delivery</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight leading-[1.15] text-white">
                Farm-Fresh Groceries & Daily Essentials,{" "}
                <span className="text-brand-300">Delivered in Minutes.</span>
              </h1>

              <p className="text-slate-200 text-sm sm:text-base max-w-xl mx-auto lg:mx-0 leading-relaxed font-normal">
                Handpicked organic vegetables, pasture-raised dairy, warm artisan sourdough, and gourmet pantry staples brought directly to your doorstep.
              </p>

              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 pt-2">
                <Link href="/products">
                  <Button
                    variant="accent"
                    size="lg"
                    rightIcon={<ArrowRight className="w-4 h-4" />}
                    className="shadow-lg shadow-accent-600/30"
                  >
                    Shop Now
                  </Button>
                </Link>
                <Link href="/offers">
                  <Button
                    variant="outline"
                    size="lg"
                    className="bg-white/10 hover:bg-white/20 text-white border-white/20 backdrop-blur-xs"
                  >
                    View Deals (Up to 50% Off)
                  </Button>
                </Link>
              </div>

              {/* Trust micro-badges */}
              <div className="flex items-center justify-center lg:justify-start gap-6 pt-4 text-xs font-medium text-slate-300">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-brand-400" />
                  <span>15 Mins Delivery</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Leaf className="w-4 h-4 text-emerald-400" />
                  <span>100% Organic & Fresh</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-accent-400" />
                  <span>Contactless & Safe</span>
                </div>
              </div>
            </div>

            {/* Hero Image Showcase */}
            <div className="lg:col-span-5 relative flex justify-center">
              <div className="relative w-full max-w-md aspect-square rounded-3xl overflow-hidden border border-white/15 shadow-2xl">
                <Image
                  src="https://images.unsplash.com/photo-1542838132-92c53300491e?w=900&auto=format&fit=crop&q=80"
                  alt="Fresh organic fruits and vegetables"
                  fill
                  priority
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 40vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur-md rounded-2xl p-3.5 shadow-lg border border-slate-100 flex items-center justify-between text-slate-800">
                  <div>
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-brand-700 bg-brand-100 px-2 py-0.5 rounded-md">
                      Fresh Harvest
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 mt-1">California Organic Hass Avocados</h4>
                    <p className="text-[11px] text-slate-500">Peak season freshness • Ready in 15 mins</p>
                  </div>
                  <span className="text-sm font-black text-brand-600 shrink-0">$4.49</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. POPULAR CATEGORIES */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Explore The Aisles</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Shop by Category
            </h2>
          </div>
          <Link
            href="/categories"
            className="text-xs sm:text-sm font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition-colors"
          >
            <span>View All</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        <CategoryGrid categories={categories} isLoading={loading} />
      </section>

      {/* 3. PROMOTIONAL SHOWCASE BANNERS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {/* Banner 1 */}
          <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-amber-500 to-orange-600 text-white p-6 sm:p-8 flex flex-col justify-between min-h-[200px] shadow-card group">
            <div className="relative z-10 max-w-xs space-y-2">
              <span className="inline-block bg-white/20 backdrop-blur-xs text-white text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-lg">
                Weekend Super Deals
              </span>
              <h3 className="text-2xl font-black leading-tight">
                Up to 50% Off Morning Breakfast Essentials
              </h3>
              <p className="text-xs text-orange-100">
                Farm-fresh eggs, organic whole milk, yogurt & freshly baked croissants.
              </p>
            </div>
            <div className="relative z-10 pt-4">
              <Link href="/products?category=cat-dairy-breakfast">
                <button className="px-4 py-2 rounded-xl bg-white text-orange-600 text-xs font-bold shadow-md hover:bg-orange-50 transition-colors">
                  Explore Deals →
                </button>
              </Link>
            </div>
            {/* Background art */}
            <div className="absolute -right-8 -bottom-8 w-48 h-48 opacity-20 group-hover:scale-110 transition-transform duration-300">
              <Percent className="w-full h-full" />
            </div>
          </div>

          {/* Banner 2 */}
          <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-emerald-600 to-teal-700 text-white p-6 sm:p-8 flex flex-col justify-between min-h-[200px] shadow-card group">
            <div className="relative z-10 max-w-xs space-y-2">
              <span className="inline-block bg-white/20 backdrop-blur-xs text-white text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-lg">
                Fresh Harvest Direct
              </span>
              <h3 className="text-2xl font-black leading-tight">
                100% Certified Organic Crisp Produce
              </h3>
              <p className="text-xs text-emerald-100">
                Picked this morning from local regenerative California growers.
              </p>
            </div>
            <div className="relative z-10 pt-4">
              <Link href="/products?category=cat-fruits-veg">
                <button className="px-4 py-2 rounded-xl bg-white text-emerald-700 text-xs font-bold shadow-md hover:bg-emerald-50 transition-colors">
                  Shop Farm Fresh →
                </button>
              </Link>
            </div>
            <div className="absolute -right-8 -bottom-8 w-48 h-48 opacity-20 group-hover:scale-110 transition-transform duration-300">
              <Leaf className="w-full h-full" />
            </div>
          </div>
        </div>
      </section>

      {/* 4. POPULAR PRODUCTS SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Customer Favorites</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Popular Everyday Essentials
            </h2>
          </div>
          <Link
            href="/products?sort=popular"
            className="text-xs sm:text-sm font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition-colors"
          >
            <span>See All</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        <ProductGrid products={popularProducts} isLoading={loading} />
      </section>

      {/* 5. HOT OFFERS & DEALS SECTION */}
      <section className="bg-slate-100/60 py-12 border-y border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-accent-600 uppercase tracking-wider mb-1">
                <Zap className="w-3.5 h-3.5 text-accent-500 fill-accent-500" />
                <span>Flash Discounts</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Deals of the Day (Save Big)
              </h2>
            </div>
            <Link
              href="/offers"
              className="text-xs sm:text-sm font-bold text-accent-600 hover:text-accent-700 flex items-center gap-1 transition-colors"
            >
              <span>All Offers</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <ProductGrid products={dealProducts} isLoading={loading} />
        </div>
      </section>

      {/* 6. CARTIFY SPEED & TRUST HIGHLIGHTS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-white border border-slate-100 p-8 sm:p-12 shadow-card grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
              <Clock className="w-7 h-7" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">15-Min Delivery</h4>
            <p className="text-xs text-slate-500 mt-1">
              Hyperlocal micro-stores stocked for rapid dispatch.
            </p>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
              <Leaf className="w-7 h-7" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">100% Quality Fresh</h4>
            <p className="text-xs text-slate-500 mt-1">
              Direct farm partnerships, rigorous cold-chain custody.
            </p>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">Zero Question Returns</h4>
            <p className="text-xs text-slate-500 mt-1">
              Not happy with produce? Instant 1-click refund or replacement.
            </p>
          </div>

          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
              <Sparkles className="w-7 h-7" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">No Hidden Fees</h4>
            <p className="text-xs text-slate-500 mt-1">
              Transparent pricing with free delivery on orders over $35.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
