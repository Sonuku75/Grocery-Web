"use client";

import React, { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { Category } from "@/types";
import { categoryService } from "@/services/categoryService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { ErrorState } from "@/components/common/ErrorState";
import { ArrowRight, Sparkles, Compass, Layers } from "lucide-react";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await categoryService.getCategories(true);
      setCategories(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unable to load categories.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8 animate-fade-in">
      <Breadcrumb items={[{ label: "Categories" }]} />

      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-100 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-brand-600 uppercase tracking-wider mb-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Curated Grocery Aisles</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
            Explore All Categories
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1.5 max-w-2xl leading-relaxed">
            From fresh organic produce and dairy essentials to daily pantry staples and household goods. Handpicked for peak quality and fast delivery.
          </p>
        </div>
        <div className="text-xs font-semibold text-slate-400">
          {!loading && categories.length > 0 && `${categories.length} Curated Departments`}
        </div>
      </div>

      {/* Error State */}
      {error && !loading && (
        <ErrorState
          title="Unable to Load Categories"
          message={error}
          onRetry={loadCategories}
        />
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 sm:gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="flex flex-col rounded-3xl bg-white border border-slate-100 overflow-hidden shadow-card animate-pulse"
            >
              <div className="aspect-4/3 w-full bg-slate-200" />
              <div className="p-5 space-y-3">
                <div className="h-5 bg-slate-200 rounded-md w-3/4" />
                <div className="h-3.5 bg-slate-100 rounded-md w-full" />
                <div className="h-3.5 bg-slate-100 rounded-md w-2/3" />
                <div className="pt-2 flex gap-2">
                  <div className="h-6 w-16 bg-slate-100 rounded-lg" />
                  <div className="h-6 w-20 bg-slate-100 rounded-lg" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && categories.length === 0 && (
        <div className="text-center py-16 px-4 bg-white rounded-3xl border border-slate-100 shadow-sm max-w-md mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-4">
            <Compass className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Categories Found</h3>
          <p className="text-xs text-slate-500 mt-1">
            Check back soon as we restock our aisles with fresh goods.
          </p>
        </div>
      )}

      {/* Categories Grid */}
      {!loading && !error && categories.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 sm:gap-6">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              href={`/categories/${cat.slug}`}
              className="group flex flex-col rounded-3xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover hover:border-brand-200 overflow-hidden transition-all duration-300"
            >
              {/* Card Image Banner */}
              <div className="relative aspect-4/3 w-full bg-slate-100 overflow-hidden">
                <Image
                  src={cat.imageUrl || "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&auto=format&fit=crop&q=80"}
                  alt={cat.name}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-80 group-hover:opacity-90 transition-opacity" />
                
                {/* Badge & Title in Image */}
                <div className="absolute bottom-3.5 left-4 right-4 text-white">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-full text-brand-100">
                      ⚡ Fast Delivery
                    </span>
                    {cat.subcategories && cat.subcategories.length > 0 && (
                      <span className="text-[10px] font-medium text-brand-200 flex items-center gap-1">
                        <Layers className="w-3 h-3" />
                        {cat.subcategories.length} Subcategories
                      </span>
                    )}
                  </div>
                  <h2 className="text-lg font-black tracking-tight leading-tight">{cat.name}</h2>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-3">
                    {cat.description || "Farm-fresh groceries handpicked for superior taste and freshness."}
                  </p>

                  {/* Subcategories quick pill preview */}
                  {cat.subcategories && cat.subcategories.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {cat.subcategories.slice(0, 3).map((sub) => (
                        <span
                          key={sub.id}
                          className="text-[10px] font-medium bg-slate-50 text-slate-600 px-2 py-0.5 rounded-md border border-slate-100"
                        >
                          {sub.name}
                        </span>
                      ))}
                      {cat.subcategories.length > 3 && (
                        <span className="text-[10px] font-medium text-brand-600 px-1 py-0.5">
                          +{cat.subcategories.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer Link */}
                <div className="flex items-center justify-between text-xs font-bold text-brand-600 group-hover:text-brand-700 pt-2 border-t border-slate-50">
                  <span>Browse Aisle</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

