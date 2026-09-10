import { apiClient, isMockMode } from "@/lib/api";
import { Category } from "@/types";
import { MOCK_CATEGORIES } from "@/lib/mockData";

export const categoryService = {
  async getCategories(): Promise<Category[]> {
    if (!isMockMode()) {
      const res = await apiClient.get<Category[]>("/categories");
      if (res.success && res.data && res.data.length > 0) {
        return res.data;
      }
    }
    return MOCK_CATEGORIES;
  },

  async getCategoryBySlug(slug: string): Promise<Category | null> {
    if (!isMockMode()) {
      const res = await apiClient.get<Category>(`/categories/${slug}`);
      if (res.success && res.data) {
        return res.data;
      }
    }
    const found = MOCK_CATEGORIES.find((c) => c.slug === slug || c.id === slug);
    return found || null;
  },
};
