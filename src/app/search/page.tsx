"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Product } from "@/types";
import { productService } from "@/services/productService";
import { ProductGrid } from "@/components/products/ProductGrid";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Search, Sparkles } from "lucide-react";

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get("q") || "";

  const [inputQuery, setInputQuery] = useState(query);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const TRENDING_SEARCHES = [
    "Organic Avocados",
    "Whole Milk",
    "Pasture-Raised Eggs",
    "Sourdough Bread",
    "Sockeye Salmon",
    "Olive Oil",
    "Strawberries",
  ];

  useEffect(() => {
    setInputQuery(query);
    async function executeSearch() {
      setLoading(true);
      try {
        const res = await productService.getProducts({
          search: query,
          limit: 24,
        });
        setProducts(res.items);
      } catch (err) {
        console.error("Search error", err);
      } finally {
        setLoading(false);
      }
    }
    executeSearch();
  }, [query]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(inputQuery.trim())}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb
        items={[
          { label: "Search", href: "/search" },
          { label: query ? `"${query}"` : "All" },
        ]}
      />

      {/* Search Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-brand-900 to-emerald-950 text-white shadow-md">
        <h1 className="text-2xl sm:text-3xl font-black mb-2">Search Cartify</h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-xl mb-4">
          Find produce, dairy, bakery items, or specialty pantry brands with instant 15-min delivery.
        </p>

        <form onSubmit={handleSearchSubmit} className="relative max-w-xl">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Search groceries, brands, or ingredients..."
            className="w-full h-12 pl-12 pr-28 rounded-2xl bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-brand-500/20 shadow-lg"
          />
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <button
            type="submit"
            className="absolute right-2 top-2 bottom-2 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold transition-colors"
          >
            Search
          </button>
        </form>

        {/* Popular chips */}
        <div className="flex items-center gap-2 flex-wrap pt-4 text-xs">
          <span className="text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-accent-400" /> Popular:
          </span>
          {TRENDING_SEARCHES.map((item) => (
            <button
              key={item}
              onClick={() => router.push(`/search?q=${encodeURIComponent(item)}`)}
              className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 transition-colors text-[11px]"
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      {/* Search Result Count */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <h2 className="text-lg font-bold text-slate-900">
          {query ? `Results for "${query}"` : "Search Results"}
        </h2>
        <span className="text-xs text-slate-500 font-medium">
          {products.length} {products.length === 1 ? "product found" : "products found"}
        </span>
      </div>

      {/* Grid */}
      <ProductGrid
        products={products}
        isLoading={loading}
        emptyTitle={`No results found for "${query}"`}
        emptyDescription="Please check your spelling or search for broader terms like 'milk', 'bread', 'fruit', or 'organic'."
      />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading search...</div>}>
      <SearchContent />
    </Suspense>
  );
}
