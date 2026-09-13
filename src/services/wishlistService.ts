import { apiClient, isMockMode } from "@/lib/api";
import { Product, WishlistResponse, WishlistCheckResponse, WishlistItem } from "@/types";
import { MOCK_PRODUCTS } from "@/lib/mockData";
import { normalizeProduct } from "@/services/productService";

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

  async getWishlist(cursor?: string, limit: number = 50): Promise<{ products: Product[]; count: number; nextCursor?: string; hasMore: boolean }> {
    if (!isMockMode()) {
      try {
        const queryParams: Record<string, any> = { limit };
        if (cursor) queryParams.cursor = cursor;

        const res = await apiClient.get<WishlistResponse>("/wishlist", queryParams);
        if (res.success && res.data) {
          const products = (res.data.items || []).map((item: WishlistItem) =>
            normalizeProduct(item.product)
          );
          return {
            products,
            count: res.data.count,
            nextCursor: res.data.nextCursor || res.data.next_cursor,
            hasMore: res.data.hasMore ?? res.data.has_more ?? false,
          };
        }
      } catch (err) {
        console.warn("Failed to fetch live wishlist, falling back to local storage:", err);
      }
    }

    const ids = this.getStoredWishlist();
    const products = MOCK_PRODUCTS.filter((p) => ids.includes(p.id));
    return {
      products,
      count: products.length,
      hasMore: false,
    };
  },

  async addToWishlist(productId: string): Promise<boolean> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.post("/wishlist/items", { productId });
        if (res.success) {
          const current = this.getStoredWishlist();
          if (!current.includes(productId)) {
            this.saveStoredWishlist([...current, productId]);
          }
          return true;
        }
      } catch (err) {
        console.warn("Failed to add to live wishlist:", err);
        throw err;
      }
    }

    const current = this.getStoredWishlist();
    if (!current.includes(productId)) {
      this.saveStoredWishlist([...current, productId]);
    }
    return true;
  },

  async removeFromWishlist(productId: string): Promise<boolean> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.delete(`/wishlist/items/${productId}`);
        if (res.success) {
          const current = this.getStoredWishlist();
          this.saveStoredWishlist(current.filter((id) => id !== productId));
          return true;
        }
      } catch (err) {
        console.warn("Failed to delete from live wishlist:", err);
        throw err;
      }
    }

    const current = this.getStoredWishlist();
    this.saveStoredWishlist(current.filter((id) => id !== productId));
    return true;
  },

  async checkWishlist(productId: string): Promise<boolean> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<WishlistCheckResponse>(`/wishlist/check/${productId}`);
        if (res.success && res.data) {
          return res.data.isWishlisted ?? res.data.is_wishlisted ?? false;
        }
      } catch {
        // Fallback to local
      }
    }
    return this.getStoredWishlist().includes(productId);
  },

  async toggleWishlist(productId: string): Promise<{ isInWishlist: boolean; ids: string[] }> {
    const current = this.getStoredWishlist();
    if (current.includes(productId)) {
      await this.removeFromWishlist(productId);
      const updated = current.filter((id) => id !== productId);
      return { isInWishlist: false, ids: updated };
    } else {
      await this.addToWishlist(productId);
      const updated = [...current, productId];
      return { isInWishlist: true, ids: updated };
    }
  },
};
