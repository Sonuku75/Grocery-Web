"use client";

import React, { useEffect, useState, useCallback, use } from "react";
import Image from "next/image";
import Link from "next/link";
import { Category } from "@/types";
import { categoryService } from "@/services/categoryService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { ErrorState } from "@/components/common/ErrorState";
import { ArrowLeft, ArrowRight, Sparkles, Layers, Package, Compass } from "lucide-react";

interface CategorySlugPageProps {
  params: Promise<{ slug: string }>;
}

export default function CategorySlugPage({ params }: CategorySlugPageProps) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const [category, setCategory] = useState<Category | null>(null);
  const [subcategories, setSubcategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCategoryData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cat = await categoryService.getCategoryBySlug(slug);
      if (!cat) {
        setError("Category not found.");
        return;
      }
      setCategory(cat);

      // Load subcategories if not already embedded
      if (cat.subcategories && cat.subcategories.length > 0) {
        setSubcategories(cat.subcategories);
      } else {
        const subs = await categoryService.getSubcategories(cat.id);
        setSubcategories(subs);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load category details.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    loadCategoryData();
  }, [loadCategoryData]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8 animate-fade-in">
      {/* Breadcrumb Navigation */}
      <Breadcrumb
        items={[
          { label: "Categories", href: "/categories" },
          { label: category ? category.name : slug },
        ]}
      />

      {/* Error State */}
      {error && !loading && (
        <div className="space-y-4">
          <ErrorState
            title="Department Not Available"
            message={error}
            onRetry={loadCategoryData}
          />
          <div className="text-center">
            <Link
              href="/categories"
              className="inline-flex items-center gap-2 text-xs font-bold text-brand-600 hover:text-brand-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to all categories</span>
            </Link>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-8 animate-pulse">
          <div className="h-64 sm:h-80 w-full rounded-3xl bg-slate-200" />
          <div className="space-y-3">
            <div className="h-6 bg-slate-200 rounded-md w-48" />
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-40 rounded-2xl bg-slate-100" />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Category Hero & Subcategories */}
      {!loading && !error && category && (
        <>
          {/* Hero Banner */}
          <div className="relative rounded-3xl overflow-hidden bg-slate-900 text-white min-h-[260px] sm:min-h-[320px] flex items-end shadow-xl border border-slate-100">
            <Image
              src={category.imageUrl || "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&auto=format&fit=crop&q=80"}
              alt={category.name}
              fill
              priority
              className="object-cover opacity-45 scale-105 transition-transform duration-700"
              sizes="100vw"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />

            <div className="relative z-10 p-6 sm:p-10 max-w-3xl space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/30 border border-brand-400/40 text-brand-200 text-xs font-semibold backdrop-blur-md">
                <Sparkles className="w-3.5 h-3.5 text-accent-400" />
                <span>Express 15-Min Delivery</span>
              </div>

              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                {category.name}
              </h1>

              <p className="text-slate-200 text-xs sm:text-base leading-relaxed max-w-2xl font-normal">
                {category.description || "Farm-fresh groceries and pantry essentials carefully curated for high quality and nutrition."}
              </p>
            </div>
          </div>

          {/* Subcategories Section */}
          <div className="space-y-6 pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-brand-600" />
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                  Subcategories & Aisles
                </h2>
              </div>
              <span className="text-xs font-semibold text-slate-500">
                {subcategories.length} {subcategories.length === 1 ? "Section" : "Sections"}
              </span>
            </div>

            {/* Subcategories Grid */}
            {subcategories.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                {subcategories.map((sub) => (
                  <div
                    key={sub.id}
                    className="group flex flex-col justify-between p-5 rounded-3xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover hover:border-brand-200 transition-all duration-200"
                  >
                    <div className="space-y-2">
                      <div className="w-10 h-10 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Package className="w-5 h-5" />
                      </div>
                      <h3 className="text-base font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                        {sub.name}
                      </h3>
                      <p className="text-xs text-slate-500 line-clamp-2">
                        {sub.description || `Fresh ${sub.name} handpicked and delivered in 15 minutes.`}
                      </p>
                    </div>

                    <div className="pt-4 mt-3 border-t border-slate-50 flex items-center justify-between text-xs font-bold text-brand-600">
                      <span>Browse Items</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 px-4 bg-white rounded-3xl border border-slate-100 shadow-sm max-w-md mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-slate-50 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <Compass className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-slate-800">No Subcategories in this Aisle</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Products in this department will be accessible directly in the upcoming Catalog module.
                </p>
              </div>
            )}
          </div>

          {/* Module 4 Catalog Ready Notice */}
          <div className="rounded-2xl bg-brand-50/60 border border-brand-100 p-4 sm:p-5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand-600 text-white flex items-center justify-center shrink-0">
                <Package className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs sm:text-sm font-bold text-brand-900">
                  Product Catalog Connection Ready
                </h4>
                <p className="text-[11px] sm:text-xs text-brand-700">
                  Taxonomy and subcategory routes are configured. Real-time product inventory will be mapped in Module 4.
                </p>
              </div>
            </div>
            <Link
              href="/categories"
              className="text-xs font-bold text-brand-600 hover:text-brand-800 whitespace-nowrap hidden sm:inline"
            >
              All Categories →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}