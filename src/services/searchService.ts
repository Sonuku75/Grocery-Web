/**
 * Search & Product Discovery Service (Module 5)
 * 
 * Supports both Live FastAPI backend and local Mock mode.
 * Centralizes all search and autocomplete requests.
 */

import { apiClient, isMockMode } from "@/lib/api/client";
import { MOCK_PRODUCTS } from "@/lib/mockData";
import {
  Product,
  SearchParams,
  SearchProduct,
  SearchResponse,
  SearchSortOption,
  SearchSuggestion,
  SearchSuggestionResponse,
} from "@/types";
import { normalizeProduct } from "./productService";

/**
 * Normalizes an API search product payload into standard SearchProduct
 */
export function normalizeSearchProduct(raw: any): SearchProduct {
  const price = Number(raw.price || 0);
  const mrp = Number(raw.mrp || raw.originalPrice || price);
  const discountPercentage = Number(
    raw.discountPercentage ??
    raw.discount_percentage ??
    (mrp > price ? Math.round(((mrp - price) / mrp) * 100) : 0)
  );

  return {
    id: String(raw.id),
    name: String(raw.name || ""),
    slug: String(raw.slug || ""),
    brand: String(raw.brand || ""),
    imageUrl: raw.imageUrl || raw.image_url || "/placeholder-product.png",
    image_url: raw.image_url || raw.imageUrl,
    price,
    mrp,
    discountPercentage,
    discount_percentage: discountPercentage,
    unit: raw.unit || "1 unit",
    isFeatured: Boolean(raw.isFeatured ?? raw.is_featured ?? false),
    is_featured: Boolean(raw.is_featured ?? raw.isFeatured ?? false),
    category: raw.category
      ? {
          id: String(raw.category.id),
          name: String(raw.category.name),
          slug: String(raw.category.slug),
        }
      : undefined,
  };
}

/**
 * Converts a SearchProduct into a standard Product model for reuse with ProductCard
 */
export function searchProductToProduct(sp: SearchProduct): Product {
  return normalizeProduct({
    id: sp.id,
    name: sp.name,
    slug: sp.slug,
    brand: sp.brand,
    price: sp.price,
    mrp: sp.mrp,
    originalPrice: sp.mrp,
    discountPercentage: sp.discountPercentage,
    discountPercent: sp.discountPercentage,
    unit: sp.unit || "1 unit",
    imageUrl: sp.imageUrl || sp.image_url,
    isFeatured: sp.isFeatured,
    categoryId: sp.category?.id,
    categoryName: sp.category?.name,
    categorySlug: sp.category?.slug,
    inStock: true,
  });
}

/**
 * Executes a simulated client-side search across mock products
 */
function searchMockProducts(params: SearchParams): SearchResponse {
  const query = (params.q || "").trim().toLowerCase();
  let items = [...MOCK_PRODUCTS].map(normalizeProduct);

  // 1. Keyword search and relevance scoring
  let scoredItems: { product: Product; score: number }[] = [];

  if (query) {
    for (const p of items) {
      const nameLower = p.name.toLowerCase();
      const brandLower = p.brand.toLowerCase();
      const catLower = (p.categoryName || "").toLowerCase();

      let score = 0;
      if (nameLower === query) score = 100;
      else if (nameLower.startsWith(query)) score = 80;
      else if (nameLower.includes(query)) score = 60;
      else if (brandLower === query) score = 50;
      else if (brandLower.includes(query)) score = 40;
      else if (catLower.includes(query)) score = 20;

      if (score > 0) {
        scoredItems.push({ product: p, score });
      }
    }
  } else {
    scoredItems = items.map((p) => ({ product: p, score: 0 }));
  }

  // 2. Category filtering
  const targetCategory = params.category_id || params.categoryId;
  if (targetCategory && targetCategory !== "all") {
    scoredItems = scoredItems.filter(
      (item) =>
        item.product.categoryId === targetCategory ||
        item.product.categorySlug === targetCategory
    );
  }

  // 3. Brand filtering
  if (params.brand && params.brand !== "all") {
    const bLower = params.brand.toLowerCase();
    scoredItems = scoredItems.filter(
      (item) => item.product.brand.toLowerCase() === bLower
    );
  }

  // 4. Price range filtering
  const minPrice = params.min_price ?? params.minPrice;
  if (minPrice !== undefined) {
    scoredItems = scoredItems.filter((item) => item.product.price >= minPrice);
  }

  const maxPrice = params.max_price ?? params.maxPrice;
  if (maxPrice !== undefined) {
    scoredItems = scoredItems.filter((item) => item.product.price <= maxPrice);
  }

  // 5. Sorting
  const sort = params.sort || "relevance";
  if (sort === "price_low_to_high") {
    scoredItems.sort((a, b) => a.product.price - b.product.price);
  } else if (sort === "price_high_to_low") {
    scoredItems.sort((a, b) => b.product.price - a.product.price);
  } else if (sort === "newest") {
    scoredItems.sort((a, b) => (b.product.createdAt || "").localeCompare(a.product.createdAt || ""));
  } else if (sort === "featured") {
    scoredItems.sort((a, b) => (b.product.isFeatured ? 1 : 0) - (a.product.isFeatured ? 1 : 0));
  } else {
    // Default relevance
    scoredItems.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (b.product.isFeatured ? 1 : 0) - (a.product.isFeatured ? 1 : 0);
    });
  }

  const total = scoredItems.length;
  const limit = params.limit || 20;
  const sliced = scoredItems.slice(0, limit);

  const searchProducts: SearchProduct[] = sliced.map(({ product: p }) => ({
    id: p.id,
    name: p.name,
    slug: p.slug || p.id,
    brand: p.brand,
    imageUrl: p.imageUrl,
    image_url: p.imageUrl,
    price: p.price,
    mrp: p.originalPrice ?? p.price,
    discountPercentage: p.discountPercentage ?? p.discountPercent ?? 0,
    unit: p.unit,
    isFeatured: p.isFeatured,
    category: p.categoryId
      ? {
          id: p.categoryId,
          name: p.categoryName || "Grocery",
          slug: p.categorySlug || "grocery",
        }
      : undefined,
  }));

  return {
    query: params.q,
    items: searchProducts,
    total,
    hasMore: total > limit,
    has_more: total > limit,
  };
}

