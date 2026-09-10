"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { Cart, CartItem, Product } from "@/types";
import { cartService } from "@/services/cartService";
import { useToast } from "@/context/ToastContext";

interface CartContextType {
  cart: Cart;
  loading: boolean;
  isCartDrawerOpen: boolean;
  setIsCartDrawerOpen: (open: boolean) => void;
  addToCart: (product: Product, quantity?: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  applyCoupon: (code: string) => Promise<{ success: boolean; message: string }>;
  removeCoupon: () => Promise<void>;
  getItemQuantity: (productId: string) => number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart>(() => cartService.getStoredCart());
  const [loading, setLoading] = useState<boolean>(false);
  const [isCartDrawerOpen, setIsCartDrawerOpen] = useState<boolean>(false);
  const { showToast } = useToast();

  useEffect(() => {
    async function loadCart() {
      try {
        const loaded = await cartService.getCart();
        setCart(loaded);
      } catch (err) {
        console.error("Failed to load cart", err);
      }
    }
    loadCart();
  }, []);

  const addToCart = useCallback(
    async (product: Product, quantity: number = 1) => {
      try {
        const updated = await cartService.addToCart(product, quantity);
        setCart(updated);
        showToast(`Added ${product.name} to cart!`, "success");
      } catch (err) {
        showToast("Failed to add to cart", "error");
      }
    },
    [showToast]
  );

  const updateQuantity = useCallback(
    async (itemId: string, quantity: number) => {
      try {
        const updated = await cartService.updateQuantity(itemId, quantity);
        setCart(updated);
      } catch (err) {
        showToast("Failed to update item quantity", "error");
      }
    },
    [showToast]
  );

  const removeFromCart = useCallback(
    async (itemId: string) => {
      try {
        const updated = await cartService.removeFromCart(itemId);
        setCart(updated);
        showToast("Item removed from cart", "info");
      } catch (err) {
        showToast("Failed to remove item", "error");
      }
    },
    [showToast]
  );

  const clearCart = useCallback(async () => {
    try {
      const updated = await cartService.clearCart();
      setCart(updated);
    } catch (err) {
      console.error(err);
    }
  }, []);

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
    (productId: string) => {
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
