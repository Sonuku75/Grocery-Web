import { apiClient } from "@/lib/api";
import { Product } from "@/types";
import { MOCK_PRODUCTS } from "@/lib/mockData";

const STORAGE_KEY = "cartify_wishlist";

export const wishlistService = {
  getStoredWishlist(): string[] {
    if (typeof window === "undefined") return ["prod-1", "prod-6"];
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      const initial = ["prod-1", "prod-6"];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(initial));
      return initial;
    }
    try {
      return JSON.parse(stored) as string[];
    } catch {
      return [];
    }
  },

  saveStoredWishlist(ids: string[]) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  },

  async getWishlist(): Promise<Product[]> {
    const res = await apiClient.get<Product[]>("/wishlist");
    if (res.success && res.data) {
      return res.data;
    }

    const ids = this.getStoredWishlist();
    return MOCK_PRODUCTS.filter((p) => ids.includes(p.id));
  },

  async addToWishlist(productId: string): Promise<string[]> {
    await apiClient.post("/wishlist", { productId });
    const current = this.getStoredWishlist();
    if (!current.includes(productId)) {
      const updated = [...current, productId];
      this.saveStoredWishlist(updated);
      return updated;
    }
    return current;
  },

  async removeFromWishlist(productId: string): Promise<string[]> {
    await apiClient.delete(`/wishlist/${productId}`);
    const current = this.getStoredWishlist();
    const updated = current.filter((id) => id !== productId);
    this.saveStoredWishlist(updated);
    return updated;
  },

  async toggleWishlist(productId: string): Promise<{ isInWishlist: boolean; ids: string[] }> {
    const current = this.getStoredWishlist();
    if (current.includes(productId)) {
      const updated = await this.removeFromWishlist(productId);
      return { isInWishlist: false, ids: updated };
    } else {
      const updated = await this.addToWishlist(productId);
      return { isInWishlist: true, ids: updated };
    }
  },
};
