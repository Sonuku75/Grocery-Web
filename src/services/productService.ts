import { apiClient, isMockMode } from "@/lib/api";
import {
  Product,
  ProductFilters,
  PaginatedResponse,
  ProductReview,
  ProductVariant,
  ProductImage,
} from "@/types";
import { MOCK_PRODUCTS, MOCK_REVIEWS } from "@/lib/mockData";

/**
 * Normalizes backend Product models / API responses to ensure complete UI compatibility.
 */
export function normalizeProduct(raw: any): Product {
  if (!raw) return raw;

  // Extract raw image URLs from images array or object list
  let images: string[] = [];
  if (Array.isArray(raw.images) && raw.images.length > 0) {
    images = raw.images.map((img: any) => (typeof img === "string" ? img : img.imageUrl || img.image_url));
  } else if (raw.imageUrl || raw.image_url) {
    images = [raw.imageUrl || raw.image_url];
  } else {
    images = ["https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800"];
  }

  // Normalize variants list
  const rawVariants: any[] = Array.isArray(raw.variants) ? raw.variants : [];
  const variants: ProductVariant[] = rawVariants.map((v: any) => ({
    id: v.id,
    productId: v.productId || v.product_id,
    sku: v.sku,
    name: v.name,
    unitValue: Number(v.unitValue ?? v.unit_value ?? 1),
    unitType: v.unitType || v.unit_type || "unit",
    price: Number(v.price),
    mrp: Number(v.mrp || v.originalPrice || v.price),
    discountPercentage: Number(v.discountPercentage ?? v.discount_percentage ?? 0),
    isActive: v.isActive ?? v.is_active ?? true,
    sortOrder: v.sortOrder ?? v.sort_order ?? 0,
    createdAt: v.createdAt || v.created_at,
    updatedAt: v.updatedAt || v.updated_at,
  }));

  const primaryVariant =
    raw.primaryVariant ||
    raw.primary_variant ||
    (variants.length > 0 ? variants[0] : undefined);

  const price = Number(
    raw.price ??
      raw.minPrice ??
      raw.min_price ??
      primaryVariant?.price ??
      0
  );

  const originalPrice = Number(
    raw.originalPrice ??
      raw.mrp ??
      raw.minMrp ??
      raw.min_mrp ??
      primaryVariant?.mrp ??
      price
  );

  const discountPercent = Number(
    raw.discountPercent ??
      raw.discountPercentage ??
      raw.maxDiscountPercentage ??
      raw.max_discount_percentage ??
      primaryVariant?.discountPercentage ??
      0
  );

  const unit =
    raw.unit ||
    (primaryVariant
      ? `${primaryVariant.unitValue} ${primaryVariant.unitType}`
      : "1 unit");

  return {
    id: raw.id,
    slug: raw.slug || raw.id,
    name: raw.name,
    brand: raw.brand || "Cartify Select",
    categoryId: raw.categoryId || raw.category_id,
    category_id: raw.category_id || raw.categoryId,
    categoryName: raw.categoryName || raw.category_name || (raw.category ? raw.category.name : undefined),
    category_name: raw.category_name || raw.categoryName,
    categorySlug: raw.categorySlug || raw.category_slug || (raw.category ? raw.category.slug : undefined),
    category_slug: raw.category_slug || raw.categorySlug,
    category: raw.category,
    description: raw.description || "",
    shortDescription: raw.shortDescription || raw.short_description,
    short_description: raw.short_description || raw.shortDescription,
    specifications: raw.specifications || {},
    price,
    originalPrice,
    mrp: originalPrice,
    discountPercent,
    discountPercentage: discountPercent,
    unit,
    stock: raw.stock ?? 10,
    rating: Number(raw.rating ?? raw.averageRating ?? raw.average_rating ?? 0),
    ratingCount: Number(raw.ratingCount ?? raw.rating_count ?? raw.totalReviews ?? raw.total_reviews ?? 0),
    imageUrl: raw.imageUrl || raw.image_url || images[0],
    image_url: raw.image_url || raw.imageUrl || images[0],
    images,
    variants,
    primaryVariant,
    isPopular: raw.isPopular ?? false,
    isFeatured: raw.isFeatured ?? raw.is_featured ?? false,
    is_featured: raw.is_featured ?? raw.isFeatured ?? false,
    isDeal: raw.isDeal ?? discountPercent >= 10,
    tags: raw.tags || [],
    inStock: raw.inStock ?? raw.in_stock ?? true,
    isActive: raw.isActive ?? raw.is_active ?? true,
    is_active: raw.is_active ?? raw.isActive ?? true,
    createdAt: raw.createdAt || raw.created_at,
    updatedAt: raw.updatedAt || raw.updated_at,
  };
}

