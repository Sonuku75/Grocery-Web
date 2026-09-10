import { apiClient } from "@/lib/api";
import { Cart, CartItem, Product, Coupon } from "@/types";
import { MOCK_COUPONS } from "@/lib/mockData";

const STORAGE_KEY = "cartify_cart";

function calculateCartTotals(items: CartItem[], appliedCoupon?: Coupon | null): Cart {
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

  let discount = 0;
  if (appliedCoupon && subtotal >= appliedCoupon.minOrderAmount) {
    if (appliedCoupon.discountType === "percent") {
      const calcDiscount = (subtotal * appliedCoupon.discountValue) / 100;
      discount = appliedCoupon.maxDiscount
        ? Math.min(calcDiscount, appliedCoupon.maxDiscount)
        : calcDiscount;
    } else {
      discount = appliedCoupon.discountValue;
    }
  }

  // Free delivery threshold: $35
  const deliveryFee = subtotal === 0 || subtotal >= 35 ? 0 : 3.99;
  const taxableAmount = Math.max(0, subtotal - discount);
  const tax = taxableAmount > 0 ? Number((taxableAmount * 0.07).toFixed(2)) : 0; // 7% standard tax
  const total = Number((taxableAmount + deliveryFee + tax).toFixed(2));

  return {
    items,
    itemCount,
    subtotal: Number(subtotal.toFixed(2)),
    discount: Number(discount.toFixed(2)),
    deliveryFee: Number(deliveryFee.toFixed(2)),
    tax,
    total,
    appliedCoupon: appliedCoupon || null,
  };
}

export const cartService = {
  getStoredCart(): Cart {
    if (typeof window === "undefined") {
      return calculateCartTotals([]);
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return calculateCartTotals([]);
    try {
      const parsed = JSON.parse(stored);
      return calculateCartTotals(parsed.items || [], parsed.appliedCoupon);
    } catch {
      return calculateCartTotals([]);
    }
  },

  saveStoredCart(cart: Cart) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
  },

  async getCart(): Promise<Cart> {
    const res = await apiClient.get<Cart>("/cart");
    if (res.success && res.data) {
      this.saveStoredCart(res.data);
      return res.data;
    }
    return this.getStoredCart();
  },

  async addToCart(product: Product, quantity: number = 1): Promise<Cart> {
    const res = await apiClient.post<Cart>("/cart/items", {
      productId: product.id,
      quantity,
    });
    if (res.success && res.data) {
      this.saveStoredCart(res.data);
      return res.data;
    }

    // Local fallback
    const current = this.getStoredCart();
    const existingIndex = current.items.findIndex((item) => item.productId === product.id);

    let updatedItems: CartItem[];
    if (existingIndex > -1) {
      updatedItems = [...current.items];
      updatedItems[existingIndex] = {
        ...updatedItems[existingIndex],
        quantity: updatedItems[existingIndex].quantity + quantity,
      };
    } else {
      const newItem: CartItem = {
        id: "ci-" + Date.now(),
        productId: product.id,
        product,
        quantity,
      };
      updatedItems = [...current.items, newItem];
    }

    const updatedCart = calculateCartTotals(updatedItems, current.appliedCoupon);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },

  async updateQuantity(itemId: string, quantity: number): Promise<Cart> {
    if (quantity <= 0) {
      return this.removeFromCart(itemId);
    }

    const res = await apiClient.put<Cart>(`/cart/items/${itemId}`, { quantity });
    if (res.success && res.data) {
      this.saveStoredCart(res.data);
      return res.data;
    }

    const current = this.getStoredCart();
    const updatedItems = current.items.map((item) =>
      item.id === itemId || item.productId === itemId ? { ...item, quantity } : item
    );

    const updatedCart = calculateCartTotals(updatedItems, current.appliedCoupon);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },

  async removeFromCart(itemId: string): Promise<Cart> {
    const res = await apiClient.delete<Cart>(`/cart/items/${itemId}`);
    if (res.success && res.data) {
      this.saveStoredCart(res.data);
      return res.data;
    }

    const current = this.getStoredCart();
    const updatedItems = current.items.filter(
      (item) => item.id !== itemId && item.productId !== itemId
    );
    const updatedCart = calculateCartTotals(updatedItems, current.appliedCoupon);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },

  async clearCart(): Promise<Cart> {
    await apiClient.delete("/cart");
    const emptyCart = calculateCartTotals([]);
    this.saveStoredCart(emptyCart);
    return emptyCart;
  },

  async applyCoupon(code: string): Promise<{ cart: Cart; message: string; success: boolean }> {
    const res = await apiClient.post<{ cart: Cart; message: string }>("/coupons/validate", { code });
    if (res.success && res.data) {
      this.saveStoredCart(res.data.cart);
      return { cart: res.data.cart, message: res.data.message, success: true };
    }

    const current = this.getStoredCart();
    const coupon = MOCK_COUPONS.find((c) => c.code.toUpperCase() === code.trim().toUpperCase());

    if (!coupon) {
      return { cart: current, message: "Invalid coupon code. Try CARTIFY50 or FRESH20.", success: false };
    }

    if (current.subtotal < coupon.minOrderAmount) {
      return {
        cart: current,
        message: `Order subtotal must be at least $${coupon.minOrderAmount} to use this coupon.`,
        success: false,
      };
    }

    const updatedCart = calculateCartTotals(current.items, coupon);
    this.saveStoredCart(updatedCart);
    return { cart: updatedCart, message: `Coupon ${coupon.code} applied successfully!`, success: true };
  },

  async removeCoupon(): Promise<Cart> {
    const current = this.getStoredCart();
    const updatedCart = calculateCartTotals(current.items, null);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },
};
