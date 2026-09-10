"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Product, Category, ProductFilters } from "@/types";
import { productService } from "@/services/productService";
import { categoryService } from "@/services/categoryService";
import { ProductGrid } from "@/components/products/ProductGrid";
import { Pagination } from "@/components/common/Pagination";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { SlidersHorizontal, ArrowUpDown, X, Star } from "lucide-react";

function ProductsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialCategory = searchParams.get("category") || "all";
  const initialSort = (searchParams.get("sort") as ProductFilters["sortBy"]) || "relevance";
  const initialPage = Number(searchParams.get("page")) || 1;

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Filters State
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory);
  const [selectedSort, setSelectedSort] = useState<ProductFilters["sortBy"]>(initialSort);
  const [selectedRating, setSelectedRating] = useState<number | undefined>(undefined);
  const [priceRange, setPriceRange] = useState<{ min?: number; max?: number }>({});
  const [inStockOnly, setInStockOnly] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(initialPage);
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState<boolean>(false);

  useEffect(() => {
    async function loadCategories() {
      const cats = await categoryService.getCategories();
      setCategories(cats);
    }
    loadCategories();
  }, []);

  useEffect(() => {
    async function fetchFilteredProducts() {
      setLoading(true);
      try {
        const res = await productService.getProducts({
          category: selectedCategory === "all" ? undefined : selectedCategory,
          sortBy: selectedSort,
          minRating: selectedRating,
          minPrice: priceRange.min,
          maxPrice: priceRange.max,
          inStock: inStockOnly ? true : undefined,
          page: currentPage,
          limit: 12,
        });

        setProducts(res.items);
        setTotalPages(res.totalPages);
        setTotalCount(res.total);
      } catch (err) {
        console.error("Error fetching products", err);
      } finally {
        setLoading(false);
      }
    }

    fetchFilteredProducts();
  }, [selectedCategory, selectedSort, selectedRating, priceRange, inStockOnly, currentPage]);

  const handleCategoryChange = (catId: string) => {
    setSelectedCategory(catId);
    setCurrentPage(1);
    router.push(`/products?category=${catId}`, { scroll: false });
  };

  const handleClearFilters = () => {
    setSelectedCategory("all");
    setSelectedSort("relevance");
    setSelectedRating(undefined);
    setPriceRange({});
    setInStockOnly(false);
    setCurrentPage(1);
    router.push("/products", { scroll: false });
  };

  const activeFiltersCount =
    (selectedCategory !== "all" ? 1 : 0) +
    (selectedRating ? 1 : 0) +
    (priceRange.min !== undefined || priceRange.max !== undefined ? 1 : 0) +
    (inStockOnly ? 1 : 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Breadcrumb items={[{ label: "Products", href: "/products" }]} />

      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6 border-b border-slate-100">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            All Fresh Groceries & Essentials
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Showing {totalCount} quality products ready for immediate 15-min delivery
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Mobile Filter Button */}
          <button
            onClick={() => setIsMobileFilterOpen(true)}
            className="lg:hidden flex items-center gap-2 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
          >
            <SlidersHorizontal className="w-4 h-4 text-brand-600" />
            <span>Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}</span>
          </button>

          {/* Sorting Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 hidden sm:inline">Sort:</span>
            <select
              value={selectedSort}
              onChange={(e) => {
                setSelectedSort(e.target.value as ProductFilters["sortBy"]);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl text-slate-700 shadow-xs focus:outline-none focus:border-brand-500"
            >
              <option value="relevance">Relevance</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="rating">Highest Rated</option>
              <option value="popular">Most Popular</option>
              <option value="newest">Newest Arrivals</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Layout (Sidebar + Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pt-6">
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <span className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-brand-600" />
              Filter Catalog
            </span>
            {activeFiltersCount > 0 && (
              <button
                onClick={handleClearFilters}
                className="text-xs font-semibold text-rose-600 hover:underline"
              >
                Reset all
              </button>
            )}
          </div>

          {/* Categories */}
          <div>
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
              Categories
            </h3>
            <div className="space-y-1">
              <button
                onClick={() => handleCategoryChange("all")}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between ${
                  selectedCategory === "all"
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>All Categories</span>
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryChange(cat.id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between ${
                    selectedCategory === cat.id
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span className="truncate">{cat.name}</span>
                  {cat.itemCount && (
                    <span className="text-[10px] text-slate-400 font-normal">
                      {cat.itemCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Price Range */}
          <div className="pt-4 border-t border-slate-100">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
              Price Range ($)
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                placeholder="Min ($)"
                value={priceRange.min !== undefined ? priceRange.min : ""}
                onChange={(e) =>
                  setPriceRange({
                    ...priceRange,
                    min: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-white"
              />
              <input
                type="number"
                placeholder="Max ($)"
                value={priceRange.max !== undefined ? priceRange.max : ""}
                onChange={(e) =>
                  setPriceRange({
                    ...priceRange,
                    max: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-white"
              />
            </div>
          </div>

          {/* Customer Rating Filter */}
          <div className="pt-4 border-t border-slate-100">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
              Customer Rating
            </h3>
            <div className="space-y-1.5">
              {[4.5, 4.0, 3.5].map((rating) => (
                <label
                  key={rating}
                  className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer hover:text-slate-900"
                >
                  <input
                    type="radio"
                    name="ratingFilter"
                    checked={selectedRating === rating}
                    onChange={() => setSelectedRating(rating)}
                    className="text-brand-600 focus:ring-brand-500 rounded"
                  />
                  <div className="flex items-center gap-1 text-amber-400">
                    <Star className="w-3.5 h-3.5 fill-amber-400" />
                    <span className="font-semibold text-slate-800">{rating} & above</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* In Stock Toggle */}
          <div className="pt-4 border-t border-slate-100">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs font-bold text-slate-700">In-Stock Only</span>
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => setInStockOnly(e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
              />
            </label>
          </div>
        </aside>

        {/* Products Grid & Pagination */}
        <div className="lg:col-span-3 space-y-8">
          <ProductGrid products={products} isLoading={loading} />

          <div className="pt-4 flex justify-center">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={(page) => {
                setCurrentPage(page);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            />
          </div>
        </div>
      </div>

      {/* Mobile Filters Drawer Modal */}
      {isMobileFilterOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs"
            onClick={() => setIsMobileFilterOpen(false)}
          />
          <div className="relative ml-auto w-full max-w-xs bg-white h-full p-6 flex flex-col justify-between shadow-2xl z-10 overflow-y-auto">
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-base font-bold text-slate-900">Filters</span>
                <button
                  onClick={() => setIsMobileFilterOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Categories */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase mb-2">Category</h4>
                <div className="space-y-1">
                  <button
                    onClick={() => {
                      handleCategoryChange("all");
                      setIsMobileFilterOpen(false);
                    }}
                    className="w-full text-left py-1.5 text-xs font-semibold text-slate-700"
                  >
                    All Categories
                  </button>
                  {categories.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => {
                        handleCategoryChange(cat.id);
                        setIsMobileFilterOpen(false);
                      }}
                      className="w-full text-left py-1.5 text-xs font-medium text-slate-600"
                    >
                      {cat.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                fullWidth
                onClick={() => {
                  handleClearFilters();
                  setIsMobileFilterOpen(false);
                }}
              >
                Clear
              </Button>
              <Button
                variant="primary"
                size="sm"
                fullWidth
                onClick={() => setIsMobileFilterOpen(false)}
              >
                Apply Filters
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading catalog...</div>}>
      <ProductsContent />
    </Suspense>
  );
}