/**
 * Filter & paginate mock products locally in mock mode
 */
function queryMockProducts(filters: ProductFilters = {}): PaginatedResponse<Product> {
  let items = [...MOCK_PRODUCTS].map(normalizeProduct);

  const targetCategory = filters.category || (filters as any).categoryId;
  if (targetCategory && targetCategory !== "all") {
    items = items.filter(
      (p) => p.categoryId === targetCategory || p.slug === targetCategory || p.categorySlug === targetCategory
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

  const sortVal = filters.sortBy || (filters as any).sort;
  switch (sortVal) {
    case "price_asc":
    case "price_low_to_high":
      items.sort((a, b) => a.price - b.price);
      break;
    case "price_desc":
    case "price_high_to_low":
      items.sort((a, b) => b.price - a.price);
      break;
    case "rating":
      items.sort((a, b) => b.rating - a.rating);
      break;
    case "popular":
    case "featured":
      items.sort((a, b) => (b.isFeatured ? 1 : 0) - (a.isFeatured ? 1 : 0));
      break;
    case "newest":
    default:
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
}

/**
 * Product Data & Service Layer (Module 4)
 * 
 * Supports both Mock and Live REST API modes:
 * - Mock mode (default): serves data locally without failing HTTP requests.
 * - Live REST API mode: automatically delegates to Python FastAPI endpoints when NEXT_PUBLIC_USE_MOCK=false.
 */
export const productService = {
  async getProducts(filters: ProductFilters = {}): Promise<PaginatedResponse<Product>> {
    if (!isMockMode()) {
      const sortMap: Record<string, string> = {
        price_asc: "price_low_to_high",
        price_desc: "price_high_to_low",
        popular: "featured",
        newest: "newest",
        featured: "featured",
      };

      const rawSort = filters.sortBy || (filters as any).sort || "newest";
      const normalizedSort = sortMap[rawSort] || (rawSort === "price_low_to_high" || rawSort === "price_high_to_low" || rawSort === "featured" ? rawSort : "newest");

      const params: Record<string, any> = {
        category_id: filters.category || (filters as any).categoryId,
        subcategory_id: (filters as any).subcategoryId || (filters as any).subcategory_id,
        brand: filters.brand,
        sort: normalizedSort,
        limit: filters.limit || 20,
        cursor: (filters as any).cursor,
      };

      try {
        const res = await apiClient.get<any>("/products", { params });
        if (res.success && res.data) {
          const rawItems = res.data.items || [];
          const normalizedItems = rawItems.map(normalizeProduct);
          return {
            items: normalizedItems,
            total: res.data.total ?? normalizedItems.length,
            page: filters.page || 1,
            pageSize: filters.limit || 20,
            totalPages: Math.ceil((res.data.total ?? normalizedItems.length) / (filters.limit || 20)),
          };
        }
      } catch (err) {
        console.warn("Live products API unavailable, falling back to mock:", err);
      }
    }

    return queryMockProducts(filters);
  },

  async getProduct(id: string): Promise<Product | null> {
    return this.getProductById(id);
  },

  async getProductById(id: string): Promise<Product | null> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>(`/products/${id}`);
        if (res.success && res.data) {
          return normalizeProduct(res.data);
        }
      } catch (err) {
        console.warn(`Product ID ${id} not found on live API, trying fallback:`, err);
      }
    }

    const found = MOCK_PRODUCTS.find((p) => p.id === id || p.slug === id);
    return found ? normalizeProduct(found) : null;
  },

  async getProductBySlug(slug: string): Promise<Product | null> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>(`/products/slug/${slug}`);
        if (res.success && res.data) {
          return normalizeProduct(res.data);
        }
      } catch (err) {
        // If lookup by slug failed, the param might be a raw UUID
        try {
          const resId = await apiClient.get<any>(`/products/${slug}`);
          if (resId.success && resId.data) {
            return normalizeProduct(resId.data);
          }
        } catch {
          // ignore secondary error
        }
        console.warn(`Product slug ${slug} not found on live API, trying fallback:`, err);
      }
    }

    const found = MOCK_PRODUCTS.find((p) => p.slug === slug || p.id === slug);
    return found ? normalizeProduct(found) : null;
  },

  async getFeaturedProducts(): Promise<Product[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>("/products", {
          params: { featured: true, limit: 8 },
        });
        if (res.success && res.data?.items && res.data.items.length > 0) {
          return res.data.items.map(normalizeProduct);
        }
      } catch (err) {
        console.warn("Failed to fetch featured products from live API:", err);
      }
    }
    return MOCK_PRODUCTS.filter((p) => p.isFeatured || p.isPopular).slice(0, 8).map(normalizeProduct);
  },

  async getDeals(): Promise<Product[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>("/products", {
          params: { sort: "featured", limit: 8 },
        });
        if (res.success && res.data?.items && res.data.items.length > 0) {
          return res.data.items.map(normalizeProduct);
        }
      } catch (err) {
        console.warn("Failed to fetch deals from live API:", err);
      }
    }
    return MOCK_PRODUCTS.filter((p) => p.isDeal || p.discountPercent >= 15).slice(0, 8).map(normalizeProduct);
  },

  async getRelatedProducts(categoryId: string, excludeId: string): Promise<Product[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>("/products", {
          params: { category_id: categoryId, limit: 5 },
        });
        if (res.success && res.data?.items) {
          return res.data.items
            .filter((p: any) => p.id !== excludeId)
            .slice(0, 4)
            .map(normalizeProduct);
        }
      } catch (err) {
        console.warn("Failed to fetch related products from live API:", err);
      }
    }
    return MOCK_PRODUCTS.filter((p) => p.id !== excludeId && p.categoryId === categoryId).slice(0, 4).map(normalizeProduct);
  },

  async getProductReviews(productId: string): Promise<ProductReview[]> {
    const specific = MOCK_REVIEWS.filter((r) => r.productId === productId);
    return specific.length > 0 ? specific : MOCK_REVIEWS;
  },

  // ---------------------------------------------------------------------------
  // Admin Operations (Module 4)
  // ---------------------------------------------------------------------------
  async createProduct(data: any): Promise<Product> {
    const res = await apiClient.post<any>("/admin/products", data);
    return normalizeProduct(res.data);
  },

  async updateProduct(productId: string, data: any): Promise<Product> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}`, data);
    return normalizeProduct(res.data);
  },

  async updateProductStatus(productId: string, isActive: boolean): Promise<Product> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}/status`, { is_active: isActive });
    return normalizeProduct(res.data);
  },

  async createVariant(productId: string, data: any): Promise<ProductVariant> {
    const res = await apiClient.post<any>(`/admin/products/${productId}/variants`, data);
    return res.data;
  },

  async updateVariant(productId: string, variantId: string, data: any): Promise<ProductVariant> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}/variants/${variantId}`, data);
    return res.data;
  },

  async updateVariantStatus(productId: string, variantId: string, isActive: boolean): Promise<ProductVariant> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}/variants/${variantId}/status`, { is_active: isActive });
    return res.data;
  },

  async addProductImage(productId: string, data: any): Promise<ProductImage> {
    const res = await apiClient.post<any>(`/admin/products/${productId}/images`, data);
    return res.data;
  },

  async updateProductImage(productId: string, imageId: string, data: any): Promise<ProductImage> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}/images/${imageId}`, data);
    return res.data;
  },

  async setPrimaryProductImage(productId: string, imageId: string): Promise<ProductImage> {
    const res = await apiClient.patch<any>(`/admin/products/${productId}/images/${imageId}/primary`, {});
    return res.data;
  },

  async deleteProductImage(productId: string, imageId: string): Promise<void> {
    await apiClient.delete(`/admin/products/${productId}/images/${imageId}`);
  },
};

export const productApi = productService;