/**
 * Generates local mock autocomplete suggestions
 */
function getMockSuggestions(query: string, limit: number = 8): SearchSuggestionResponse {
  const cleanQ = query.trim().toLowerCase();
  if (!cleanQ) return { items: [] };

  const suggestions: SearchSuggestion[] = [];

  // Product matches
  for (const p of MOCK_PRODUCTS) {
    if (p.name.toLowerCase().includes(cleanQ)) {
      suggestions.push({
        type: "product",
        label: p.name,
        slug: p.slug || p.id,
        id: p.id,
        price: p.price,
        imageUrl: p.imageUrl,
      });
      if (suggestions.length >= limit) return { items: suggestions };
    }
  }

  // Brand matches
  const brands: string[] = Array.from(new Set(MOCK_PRODUCTS.map((p) => p.brand).filter(Boolean)));
  for (const b of brands) {
    if (b.toLowerCase().includes(cleanQ)) {
      suggestions.push({
        type: "brand",
        label: b,
      });
      if (suggestions.length >= limit) return { items: suggestions };
    }
  }

  return { items: suggestions };
}

/**
 * Search API Client for Cartify (Web, Android, iOS)
 */
export const searchService = {
  /**
   * Searches products with relevance ranking, filters, and cursor pagination
   */
  async search(params: SearchParams): Promise<SearchResponse> {
    if (!isMockMode()) {
      try {
        const queryParams: Record<string, any> = {
          q: params.q,
          category_id: params.category_id || params.categoryId,
          brand: params.brand,
          min_price: params.min_price ?? params.minPrice,
          max_price: params.max_price ?? params.maxPrice,
          sort: params.sort || "relevance",
          cursor: params.cursor,
          limit: params.limit || 20,
        };

        const res = await apiClient.get<SearchResponse>("/search", { params: queryParams });
        if (res.success && res.data) {
          const rawItems = res.data.items || [];
          return {
            query: res.data.query,
            items: rawItems.map(normalizeSearchProduct),
            nextCursor: res.data.nextCursor || res.data.next_cursor,
            next_cursor: res.data.next_cursor || res.data.nextCursor,
            hasMore: Boolean(res.data.hasMore ?? res.data.has_more),
            has_more: Boolean(res.data.has_more ?? res.data.hasMore),
            total: res.data.total ?? rawItems.length,
          };
        }
      } catch (err) {
        console.warn("Live search API unavailable, falling back to mock:", err);
      }
    }

    return searchMockProducts(params);
  },

  /**
   * Retrieves debounced autocomplete suggestions
   */
  async getSuggestions(query: string, limit: number = 8): Promise<SearchSuggestionResponse> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<SearchSuggestionResponse>("/search/suggestions", {
          params: { q: query.trim(), limit },
        });
        if (res.success && res.data) {
          return res.data;
        }
      } catch (err) {
        console.warn("Live suggestions API unavailable, falling back to mock:", err);
      }
    }

    return getMockSuggestions(query, limit);
  },
};
