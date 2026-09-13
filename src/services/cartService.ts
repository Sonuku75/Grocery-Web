import { apiClient, isMockMode } from "@/lib/api";
import { Cart, CartItem, Product, ProductVariant, CartVariantSummary, Coupon } from "@/types";
import { MOCK_COUPONS } from "@/lib/mockData";

const STORAGE_KEY = "cartify_cart";

function calculateCartTotals(items: CartItem[], appliedCoupon?: Coupon | null): Cart {
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce((sum, item) => {
    const unitPrice = item.unitPrice ?? item.variant?.price ?? item.product.price;
    return sum + unitPrice * item.quantity;
  }, 0);

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

  // Free delivery threshold: ₹500 (or $35)
  const deliveryFee = subtotal === 0 || subtotal >= 500 ? 0 : 40;
  const taxableAmount = Math.max(0, subtotal - discount);
  const tax = taxableAmount > 0 ? Number((taxableAmount * 0.05).toFixed(2)) : 0;
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

function normalizeServerCart(raw: any, existingCoupon?: Coupon | null): Cart {
  if (!raw) return calculateCartTotals([], existingCoupon);

  const items: CartItem[] = (raw.items || []).map((rawItem: any) => {
    const prod = rawItem.product || {};
    const vari = rawItem.variant || {};
    const unitPrice = Number(rawItem.unitPrice ?? rawItem.unit_price ?? vari.price ?? prod.price ?? 0);
    const lineTotal = Number(rawItem.lineTotal ?? rawItem.line_total ?? unitPrice * (rawItem.quantity || 1));

    return {
      id: rawItem.id,
      cartId: rawItem.cartId || rawItem.cart_id,
      productId: rawItem.productId || rawItem.product_id || prod.id,
      variantId: rawItem.variantId || rawItem.variant_id || vari.id,
      quantity: rawItem.quantity || 1,
      unitPrice,
      lineTotal,
      product: {
        id: prod.id,
        name: prod.title || prod.name || "Grocery Item",
        title: prod.title || prod.name || "Grocery Item",
        slug: prod.slug || "",
        brand: prod.brand || "Cartify",
        price: unitPrice,
        unit: vari.unit || prod.unit || "1 pc",
        imageUrl: prod.thumbnailUrl || prod.thumbnail_url || prod.imageUrl || prod.image_url,
        images: prod.imageUrl ? [prod.imageUrl] : [],
        isActive: prod.isActive ?? prod.is_active ?? true,
      } as any,
      variant: {
        id: vari.id,
        productId: vari.productId || vari.product_id,
        sku: vari.sku,
        name: vari.name,
        unit: vari.unit,
        price: unitPrice,
        mrp: vari.mrp ? Number(vari.mrp) : null,
        stockQuantity: vari.stockQuantity ?? vari.stock_quantity ?? 99,
        isActive: vari.isActive ?? vari.is_active ?? true,
      },
      createdAt: rawItem.createdAt || rawItem.created_at,
      updatedAt: rawItem.updatedAt || rawItem.updated_at,
    };
  });

  const itemCount = Number(raw.itemCount ?? raw.item_count ?? items.reduce((s, i) => s + i.quantity, 0));
  const subtotal = Number(raw.subtotal ?? 0);
  const discount = Number(raw.discount ?? 0);
  const deliveryFee = Number(raw.deliveryFee ?? raw.delivery_fee ?? 0);
  const tax = Number(raw.tax ?? 0);
  const total = Number(raw.total ?? (subtotal - discount + deliveryFee + tax));

  const rawCoupon = raw.appliedCoupon || raw.applied_coupon;
  let normalizedCoupon: Coupon | null = existingCoupon || null;
  if (rawCoupon) {
    normalizedCoupon = {
      id: rawCoupon.id,
      code: rawCoupon.code,
      name: rawCoupon.name || rawCoupon.code,
      description: rawCoupon.description || "",
      discountType:
        (rawCoupon.discountType || rawCoupon.discount_type || "percent").toString().toLowerCase() === "percentage"
          ? "percent"
          : (rawCoupon.discountType || rawCoupon.discount_type || "fixed").toString().toLowerCase() === "fixed_amount"
          ? "fixed"
          : (rawCoupon.discountType || rawCoupon.discount_type || "percent"),
      discountValue: Number(rawCoupon.discountValue ?? rawCoupon.discount_value ?? 0),
      minOrderAmount: Number(rawCoupon.minimumOrderValue ?? rawCoupon.minimum_order_value ?? rawCoupon.minOrderAmount ?? 0),
      minimumOrderValue: Number(rawCoupon.minimumOrderValue ?? rawCoupon.minimum_order_value ?? rawCoupon.minOrderAmount ?? 0),
      maxDiscount: rawCoupon.maximumDiscount != null ? Number(rawCoupon.maximumDiscount) : rawCoupon.maximum_discount != null ? Number(rawCoupon.maximum_discount) : undefined,
      maximumDiscount: rawCoupon.maximumDiscount != null ? Number(rawCoupon.maximumDiscount) : rawCoupon.maximum_discount != null ? Number(rawCoupon.maximum_discount) : undefined,
      validUntil: rawCoupon.expiresAt || rawCoupon.expires_at || rawCoupon.validUntil || "",
      expiresAt: rawCoupon.expiresAt || rawCoupon.expires_at || rawCoupon.validUntil || "",
      isActive: rawCoupon.isActive ?? rawCoupon.is_active ?? true,
    };
  } else if (raw.couponId === null || raw.coupon_id === null || discount === 0) {
    if (!existingCoupon || discount === 0) {
      normalizedCoupon = null;
    }
  }

  return {
    id: raw.id,
    userId: raw.userId || raw.user_id,
    items,
    itemCount,
    subtotal,
    discount,
    deliveryFee,
    tax,
    total,
    appliedCoupon: normalizedCoupon,
    createdAt: raw.createdAt || raw.created_at,
    updatedAt: raw.updatedAt || raw.updated_at,
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
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.get<any>("/cart");
        if (res.success && res.data) {
          const prev = this.getStoredCart();
          const normalized = normalizeServerCart(res.data, prev.appliedCoupon);
          this.saveStoredCart(normalized);
          return normalized;
        }
      } catch (err) {
        console.warn("Failed to fetch live cart from server, using local fallback", err);
      }
    }
    return this.getStoredCart();
  },

  async addToCart(
    product: Product,
    quantity: number = 1,
    variant?: ProductVariant | CartVariantSummary
  ): Promise<Cart> {
    const boundedQty = Math.max(1, Math.min(quantity, 99));
    const resolvedVariant = variant || product.primaryVariant || (product.variants && product.variants.length > 0 ? product.variants[0] : undefined);
    const variantId = resolvedVariant?.id || product.id;

    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.post<any>("/cart/items", {
          variantId,
          productId: product.id,
          quantity: boundedQty,
        });
        if (res.success && res.data) {
          const prev = this.getStoredCart();
          const normalized = normalizeServerCart(res.data, prev.appliedCoupon);
          this.saveStoredCart(normalized);
          return normalized;
        }
      } catch (err) {
        console.warn("Live add to cart failed, using local storage", err);
      }
    }

    // Local state fallback
    const current = this.getStoredCart();
    const existingIndex = current.items.findIndex(
      (item) => item.variantId === variantId || item.productId === product.id
    );

    let updatedItems: CartItem[];
    if (existingIndex > -1) {
      updatedItems = [...current.items];
      const newQty = Math.min(99, updatedItems[existingIndex].quantity + boundedQty);
      updatedItems[existingIndex] = {
        ...updatedItems[existingIndex],
        quantity: newQty,
      };
    } else {
      const unitPrice = resolvedVariant ? resolvedVariant.price : product.price;
      const newItem: CartItem = {
        id: "ci-" + Date.now(),
        productId: product.id,
        variantId,
        product,
        variant: resolvedVariant as any,
        quantity: boundedQty,
        unitPrice,
        lineTotal: unitPrice * boundedQty,
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
    const boundedQty = Math.max(1, Math.min(quantity, 99));

    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.patch<any>(`/cart/items/${itemId}`, {
          quantity: boundedQty,
        });
        if (res.success && res.data) {
          const prev = this.getStoredCart();
          const normalized = normalizeServerCart(res.data, prev.appliedCoupon);
          this.saveStoredCart(normalized);
          return normalized;
        }
      } catch (err) {
        console.warn("Live update quantity failed, falling back to local update", err);
      }
    }

    const current = this.getStoredCart();
    const updatedItems = current.items.map((item) =>
      item.id === itemId || item.productId === itemId || item.variantId === itemId
        ? { ...item, quantity: boundedQty }
        : item
    );

    const updatedCart = calculateCartTotals(updatedItems, current.appliedCoupon);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },

  async removeFromCart(itemId: string): Promise<Cart> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.delete<any>(`/cart/items/${itemId}`);
        if (res.success && res.data) {
          const prev = this.getStoredCart();
          const normalized = normalizeServerCart(res.data, prev.appliedCoupon);
          this.saveStoredCart(normalized);
          return normalized;
        }
      } catch (err) {
        console.warn("Live remove item failed, falling back to local remove", err);
      }
    }

    const current = this.getStoredCart();
    const updatedItems = current.items.filter(
      (item) => item.id !== itemId && item.productId !== itemId && item.variantId !== itemId
    );
    const updatedCart = calculateCartTotals(updatedItems, current.appliedCoupon);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },

  async clearCart(): Promise<Cart> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        await apiClient.delete("/cart");
      } catch (err) {
        console.warn("Live clear cart failed, clearing locally", err);
      }
    }
    const emptyCart = calculateCartTotals([]);
    this.saveStoredCart(emptyCart);
    return emptyCart;
  },

  async applyCoupon(code: string): Promise<{ cart: Cart; message: string; success: boolean }> {
    const current = this.getStoredCart();
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();

    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.post<any>("/cart/coupon", { code });
        if (res.data) {
          const normalized = normalizeServerCart(res.data);
          this.saveStoredCart(normalized);
          return {
            cart: normalized,
            message: res.message || `Coupon ${code.toUpperCase()} applied successfully!`,
            success: true,
          };
        }
      } catch (err: any) {
        const errMsg = err?.message || err?.error?.message || "Failed to apply coupon.";
        return { cart: current, message: errMsg, success: false };
      }
    }

    // Local fallback for unauthenticated / mock mode
    const coupon = MOCK_COUPONS.find((c) => c.code.toUpperCase() === code.trim().toUpperCase());
    if (!coupon) {
      return { cart: current, message: "Invalid coupon code. Try SAVE20 or FLAT150.", success: false };
    }

    if (current.subtotal < coupon.minOrderAmount) {
      return {
        cart: current,
        message: `Order subtotal must be at least ₹${coupon.minOrderAmount} to use this coupon.`,
        success: false,
      };
    }

    const updatedCart = calculateCartTotals(current.items, coupon);
    this.saveStoredCart(updatedCart);
    return { cart: updatedCart, message: `Coupon ${coupon.code} applied successfully!`, success: true };
  },

  async removeCoupon(): Promise<Cart> {
    const current = this.getStoredCart();
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();

    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.delete<any>("/cart/coupon");
        if (res.data) {
          const normalized = normalizeServerCart(res.data);
          this.saveStoredCart(normalized);
          return normalized;
        }
      } catch (err) {
        console.warn("Live remove coupon failed, falling back to local", err);
      }
    }

    const updatedCart = calculateCartTotals(current.items, null);
    this.saveStoredCart(updatedCart);
    return updatedCart;
  },
};
