"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import { Product } from "@/types";
import { wishlistService } from "@/services/wishlistService";
import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";

interface WishlistContextType {
  wishlistIds: string[];
  wishlistProducts: Product[];
  count: number;
  loading: boolean;
  isInWishlist: (productId: string) => boolean;
  toggleWishlist: (product: Product) => Promise<void>;
  removeFromWishlist: (productId: string) => Promise<void>;
  refreshWishlist: () => Promise<void>;
}

const WishlistContext = createContext<WishlistContextType | undefined>(undefined);

export function WishlistProvider({ children }: { children: ReactNode }) {
  const [wishlistIds, setWishlistIds] = useState<string[]>(() => wishlistService.getStoredWishlist());
  const [wishlistProducts, setWishlistProducts] = useState<Product[]>([]);
  const [count, setCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const { showToast } = useToast();
  const { isAuthenticated, loading: authLoading } = useAuth();
  
  // Guard against rapid double-clicks on the same product
  const inflightOperations = useRef<Set<string>>(new Set());

  const loadWishlist = useCallback(async () => {
    setLoading(true);
    try {
      const res = await wishlistService.getWishlist();
      setWishlistProducts(res.products);
      const ids = res.products.map((p) => p.id);
      setWishlistIds(ids);
      setCount(res.count);
    } catch (err) {
      console.warn("Error loading wishlist:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) {
      loadWishlist();
    }
  }, [isAuthenticated, authLoading, loadWishlist]);

  const isInWishlist = useCallback(
    (productId: string) => {
      return wishlistIds.includes(productId);
    },
    [wishlistIds]
  );

  const toggleWishlist = useCallback(
    async (product: Product) => {
      if (!product || !product.id) return;

      if (!isAuthenticated) {
        showToast("Please sign in to add items to your wishlist.", "warning");
        return;
      }

      if (inflightOperations.current.has(product.id)) {
        return; // debounce / avoid double click
      }
      inflightOperations.current.add(product.id);

      const isCurrently = wishlistIds.includes(product.id);

      // Snapshot for potential rollback
      const prevIds = [...wishlistIds];
      const prevProducts = [...wishlistProducts];
      const prevCount = count;

      // 1. Optimistic Update
      if (isCurrently) {
        setWishlistIds((prev) => prev.filter((id) => id !== product.id));
        setWishlistProducts((prev) => prev.filter((p) => p.id !== product.id));
        setCount((prev) => Math.max(0, prev - 1));
        showToast(`Removed from Wishlist`, "info");
      } else {
        setWishlistIds((prev) => [...prev, product.id]);
        setWishlistProducts((prev) => [product, ...prev]);
        setCount((prev) => prev + 1);
        showToast(`Added ${product.name} to Wishlist`, "success");
      }

      // 2. Background API dispatch with Rollback Safety
      try {
        if (isCurrently) {
          await wishlistService.removeFromWishlist(product.id);
        } else {
          await wishlistService.addToWishlist(product.id);
        }
      } catch (err) {
        console.error("Wishlist operation failed, rolling back UI:", err);
        // Rollback to prior snapshot
        setWishlistIds(prevIds);
        setWishlistProducts(prevProducts);
        setCount(prevCount);
        showToast("Failed to update wishlist. Please try again.", "error");
      } finally {
        inflightOperations.current.delete(product.id);
      }
    },
    [isAuthenticated, wishlistIds, wishlistProducts, count, showToast]
  );

  const removeFromWishlist = useCallback(
    async (productId: string) => {
      if (!productId) return;

      if (inflightOperations.current.has(productId)) {
        return;
      }
      inflightOperations.current.add(productId);

      const prevIds = [...wishlistIds];
      const prevProducts = [...wishlistProducts];
      const prevCount = count;

      // Optimistic removal
      setWishlistIds((prev) => prev.filter((id) => id !== productId));
      setWishlistProducts((prev) => prev.filter((p) => p.id !== productId));
      setCount((prev) => Math.max(0, prev - 1));
      showToast("Removed from Wishlist", "info");

      try {
        await wishlistService.removeFromWishlist(productId);
      } catch (err) {
        console.error("Failed to remove item from wishlist, rolling back:", err);
        setWishlistIds(prevIds);
        setWishlistProducts(prevProducts);
        setCount(prevCount);
        showToast("Failed to remove item. Please try again.", "error");
      } finally {
        inflightOperations.current.delete(productId);
      }
    },
    [wishlistIds, wishlistProducts, count, showToast]
  );

  return (
    <WishlistContext.Provider
      value={{
        wishlistIds,
        wishlistProducts,
        count,
        loading,
        isInWishlist,
        toggleWishlist,
        removeFromWishlist,
        refreshWishlist: loadWishlist,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error("useWishlist must be used within a WishlistProvider");
  }
  return context;
}
