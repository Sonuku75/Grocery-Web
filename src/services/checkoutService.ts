/**
 * Cartify Checkout Service (Module 9)
 *
 * Frontend service for managing customer checkout previews, sessions, and confirmation:
 * - Direct REST integration with FastAPI /api/v1/checkout endpoints
 * - Authoritative server-side price, delivery fee, and discount synchronization
 * - Double-click idempotency protection with UUID-based Idempotency-Key
 * - Dual camelCase / snake_case response normalization
 * - Graceful mock/offline fallback
 */

import { apiClient, isMockMode } from "@/lib/api";
import {
  CheckoutConfirmRequest,
  CheckoutConfirmResponse,
  CheckoutPreviewRequest,
  CheckoutSummary,
  CheckoutItemSnapshot,
  CheckoutAddressSnapshot,
} from "@/types";

function normalizeCheckoutSummary(raw: any): CheckoutSummary {
  const rawItems = raw.items || [];
  const items: CheckoutItemSnapshot[] = rawItems.map((item: any) => ({
    variantId: item.variantId || item.variant_id || "",
    productId: item.productId || item.product_id || "",
    sku: item.sku || undefined,
    productTitle: item.productTitle || item.product_title || item.title || item.name || "Item",
    variantName: item.variantName || item.variant_name || undefined,
    unit: item.unit || undefined,
    quantity: Number(item.quantity ?? 1),
    unitPrice: Number(item.unitPrice ?? item.unit_price ?? 0),
    lineTotal: Number(item.lineTotal ?? item.line_total ?? 0),
    thumbnailUrl: item.thumbnailUrl || item.thumbnail_url || item.imageUrl || item.image_url || undefined,
  }));

  let address: CheckoutAddressSnapshot | null = null;
  if (raw.address) {
    const a = raw.address;
    address = {
      id: a.id,
      recipientName: a.recipientName || a.recipient_name || a.fullName || a.full_name || "Customer",
      phone: a.phone || a.mobile || "",
      addressLine1: a.addressLine1 || a.address_line_1 || a.houseFlat || a.house_flat || "",
      addressLine2: a.addressLine2 || a.address_line_2 || a.street || a.area || "",
      landmark: a.landmark || "",
      city: a.city || "",
      state: a.state || "",
      country: a.country || "India",
      postalCode: a.postalCode || a.postal_code || a.pincode || "",
      label: a.label || a.addressType || "Home",
      latitude: a.latitude != null ? Number(a.latitude) : undefined,
      longitude: a.longitude != null ? Number(a.longitude) : undefined,
    };
  }

  return {
    id: raw.id,
    userId: raw.userId || raw.user_id || "",
    cartId: raw.cartId || raw.cart_id || "",
    status: raw.status || "ACTIVE",
    items,
    address,
    subtotal: Number(raw.subtotal ?? 0),
    discount: Number(raw.discount ?? raw.discountAmount ?? raw.discount_amount ?? 0),
    deliveryFee: Number(raw.deliveryFee ?? raw.delivery_fee ?? 0),
    tax: Number(raw.tax ?? raw.taxAmount ?? raw.tax_amount ?? 0),
    total: Number(raw.total ?? raw.totalAmount ?? raw.total_amount ?? 0),
    currency: raw.currency || "INR",
    coupon: raw.coupon || null,
    deliveryMethod: raw.deliveryMethod || raw.delivery_method || "STANDARD",
    deliverySlot: raw.deliverySlot || raw.delivery_slot || "Today • Express 15-Minute Delivery",
    expiresAt: raw.expiresAt || raw.expires_at || "",
    priceChanged: Boolean(raw.priceChanged || raw.price_changed),
    warningMessage: raw.warningMessage || raw.warning_message || null,
    createdAt: raw.createdAt || raw.created_at,
    updatedAt: raw.updatedAt || raw.updated_at,
  };
}

