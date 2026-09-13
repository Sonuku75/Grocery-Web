"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from "react";
import { Cart, CartItem, Product, ProductVariant, CartVariantSummary } from "@/types";
import { cartService } from "@/services/cartService";
import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";

interface CartContextType {
  cart: Cart;
  loading: boolean;
  isCartDrawerOpen: boolean;
  setIsCartDrawerOpen: (open: boolean) => void;
  addToCart: (product: Product, quantity?: number, variant?: ProductVariant | CartVariantSummary) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  applyCoupon: (code: string) => Promise<{ success: boolean; message: string }>;
  removeCoupon: () => Promise<void>;
  getItemQuantity: (productId: string, variantId?: string) => number;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart>(() => cartService.getStoredCart());
  const [loading, setLoading] = useState<boolean>(false);
  const [isCartDrawerOpen, setIsCartDrawerOpen] = useState<boolean>(false);
  const { showToast } = useToast();
  const { user } = useAuth();
  const isUpdatingRef = useRef<boolean>(false);

  const refreshCart = useCallback(async () => {
    setLoading(true);
    try {
      const loaded = await cartService.getCart();
      setCart(loaded);
    } catch (err) {
      console.error("Failed to refresh cart", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Reload cart whenever authenticated user changes (login / logout)
  useEffect(() => {
    refreshCart();
  }, [user, refreshCart]);

  const addToCart = useCallback(
    async (
      product: Product,
      quantity: number = 1,
      variant?: ProductVariant | CartVariantSummary
    ) => {
      const previousCart = cart;
      const targetVariant = variant || product.primaryVariant || (product.variants && product.variants.length > 0 ? product.variants[0] : undefined);
      const variantTitle = targetVariant?.name || product.name;

      // Optimistic state calculation
      const variantId = targetVariant?.id || product.id;
      const existingIdx = previousCart.items.findIndex(
        (i) => i.variantId === variantId || i.productId === product.id
      );

      let optimisticItems: CartItem[];
      if (existingIdx > -1) {
        optimisticItems = [...previousCart.items];
        const newQty = Math.min(99, optimisticItems[existingIdx].quantity + quantity);
        optimisticItems[existingIdx] = {
          ...optimisticItems[existingIdx],
          quantity: newQty,
        };
      } else {
        const unitPrice = targetVariant ? targetVariant.price : product.price;
        const newItem: CartItem = {
          id: "temp-" + Date.now(),
          productId: product.id,
          variantId,
          product,
          variant: targetVariant as any,
          quantity,
          unitPrice,
          lineTotal: unitPrice * quantity,
        };
        optimisticItems = [...previousCart.items, newItem];
      }

      const optimisticCount = optimisticItems.reduce((s, i) => s + i.quantity, 0);
      const optimisticSubtotal = optimisticItems.reduce((s, i) => {
        const p = i.unitPrice ?? i.variant?.price ?? (i.product as any).price ?? 0;
        return s + p * i.quantity;
      }, 0);

      setCart({
        ...previousCart,
        items: optimisticItems,
        itemCount: optimisticCount,
        subtotal: Number(optimisticSubtotal.toFixed(2)),
        total: Number(optimisticSubtotal.toFixed(2)),
      });

      try {
        const updated = await cartService.addToCart(product, quantity, targetVariant);
        setCart(updated);
        showToast(`Added ${variantTitle} to cart!`, "success");
      } catch (err: any) {
        // Rollback
        setCart(previousCart);
        const msg = err?.message || "Failed to add to cart";
        showToast(msg, "error");
      }
    },
    [cart, showToast]
  );

  const updateQuantity = useCallback(
    async (itemId: string, quantity: number) => {
      if (isUpdatingRef.current) return;
      isUpdatingRef.current = true;
      const previousCart = cart;

      // Optimistic update
      let optimisticItems: CartItem[];
      if (quantity <= 0) {
        optimisticItems = previousCart.items.filter(
          (i) => i.id !== itemId && i.productId !== itemId && i.variantId !== itemId
        );
      } else {
        optimisticItems = previousCart.items.map((i) =>
          i.id === itemId || i.productId === itemId || i.variantId === itemId
            ? { ...i, quantity: Math.min(99, quantity) }
            : i
        );
      }

      const optimisticCount = optimisticItems.reduce((s, i) => s + i.quantity, 0);
      const optimisticSubtotal = optimisticItems.reduce((s, i) => {
        const p = i.unitPrice ?? i.variant?.price ?? (i.product as any).price ?? 0;
        return s + p * i.quantity;
      }, 0);

      setCart({
        ...previousCart,
        items: optimisticItems,
        itemCount: optimisticCount,
        subtotal: Number(optimisticSubtotal.toFixed(2)),
        total: Number(optimisticSubtotal.toFixed(2)),
      });

      try {
        const updated = await cartService.updateQuantity(itemId, quantity);
        setCart(updated);
      } catch (err: any) {
        setCart(previousCart);
        showToast(err?.message || "Failed to update item quantity", "error");
      } finally {
        isUpdatingRef.current = false;
      }
    },
    [cart, showToast]
  );

  const removeFromCart = useCallback(
    async (itemId: string) => {
      const previousCart = cart;
      const optimisticItems = previousCart.items.filter(
        (i) => i.id !== itemId && i.productId !== itemId && i.variantId !== itemId
      );
      const optimisticCount = optimisticItems.reduce((s, i) => s + i.quantity, 0);
      const optimisticSubtotal = optimisticItems.reduce((s, i) => {
        const p = i.unitPrice ?? i.variant?.price ?? (i.product as any).price ?? 0;
        return s + p * i.quantity;
      }, 0);

      setCart({
        ...previousCart,
        items: optimisticItems,
        itemCount: optimisticCount,
        subtotal: Number(optimisticSubtotal.toFixed(2)),
        total: Number(optimisticSubtotal.toFixed(2)),
      });

      try {
        const updated = await cartService.removeFromCart(itemId);
        setCart(updated);
        showToast("Item removed from cart", "info");
      } catch (err: any) {
        setCart(previousCart);
        showToast(err?.message || "Failed to remove item", "error");
      }
    },
    [cart, showToast]
  );

  const clearCart = useCallback(async () => {
    const previousCart = cart;
    setCart({
      ...previousCart,
      items: [],
      itemCount: 0,
      subtotal: 0,
      discount: 0,
      deliveryFee: 0,
      tax: 0,
      total: 0,
    });

    try {
      const updated = await cartService.clearCart();
      setCart(updated);
      showToast("Cart cleared", "info");
    } catch (err: any) {
      setCart(previousCart);
      showToast(err?.message || "Failed to clear cart", "error");
    }
  }, [cart, showToast]);

  const applyCoupon = useCallback(
    async (code: string) => {
      const res = await cartService.applyCoupon(code);
      setCart(res.cart);
      showToast(res.message, res.success ? "success" : "error");
      return { success: res.success, message: res.message };
    },
    [showToast]
  );

  const removeCoupon = useCallback(async () => {
    const updated = await cartService.removeCoupon();
    setCart(updated);
    showToast("Coupon removed", "info");
  }, [showToast]);

  const getItemQuantity = useCallback(
    (productId: string, variantId?: string) => {
      if (variantId) {
        const variantItem = cart.items.find((i) => i.variantId === variantId);
        if (variantItem) return variantItem.quantity;
      }
      const item = cart.items.find((i) => i.productId === productId || i.id === productId);
      return item ? item.quantity : 0;
    },
    [cart.items]
  );

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        isCartDrawerOpen,
        setIsCartDrawerOpen,
        addToCart,
        updateQuantity,
        removeFromCart,
        clearCart,
        applyCoupon,
        removeCoupon,
        getItemQuantity,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
