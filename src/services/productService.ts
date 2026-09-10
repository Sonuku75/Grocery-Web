import { apiClient } from "@/lib/api";
import { Product, ProductFilters, PaginatedResponse, ProductReview } from "@/types";
import { MOCK_PRODUCTS, MOCK_REVIEWS } from "@/lib/mockData";

export const productService = {
  async getProducts(filters: ProductFilters = {}): Promise<PaginatedResponse<Product>> {
    const params: Record<string, string | number | boolean | undefined> = {
      category: filters.category,
      min_price: filters.minPrice,
      max_price: filters.maxPrice,
      min_rating: filters.minRating,
      brand: filters.brand,
      in_stock: filters.inStock,
      search: filters.search,
      sort: filters.sortBy,
      page: filters.page || 1,
      limit: filters.limit || 12,
    };

    const res = await apiClient.get<PaginatedResponse<Product>>("/products", { params });
    if (res.success && res.data && res.data.items) {
      return res.data;
    }

    // Fallback: Local filtering on mock products
    let items = [...MOCK_PRODUCTS];

    if (filters.category && filters.category !== "all") {
      items = items.filter(
        (p) => p.categoryId === filters.category || p.slug === filters.category
      );
    }

    if (filters.search) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.brand.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q)) ||
          (p.categoryName && p.categoryName.toLowerCase().includes(q))
      );
    }

    if (filters.brand) {
      items = items.filter((p) => p.brand.toLowerCase() === filters.brand?.toLowerCase());
    }

    if (filters.minPrice !== undefined) {
      items = items.filter((p) => p.price >= (filters.minPrice ?? 0));
    }

    if (filters.maxPrice !== undefined) {
      items = items.filter((p) => p.price <= (filters.maxPrice ?? 9999));
    }

    if (filters.minRating !== undefined) {
      items = items.filter((p) => p.rating >= (filters.minRating ?? 0));
    }

    if (filters.inStock) {
      items = items.filter((p) => p.inStock);
    }

    // Sorting
    switch (filters.sortBy) {
      case "price_asc":
        items.sort((a, b) => a.price - b.price);
        break;
      case "price_desc":
        items.sort((a, b) => b.price - a.price);
        break;
      case "rating":
        items.sort((a, b) => b.rating - a.rating);
        break;
      case "popular":
        items.sort((a, b) => (b.isPopular ? 1 : 0) - (a.isPopular ? 1 : 0));
        break;
      case "newest":
      default:
        // natural order
        break;
    }

    const page = filters.page || 1;
    const limit = filters.limit || 12;
    const total = items.length;
    const totalPages = Math.ceil(total / limit);
    const paginatedItems = items.slice((page - 1) * limit, page * limit);

    return {
      items: paginatedItems,
      total,
      page,
      pageSize: limit,
      totalPages,
    };
  },

  async getProductById(idOrSlug: string): Promise<Product | null> {
    const res = await apiClient.get<Product>(`/products/${idOrSlug}`);
    if (res.success && res.data) {
      return res.data;
    }

    const found = MOCK_PRODUCTS.find((p) => p.id === idOrSlug || p.slug === idOrSlug);
    return found || null;
  },

  async getFeaturedProducts(): Promise<Product[]> {
    const res = await apiClient.get<Product[]>("/products/featured");
    if (res.success && res.data && res.data.length > 0) {
      return res.data;
    }
    return MOCK_PRODUCTS.filter((p) => p.isFeatured || p.isPopular).slice(0, 8);
  },

  async getDeals(): Promise<Product[]> {
    const res = await apiClient.get<Product[]>("/products/deals");
    if (res.success && res.data && res.data.length > 0) {
      return res.data;
    }
    return MOCK_PRODUCTS.filter((p) => p.isDeal || p.discountPercent >= 15).slice(0, 8);
  },

  async getRelatedProducts(categoryId: string, excludeId: string): Promise<Product[]> {
    const res = await apiClient.get<Product[]>(`/products/related`, {
      params: { categoryId, excludeId },
    });
    if (res.success && res.data && res.data.length > 0) {
      return res.data;
    }
    return MOCK_PRODUCTS.filter((p) => p.id !== excludeId && p.categoryId === categoryId).slice(0, 4);
  },

  async getProductReviews(productId: string): Promise<ProductReview[]> {
    const res = await apiClient.get<ProductReview[]>(`/products/${productId}/reviews`);
    if (res.success && res.data && res.data.length > 0) {
      return res.data;
    }
    const specific = MOCK_REVIEWS.filter((r) => r.productId === productId);
    return specific.length > 0 ? specific : MOCK_REVIEWS;
  },
};