export const checkoutService = {
  /**
   * Generates or updates an authoritative checkout preview.
   */
  async previewCheckout(payload?: CheckoutPreviewRequest): Promise<CheckoutSummary> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();

    if (!isMockMode() && hasToken) {
      try {
        const body: Record<string, any> = {};
        if (payload?.addressId || payload?.address_id) {
          body.addressId = payload.addressId || payload.address_id;
        }
        if (payload?.deliveryMethod || payload?.delivery_method) {
          body.deliveryMethod = payload.deliveryMethod || payload.delivery_method;
        }
        if (payload?.deliverySlot || payload?.delivery_slot) {
          body.deliverySlot = payload.deliverySlot || payload.delivery_slot;
        }

        const res = await apiClient.post<any>("/checkout/preview", body);
        const data = res.data?.data || res.data;
        if (data && data.id) {
          return normalizeCheckoutSummary(data);
        }
      } catch (err) {
        console.warn("API preview checkout failed, evaluating fallback", err);
        throw err;
      }
    }

    // Mock fallback when offline or in mock mode
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 30 * 60 * 1000).toISOString();
    return {
      id: "mock-sess-" + Math.random().toString(36).substring(2, 9),
      userId: "usr-guest",
      cartId: "cart-guest",
      status: "ACTIVE",
      items: [],
      address: null,
      subtotal: 0,
      discount: 0,
      deliveryFee: 40,
      tax: 0,
      total: 40,
      currency: "INR",
      deliveryMethod: payload?.deliveryMethod || "STANDARD",
      deliverySlot: payload?.deliverySlot || "Today • Express 15-Minute Delivery",
      expiresAt,
      priceChanged: false,
    };
  },

  /**
   * Retrieves the currently active checkout session if any.
   */
  async getActiveCheckout(): Promise<CheckoutSummary | null> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.get<any>("/checkout");
        const data = res.data?.data || res.data;
        if (data && data.id) {
          return normalizeCheckoutSummary(data);
        }
      } catch (err: any) {
        if (err?.status === 404 || err?.statusCode === 404) {
          return null;
        }
        console.warn("Error fetching active checkout", err);
        return null;
      }
    }
    return null;
  },

  /**
   * Confirms checkout session with Idempotency-Key support.
   */
  async confirmCheckout(
    payload: CheckoutConfirmRequest,
    idempotencyKey?: string
  ): Promise<CheckoutConfirmResponse> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();

    const headers: Record<string, string> = {};
    const key = idempotencyKey || (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : "idem-" + Date.now());
    headers["Idempotency-Key"] = key;

    if (!isMockMode() && hasToken) {
      const body = {
        checkoutSessionId: payload.checkoutSessionId || payload.checkout_session_id,
        deliverySlot: payload.deliverySlot || payload.delivery_slot,
        notes: payload.notes,
      };

      const res = await apiClient.post<any>("/checkout/confirm", body, { headers });
      const data = res.data?.data || res.data;
      return {
        checkoutStatus: data.checkoutStatus || data.checkout_status || "READY_FOR_ORDER",
        checkoutSessionId: data.checkoutSessionId || data.checkout_session_id || payload.checkoutSessionId,
        summary: normalizeCheckoutSummary(data.summary || {}),
        message: data.message || "Checkout confirmed and ready for order placement.",
      };
    }

    // Mock fallback
    return {
      checkoutStatus: "READY_FOR_ORDER",
      checkoutSessionId: payload.checkoutSessionId,
      summary: {
        id: payload.checkoutSessionId,
        userId: "usr-guest",
        cartId: "cart-guest",
        status: "COMPLETED",
        items: [],
        address: null,
        subtotal: 0,
        discount: 0,
        deliveryFee: 40,
        tax: 0,
        total: 40,
        currency: "INR",
        deliveryMethod: "STANDARD",
        expiresAt: new Date().toISOString(),
      },
      message: "Checkout confirmed and ready for order placement.",
    };
  },

  /**
   * Cancels an active checkout session.
   */
  async cancelCheckout(sessionId: string): Promise<boolean> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        await apiClient.delete(`/checkout/${sessionId}`);
        return true;
      } catch (err) {
        console.warn("Error cancelling checkout session", err);
        return false;
      }
    }
    return true;
  },
};
