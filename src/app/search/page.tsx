"use client";

import React, { useEffect, useState, useTransition, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  X,
  RotateCcw,
  Sparkles,
  ChevronDown,
  Check,
  Compass,
  Tag,
  Loader2,
  PackageX,
  ShoppingBag,
} from "lucide-react";

import {
  Category,
  Product,
  SearchParams,
  SearchProduct,
  SearchSortOption,
} from "@/types";
import { searchService, searchProductToProduct } from "@/services/searchService";
import { categoryService } from "@/services/categoryService";
import { ProductCard } from "@/components/products/ProductCard";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { formatCurrency, cn } from "@/lib/utils";

const SORT_OPTIONS: { label: string; value: SearchSortOption }[] = [
  { label: "Relevance", value: "relevance" },
  { label: "Price: Low to High", value: "price_low_to_high" },
  { label: "Price: High to Low", value: "price_high_to_low" },
  { label: "Newest First", value: "newest" },
  { label: "Featured", value: "featured" },
];

const PRICE_PRESETS = [
  { label: "All Prices", min: undefined, max: undefined },
  { label: "Under ₹50", min: 0, max: 50 },
  { label: "₹50 to ₹100", min: 50, max: 100 },
  { label: "₹100 to ₹250", min: 100, max: 250 },
  { label: "₹250 & Above", min: 250, max: undefined },
];

const POPULAR_BRANDS = [
  "Amul",
  "Mother Dairy",
  "Nestle",
  "Britannia",
  "Organic Tattva",
  "Tata Sampann",
  "Aashirvaad",
  "Fortune",
];

function SearchResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  // Read URL search params
  const qParam = searchParams.get("q") || "";
  const catParam = searchParams.get("category_id") || searchParams.get("categoryId") || "";
  const brandParam = searchParams.get("brand") || "";
  const minPriceParam = searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined;
  const maxPriceParam = searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined;
  const sortParam = (searchParams.get("sort") as SearchSortOption) || "relevance";

  // Component state
  const [searchInput, setSearchInput] = useState(qParam);
  const [products, setProducts] = useState<SearchProduct[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filter UI state
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sortDropdownOpen, setSortDropdownOpen] = useState(false);

  // Sync searchInput when URL qParam changes
  useEffect(() => {
    setSearchInput(qParam);
  }, [qParam]);

  // Load available categories for filtering
  useEffect(() => {
    categoryService
      .getCategories(true)
      .then((cats) => setCategories(cats))
      .catch(() => {});
  }, []);

  // Fetch search results whenever URL parameters change
  useEffect(() => {
    let isCancelled = false;

    async function executeSearch() {
      setLoading(true);
      setError(null);

      const params: SearchParams = {
        q: qParam.trim() || undefined,
        category_id: catParam || undefined,
        brand: brandParam || undefined,
        min_price: minPriceParam,
        max_price: maxPriceParam,
        sort: sortParam,
        limit: 20,
      };

      try {
        const res = await searchService.search(params);
        if (!isCancelled) {
          setProducts(res.items);
          setTotalCount(res.total);
          setHasMore(res.hasMore);
          setNextCursor(res.nextCursor);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setError(
            err instanceof Error ? err.message : "Search is temporarily unavailable."
          );
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    executeSearch();

    return () => {
      isCancelled = true;
    };
  }, [qParam, catParam, brandParam, minPriceParam, maxPriceParam, sortParam]);

  // Handle Load More (pagination)
  const handleLoadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);

    try {
      const res = await searchService.search({
        q: qParam.trim() || undefined,
        category_id: catParam || undefined,
        brand: brandParam || undefined,
        min_price: minPriceParam,
        max_price: maxPriceParam,
        sort: sortParam,
        cursor: nextCursor,
        limit: 20,
      });

      setProducts((prev) => [...prev, ...res.items]);
      setHasMore(res.hasMore);
      setNextCursor(res.nextCursor);
    } catch {
      // Keep existing items on failure
    } finally {
      setLoadingMore(false);
    }
  };

  // Helper to update URL parameters
  const updateUrlParams = (updates: Record<string, string | number | undefined | null>) => {
    const current = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, val]) => {
      if (val === undefined || val === null || val === "") {
        current.delete(key);
      } else {
        current.set(key, String(val));
      }
    });

    startTransition(() => {
      router.push(`/search?${current.toString()}`);
    });
  };

  // Search input submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateUrlParams({ q: searchInput.trim() || null });
  };

  // Reset all filters
  const handleClearAllFilters = () => {
    updateUrlParams({
      category_id: null,
      categoryId: null,
      brand: null,
      min_price: null,
      max_price: null,
    });
    setIsMobileFilterOpen(false);
  };

  // Count active filters (excluding query and sort)
  const activeFiltersCount =
    (catParam ? 1 : 0) +
    (brandParam ? 1 : 0) +
    (minPriceParam !== undefined || maxPriceParam !== undefined ? 1 : 0);

  // Selected category title
  const activeCategory = categories.find((c) => c.id === catParam || c.slug === catParam);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb
        items={[
          { label: "Catalog", href: "/products" },
          { label: "Search", href: "/search" },
          ...(qParam ? [{ label: `"${qParam}"` }] : []),
        ]}
      />

      {/* Hero Search & Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-brand-950 text-white p-6 sm:p-8 shadow-sm">
        <div className="relative z-10 max-w-2xl space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 text-xs font-semibold backdrop-blur-sm border border-brand-500/30">
            <Sparkles className="w-3.5 h-3.5 text-accent-400" />
            Instant 15-Minute Grocery Search
          </span>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight">
            {qParam ? (
              <>
                Results for <span className="text-brand-400">&ldquo;{qParam}&rdquo;</span>
              </>
            ) : (
              "Explore Cartify Catalog"
            )}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 font-normal leading-relaxed">
            Search across fresh dairy, daily farm produce, artisanal bakery, and household essentials.
          </p>

          {/* Large In-Page Search Bar */}
          <form onSubmit={handleSearchSubmit} className="pt-2 relative flex items-center">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search groceries, brands, categories..."
              className="w-full h-12 sm:h-13 pl-11 pr-28 rounded-2xl bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-brand-500/30 shadow-md transition-all"
            />
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <button
              type="submit"
              className="absolute right-2 px-4 sm:px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs sm:text-sm font-bold shadow transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Subtle decorative background blur */}
        <div className="absolute -right-16 -bottom-16 w-80 h-80 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
      </div>

      {/* Main Results Toolbar: Filter pill indicators, Count, Sorting, Mobile Filter Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2 border-b border-slate-100">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-baseline gap-2">
            <span className="text-base sm:text-lg font-bold text-slate-900">
              {loading ? "Searching..." : `${totalCount} ${totalCount === 1 ? "product" : "products"}`}
            </span>
            {qParam && (
              <span className="text-xs text-slate-400 font-medium">
                found in catalog
              </span>
            )}
          </div>

          {/* Active Filter Tags */}
          {activeFiltersCount > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {catParam && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 text-xs font-semibold border border-brand-100">
                  <Compass className="w-3 h-3 text-brand-600" />
                  {activeCategory ? activeCategory.name : "Category"}
                  <button
                    onClick={() => updateUrlParams({ category_id: null, categoryId: null })}
                    className="hover:text-brand-900"
                    aria-label="Remove category filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}

              {brandParam && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-accent-50 text-accent-700 text-xs font-semibold border border-accent-100">
                  <Tag className="w-3 h-3 text-accent-600" />
                  {brandParam}
                  <button
                    onClick={() => updateUrlParams({ brand: null })}
                    className="hover:text-accent-900"
                    aria-label="Remove brand filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}

              {(minPriceParam !== undefined || maxPriceParam !== undefined) && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200">
                  {minPriceParam !== undefined && maxPriceParam !== undefined
                    ? `₹${minPriceParam} - ₹${maxPriceParam}`
                    : minPriceParam !== undefined
                    ? `≥ ₹${minPriceParam}`
                    : `≤ ₹${maxPriceParam}`}
                  <button
                    onClick={() => updateUrlParams({ min_price: null, max_price: null })}
                    className="hover:text-slate-900"
                    aria-label="Remove price filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}

              <button
                onClick={handleClearAllFilters}
                className="text-xs text-rose-600 hover:text-rose-700 font-semibold underline px-1"
              >
                Clear all
              </button>
            </div>
          )}
        </div>

        {/* Toolbar Controls: Sort dropdown & Mobile filter button */}
        <div className="flex items-center gap-2.5 self-end sm:self-auto">
          {/* Mobile Filter Toggle */}
          <button
            onClick={() => setIsMobileFilterOpen(true)}
            className="lg:hidden flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Filters</span>
            {activeFiltersCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-brand-600 text-white text-[10px] font-bold flex items-center justify-center">
                {activeFiltersCount}
              </span>
            )}
          </button>

          {/* Sort Dropdown */}
          <div className="relative">
            <button
              onClick={() => setSortDropdownOpen(!sortDropdownOpen)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-200 hover:border-slate-300 bg-white text-xs font-semibold text-slate-700 shadow-xs transition-colors"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
              <span>
                {SORT_OPTIONS.find((s) => s.value === sortParam)?.label || "Sort"}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {sortDropdownOpen && (
              <div
                onMouseLeave={() => setSortDropdownOpen(false)}
                className="absolute right-0 top-full mt-1.5 w-48 bg-white rounded-2xl shadow-dropdown border border-slate-100 p-1.5 z-40 animate-fade-in"
              >
                {SORT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      updateUrlParams({ sort: opt.value });
                      setSortDropdownOpen(false);
                    }}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-left transition-colors",
                      sortParam === opt.value
                        ? "bg-brand-50 text-brand-700 font-bold"
                        : "hover:bg-slate-50 text-slate-700"
                    )}
                  >
                    <span>{opt.label}</span>
                    {sortParam === opt.value && <Check className="w-3.5 h-3.5 text-brand-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Body: Two column layout on desktop (Sidebar Filters + Results Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Desktop Sidebar Filter Panel */}
        <aside className="hidden lg:block lg:col-span-3 space-y-6 bg-white p-5 rounded-3xl border border-slate-100 shadow-xs sticky top-24">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-brand-600" />
              <h2 className="text-sm font-bold text-slate-900">Filters</h2>
            </div>
            {activeFiltersCount > 0 && (
              <button
                onClick={handleClearAllFilters}
                className="text-xs text-rose-600 hover:text-rose-700 font-semibold"
              >
                Reset
              </button>
            )}
          </div>

          {/* Filter: Categories */}
          <div className="space-y-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Categories
            </h3>
            <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
              <button
                onClick={() => updateUrlParams({ category_id: null, categoryId: null })}
                className={cn(
                  "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left",
                  !catParam
                    ? "bg-brand-50 text-brand-700 font-bold"
                    : "hover:bg-slate-50 text-slate-600"
                )}
              >
                <span>All Categories</span>
                {!catParam && <Check className="w-3.5 h-3.5 text-brand-600" />}
              </button>
              {categories.map((c) => {
                const isSelected = catParam === c.id || catParam === c.slug;
                return (
                  <button
                    key={c.id}
                    onClick={() => updateUrlParams({ category_id: c.id, categoryId: null })}
                    className={cn(
                      "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left",
                      isSelected
                        ? "bg-brand-50 text-brand-700 font-bold"
                        : "hover:bg-slate-50 text-slate-600"
                    )}
                  >
                    <span className="truncate">{c.name}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-brand-600 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Filter: Brands */}
          <div className="space-y-2.5 pt-3 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Popular Brands
            </h3>
            <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
              <button
                onClick={() => updateUrlParams({ brand: null })}
                className={cn(
                  "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left",
                  !brandParam
                    ? "bg-brand-50 text-brand-700 font-bold"
                    : "hover:bg-slate-50 text-slate-600"
                )}
              >
                <span>All Brands</span>
                {!brandParam && <Check className="w-3.5 h-3.5 text-brand-600" />}
              </button>
              {POPULAR_BRANDS.map((b) => {
                const isSelected = brandParam.toLowerCase() === b.toLowerCase();
                return (
                  <button
                    key={b}
                    onClick={() => updateUrlParams({ brand: isSelected ? null : b })}
                    className={cn(
                      "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left",
                      isSelected
                        ? "bg-brand-50 text-brand-700 font-bold"
                        : "hover:bg-slate-50 text-slate-600"
                    )}
                  >
                    <span>{b}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-brand-600 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Filter: Price Presets */}
          <div className="space-y-2.5 pt-3 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Price Range
            </h3>
            <div className="space-y-1">
              {PRICE_PRESETS.map((preset, idx) => {
                const isSelected =
                  minPriceParam === preset.min && maxPriceParam === preset.max;
                return (
                  <button
                    key={idx}
                    onClick={() =>
                      updateUrlParams({
                        min_price: preset.min ?? null,
                        max_price: preset.max ?? null,
                      })
                    }
                    className={cn(
                      "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left",
                      isSelected
                        ? "bg-brand-50 text-brand-700 font-bold"
                        : "hover:bg-slate-50 text-slate-600"
                    )}
                  >
                    <span>{preset.label}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-brand-600 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        </aside>

        {/* Results Area */}
        <main className="lg:col-span-9 space-y-6">
          {/* Loading Skeleton State */}
          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4 animate-pulse">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="bg-slate-100 rounded-3xl aspect-[3/4] p-4 flex flex-col justify-end space-y-2"
                >
                  <div className="h-3 w-16 bg-slate-200 rounded" />
                  <div className="h-4 w-full bg-slate-200 rounded" />
                  <div className="h-4 w-20 bg-slate-200 rounded" />
                </div>
              ))}
            </div>
          ) : error ? (
            /* Error State */
            <div className="flex flex-col items-center justify-center p-12 text-center rounded-3xl bg-rose-50/50 border border-rose-100 max-w-md mx-auto my-12 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center">
                <RotateCcw className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-slate-900">Search Error</h2>
              <p className="text-xs text-slate-500 leading-relaxed">{error}</p>
              <Button
                size="sm"
                variant="outline"
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                onClick={() => updateUrlParams({ q: qParam })}
              >
                Try Again
              </Button>
            </div>
          ) : products.length === 0 ? (
            /* Apple-Inspired Empty State */
            <div className="flex flex-col items-center justify-center p-12 text-center rounded-3xl bg-slate-50/80 border border-slate-100 max-w-md mx-auto my-8 space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-slate-100 text-slate-400 flex items-center justify-center">
                <PackageX className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-slate-900">
                  No products found
                </h2>
                <p className="text-xs text-slate-500 leading-relaxed">
                  We couldn&apos;t find any items matching &ldquo;{qParam || "your filters"}&rdquo;.
                </p>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-100 text-xs text-slate-600 text-left w-full space-y-1.5">
                <p className="font-semibold text-slate-900">Helpful suggestions:</p>
                <ul className="list-disc list-inside space-y-1 text-slate-500 text-[11px]">
                  <li>Check your query for spelling typos</li>
                  <li>Try broader search terms like &ldquo;Milk&rdquo; or &ldquo;Avocado&rdquo;</li>
                  <li>Remove active price or brand filters</li>
                </ul>
              </div>

              <div className="flex items-center gap-3 pt-2">
                {activeFiltersCount > 0 && (
                  <Button size="sm" variant="outline" onClick={handleClearAllFilters}>
                    Clear Filters
                  </Button>
                )}
                <Link href="/categories">
                  <Button size="sm" variant="primary" leftIcon={<ShoppingBag className="w-3.5 h-3.5" />}>
                    Browse Categories
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            /* Product Grid */
            <div className="space-y-8">
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 lg:gap-5">
                {products.map((p) => {
                  const productModel: Product = searchProductToProduct(p);
                  return <ProductCard key={p.id} product={productModel} />;
                })}
              </div>

              {/* Keyset Cursor Pagination (Load More) */}
              {hasMore && (
                <div className="flex justify-center pt-6">
                  <Button
                    size="md"
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    leftIcon={
                      loadingMore ? (
                        <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                      ) : undefined
                    }
                    className="px-8 rounded-2xl shadow-xs"
                  >
                    {loadingMore ? "Loading more products..." : "Load More Products"}
                  </Button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Mobile Filter Slide-Over Drawer */}
      {isMobileFilterOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden animate-fade-in">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileFilterOpen(false)}
          />

          {/* Bottom sheet / Drawer */}
          <div className="relative ml-auto w-full max-w-xs h-full bg-white shadow-2xl flex flex-col z-10 animate-slide-in-right">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-brand-600" />
                <h3 className="text-sm font-bold text-slate-900">Filters</h3>
              </div>
              <button
                onClick={() => setIsMobileFilterOpen(false)}
                className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600"
                aria-label="Close filters"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Filter Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Category */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Categories
                </h4>
                <div className="space-y-1">
                  <button
                    onClick={() => updateUrlParams({ category_id: null, categoryId: null })}
                    className={cn(
                      "w-full flex items-center justify-between p-2 rounded-xl text-xs text-left",
                      !catParam ? "bg-brand-50 text-brand-700 font-bold" : "text-slate-600"
                    )}
                  >
                    <span>All Categories</span>
                    {!catParam && <Check className="w-4 h-4 text-brand-600" />}
                  </button>
                  {categories.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => updateUrlParams({ category_id: c.id, categoryId: null })}
                      className={cn(
                        "w-full flex items-center justify-between p-2 rounded-xl text-xs text-left",
                        catParam === c.id || catParam === c.slug
                          ? "bg-brand-50 text-brand-700 font-bold"
                          : "text-slate-600"
                      )}
                    >
                      <span>{c.name}</span>
                      {(catParam === c.id || catParam === c.slug) && (
                        <Check className="w-4 h-4 text-brand-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Brand */}
              <div className="space-y-2 pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Brands
                </h4>
                <div className="space-y-1">
                  <button
                    onClick={() => updateUrlParams({ brand: null })}
                    className={cn(
                      "w-full flex items-center justify-between p-2 rounded-xl text-xs text-left",
                      !brandParam ? "bg-brand-50 text-brand-700 font-bold" : "text-slate-600"
                    )}
                  >
                    <span>All Brands</span>
                    {!brandParam && <Check className="w-4 h-4 text-brand-600" />}
                  </button>
                  {POPULAR_BRANDS.map((b) => (
                    <button
                      key={b}
                      onClick={() =>
                        updateUrlParams({
                          brand: brandParam.toLowerCase() === b.toLowerCase() ? null : b,
                        })
                      }
                      className={cn(
                        "w-full flex items-center justify-between p-2 rounded-xl text-xs text-left",
                        brandParam.toLowerCase() === b.toLowerCase()
                          ? "bg-brand-50 text-brand-700 font-bold"
                          : "text-slate-600"
                      )}
                    >
                      <span>{b}</span>
                      {brandParam.toLowerCase() === b.toLowerCase() && (
                        <Check className="w-4 h-4 text-brand-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price */}
              <div className="space-y-2 pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Price Presets
                </h4>
                <div className="space-y-1">
                  {PRICE_PRESETS.map((preset, idx) => {
                    const isSelected =
                      minPriceParam === preset.min && maxPriceParam === preset.max;
                    return (
                      <button
                        key={idx}
                        onClick={() =>
                          updateUrlParams({
                            min_price: preset.min ?? null,
                            max_price: preset.max ?? null,
                          })
                        }
                        className={cn(
                          "w-full flex items-center justify-between p-2 rounded-xl text-xs text-left",
                          isSelected
                            ? "bg-brand-50 text-brand-700 font-bold"
                            : "text-slate-600"
                        )}
                      >
                        <span>{preset.label}</span>
                        {isSelected && <Check className="w-4 h-4 text-brand-600" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-slate-100 flex items-center gap-3">
              <Button
                size="sm"
                variant="outline"
                onClick={handleClearAllFilters}
                className="flex-1"
              >
                Reset All
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={() => setIsMobileFilterOpen(false)}
                className="flex-1"
              >
                Show Results
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-12 text-center text-sm text-slate-400 animate-pulse">
          Loading Cartify Search...
        </div>
      }
    >
      <SearchResultsContent />
    </Suspense>
  );
}
