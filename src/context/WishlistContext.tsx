"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { Product } from "@/types";
import { wishlistService } from "@/services/wishlistService";
import { useToast } from "@/context/ToastContext";

interface WishlistContextType {
  wishlistIds: string[];
  wishlistProducts: Product[];
  loading: boolean;
  isInWishlist: (productId: string) => boolean;
  toggleWishlist: (product: Product) => Promise<void>;
  removeFromWishlist: (productId: string) => Promise<void>;
}

const WishlistContext = createContext<WishlistContextType | undefined>(undefined);

export function WishlistProvider({ children }: { children: ReactNode }) {
  const [wishlistIds, setWishlistIds] = useState<string[]>(() => wishlistService.getStoredWishlist());
  const [wishlistProducts, setWishlistProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { showToast } = useToast();

  const loadWishlist = useCallback(async () => {
    setLoading(true);
    try {
      const items = await wishlistService.getWishlist();
      setWishlistProducts(items);
      setWishlistIds(items.map((i) => i.id));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWishlist();
  }, [loadWishlist]);

  const isInWishlist = useCallback(
    (productId: string) => {
      return wishlistIds.includes(productId);
    },
    [wishlistIds]
  );

  const toggleWishlist = useCallback(
    async (product: Product) => {
      const isCurrently = wishlistIds.includes(product.id);
      const res = await wishlistService.toggleWishlist(product.id);
      setWishlistIds(res.ids);
      if (res.isInWishlist) {
        setWishlistProducts((prev) => [...prev, product]);
        showToast(`Added ${product.name} to Wishlist`, "success");
      } else {
        setWishlistProducts((prev) => prev.filter((p) => p.id !== product.id));
        showToast(`Removed from Wishlist`, "info");
      }
    },
    [wishlistIds, showToast]
  );

  const removeFromWishlist = useCallback(
    async (productId: string) => {
      const ids = await wishlistService.removeFromWishlist(productId);
      setWishlistIds(ids);
      setWishlistProducts((prev) => prev.filter((p) => p.id !== productId));
      showToast("Removed from Wishlist", "info");
    },
    [showToast]
  );

  return (
    <WishlistContext.Provider
      value={{
        wishlistIds,
        wishlistProducts,
        loading,
        isInWishlist,
        toggleWishlist,
        removeFromWishlist,
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
