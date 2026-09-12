import { apiClient, isMockMode } from "@/lib/api";
import { Category, CategoryInput, CategoryListResponse } from "@/types";
import { MOCK_CATEGORIES } from "@/lib/mockData";

function normalizeCategory(cat: any): Category {
  return {
    id: cat.id,
    slug: cat.slug,
    name: cat.name,
    description: cat.description || "",
    icon: cat.icon || "Compass",
    imageUrl: cat.imageUrl || cat.image_url || "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&auto=format&fit=crop&q=80",
    image_url: cat.image_url || cat.imageUrl,
    parentId: cat.parentId ?? cat.parent_id ?? null,
    parent_id: cat.parent_id ?? cat.parentId ?? null,
    sortOrder: cat.sortOrder ?? cat.sort_order ?? 0,
    sort_order: cat.sort_order ?? cat.sortOrder ?? 0,
    isActive: cat.isActive ?? cat.is_active ?? true,
    is_active: cat.is_active ?? cat.isActive ?? true,
    itemCount: cat.itemCount ?? cat.item_count ?? 30,
    subcategories: Array.isArray(cat.subcategories)
      ? cat.subcategories.map(normalizeCategory)
      : undefined,
    createdAt: cat.createdAt || cat.created_at,
    updatedAt: cat.updatedAt || cat.updated_at,
  };
}

export const categoryService = {
  async getCategories(includeSubcategories = false): Promise<Category[]> {
    if (!isMockMode()) {
      try {
        const query = includeSubcategories ? "?includeSubcategories=true" : "";
        const res = await apiClient.get<CategoryListResponse | Category[]>(`/categories${query}`);
        if (res.success && res.data) {
          const rawItems = Array.isArray(res.data)
            ? res.data
            : (res.data as CategoryListResponse).items || [];
          if (rawItems.length > 0) {
            return rawItems.map(normalizeCategory);
          }
        }
      } catch (err) {
        console.warn("API categories fetch failed, falling back to mock data:", err);
      }
    }
    return MOCK_CATEGORIES.map(normalizeCategory);
  },

  async getCategoryBySlug(slug: string): Promise<Category | null> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<Category>(`/categories/slug/${slug}`);
        if (res.success && res.data) {
          return normalizeCategory(res.data);
        }
      } catch (err) {
        console.warn(`API getCategoryBySlug('${slug}') failed, falling back to mock:`, err);
      }
    }
    const found = MOCK_CATEGORIES.find((c) => c.slug === slug || c.id === slug);
    return found ? normalizeCategory(found) : null;
  },

  async getCategoryById(id: string): Promise<Category | null> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<Category>(`/categories/${id}`);
        if (res.success && res.data) {
          return normalizeCategory(res.data);
        }
      } catch (err) {
        console.warn(`API getCategoryById('${id}') failed, falling back to mock:`, err);
      }
    }
    const found = MOCK_CATEGORIES.find((c) => c.id === id || c.slug === id);
    return found ? normalizeCategory(found) : null;
  },

  async getSubcategories(categoryId: string): Promise<Category[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<CategoryListResponse | Category[]>(
          `/categories/${categoryId}/subcategories`
        );
        if (res.success && res.data) {
          const rawItems = Array.isArray(res.data)
            ? res.data
            : (res.data as CategoryListResponse).items || [];
          return rawItems.map(normalizeCategory);
        }
      } catch (err) {
        console.warn(`API getSubcategories('${categoryId}') failed:`, err);
      }
    }
    return [];
  },

  // Admin APIs
  async createCategory(payload: CategoryInput): Promise<Category> {
    const res = await apiClient.post<Category>("/admin/categories", payload);
    if (!res.success || !res.data) {
      throw new Error(res.error || "Failed to create category");
    }
    return normalizeCategory(res.data);
  },

  async updateCategory(id: string, payload: Partial<CategoryInput>): Promise<Category> {
    const res = await apiClient.patch<Category>(`/admin/categories/${id}`, payload);
    if (!res.success || !res.data) {
      throw new Error(res.error || "Failed to update category");
    }
    return normalizeCategory(res.data);
  },

  async deleteCategory(id: string, hardDelete = false): Promise<void> {
    const res = await apiClient.delete(`/admin/categories/${id}?hard_delete=${hardDelete}`);
    if (!res.success) {
      throw new Error(res.error || "Failed to delete category");
    }
  },
};

