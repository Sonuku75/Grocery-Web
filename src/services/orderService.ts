import { apiClient } from "@/lib/api";
import {
  CreateOrderRequest,
  Order,
  OrderItem,
  OrderListResponse,
  OrderStatus,
  TrackingStep,
} from "@/types";
import { MOCK_ORDERS } from "@/lib/mockData";
import { generateOrderNumber } from "@/lib/utils";

const STORAGE_KEY = "cartify_orders";

/**
 * Normalizes backend OrderDetailResponse / OrderSummaryResponse
 * to ensure all UI convenience fields (total, subtotal, productImage, address) are populated.
 */
export function normalizeOrder(raw: any): Order {
  if (!raw) return raw;

  const total = Number(raw.totalAmount ?? raw.total ?? 0);
  const subtotal = Number(raw.subtotalAmount ?? raw.subtotal ?? 0);
  const discount = Number(raw.discountAmount ?? raw.discount ?? 0);
  const tax = Number(raw.taxAmount ?? raw.tax ?? 0);
  const deliveryFee = Number(raw.deliveryFee ?? 0);

  const items: OrderItem[] = (raw.items || []).map((it: any) => ({
    id: it.id || "",
    productId: it.productId || it.product_id || "",
    variantId: it.variantId || it.variant_id,
    productName: it.productName || it.product_name || "Item",
    variantName: it.variantName || it.variant_name,
    sku: it.sku,
    unitValue: it.unitValue || it.unit_value,
    unitType: it.unitType || it.unit_type,
    unit: it.unit || (it.variantName ? it.variantName : "1 unit"),
    unitPrice: Number(it.unitPrice ?? it.unit_price ?? 0),
    mrp: it.mrp ? Number(it.mrp) : undefined,
    quantity: Number(it.quantity ?? 1),
    lineTotal: Number(it.lineTotal ?? it.line_total ?? it.totalPrice ?? it.total_price ?? 0),
    totalPrice: Number(it.lineTotal ?? it.line_total ?? it.totalPrice ?? it.total_price ?? 0),
    thumbnailUrl: it.thumbnailUrl || it.thumbnail_url || it.productImage || it.product_image || "/images/placeholder.svg",
    productImage: it.thumbnailUrl || it.thumbnail_url || it.productImage || it.product_image || "/images/placeholder.svg",
  }));

  // Build legacy address object if only addressSnapshot is present
  const addressSnapshot = raw.addressSnapshot || raw.address_snapshot;
  const address = raw.address || (addressSnapshot ? {
    id: "snapshot-addr",
    label: addressSnapshot.addressType || "Home",
    recipientName: addressSnapshot.fullName,
    phone: addressSnapshot.phone,
    addressLine1: addressSnapshot.addressLine1,
    addressLine2: addressSnapshot.addressLine2,
    city: addressSnapshot.city,
    state: addressSnapshot.state,
    postalCode: addressSnapshot.postalCode,
    isDefault: false,
  } : undefined);

  // Derive tracking history from statusHistory or current status
  const trackingHistory: TrackingStep[] = raw.trackingHistory || buildTrackingStepsFromStatus(raw.status, raw.createdAt);

  return {
    id: raw.id,
    orderNumber: raw.orderNumber || raw.order_number || raw.id,
    userId: raw.userId || raw.user_id || "",
    status: raw.status,
    paymentStatus: raw.paymentStatus || raw.payment_status || "PENDING",
    fulfillmentStatus: raw.fulfillmentStatus || raw.fulfillment_status || "UNFULFILLED",
    subtotalAmount: subtotal,
    subtotal: subtotal,
    discountAmount: discount,
    discount: discount,
    deliveryFee: deliveryFee,
    taxAmount: tax,
    tax: tax,
    totalAmount: total,
    total: total,
    deliverySlot: raw.deliverySlot || raw.delivery_slot,
    couponCode: raw.couponCode || raw.coupon_code,
    notes: raw.notes,
    addressSnapshot: addressSnapshot,
    address: address,
    items: items,
    statusHistory: raw.statusHistory || raw.status_history || [],
    paymentMethod: raw.paymentMethod || "card",
    paymentTransactionId: raw.paymentTransactionId || raw.payment_transaction_id,
    trackingHistory: trackingHistory,
    checkoutSessionId: raw.checkoutSessionId || raw.checkout_session_id,
    createdAt: raw.createdAt || raw.created_at || new Date().toISOString(),
    updatedAt: raw.updatedAt || raw.updated_at,
  };
}

function buildTrackingStepsFromStatus(status: OrderStatus, createdAt: string): TrackingStep[] {
  const normalized = (status || "").toUpperCase();
  const isCancelled = normalized === "CANCELLED";

  return [
    {
      status: "PENDING",
      title: "Order Placed",
      description: "Order received by Cartify Hub",
      timestamp: createdAt,
      completed: true,
      current: normalized === "PENDING",
    },
    {
      status: "CONFIRMED",
      title: "Order Confirmed",
      description: "Inventory verified & reserved",
      timestamp: createdAt,
      completed: ["CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"].includes(normalized),
      current: normalized === "CONFIRMED",
    },
    {
      status: "PROCESSING",
      title: "Packing Order",
      description: "Carefully picking fresh groceries & sealing bags",
      timestamp: "",
      completed: ["PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"].includes(normalized),
      current: normalized === "PROCESSING",
    },
    {
      status: "SHIPPED",
      title: "Shipped & In Transit",
      description: "Dispatched from local micro-fulfillment center",
      timestamp: "",
      completed: ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"].includes(normalized),
      current: normalized === "SHIPPED",
    },
    {
      status: "OUT_FOR_DELIVERY",
      title: "Out for Delivery",
      description: "Assigned to Cartify electric delivery rider",
      timestamp: "",
      completed: ["OUT_FOR_DELIVERY", "DELIVERED"].includes(normalized),
      current: normalized === "OUT_FOR_DELIVERY",
    },
    {
      status: isCancelled ? "CANCELLED" : "DELIVERED",
      title: isCancelled ? "Order Cancelled" : "Delivered",
      description: isCancelled ? "Order was cancelled" : "Safe doorstep delivery with photo confirmation",
      timestamp: "",
      completed: ["DELIVERED", "CANCELLED"].includes(normalized),
      current: ["DELIVERED", "CANCELLED"].includes(normalized),
    },
  ];
}

export const orderService = {
  getStoredOrders(): Order[] {
    if (typeof window === "undefined") return MOCK_ORDERS.map(normalizeOrder);
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      const normalized = MOCK_ORDERS.map(normalizeOrder);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
      return normalized;
    }
    try {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed.map(normalizeOrder) : [];
    } catch {
      return MOCK_ORDERS.map(normalizeOrder);
    }
  },

  saveStoredOrders(orders: Order[]) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(orders));
  },

  /**
   * List customer's orders with pagination.
   */
  async getOrders(params?: { limit?: number; offset?: number }): Promise<Order[]> {
    const limit = params?.limit ?? 20;
    const offset = params?.offset ?? 0;
    try {
      const res = await apiClient.get<any>(`/orders?limit=${limit}&offset=${offset}`);
      if (res.success && res.data) {
        const rawItems = Array.isArray(res.data) ? res.data : (res.data.items || []);
        const normalized = rawItems.map(normalizeOrder);
        if (normalized.length > 0) {
          this.saveStoredOrders(normalized);
          return normalized;
        }
      }
    } catch (err) {
      console.warn("API getOrders failed, falling back to local storage", err);
    }
    return this.getStoredOrders();
  },

  /**
   * Retrieve single order details by internal UUID or public order number.
   */
  async getOrderById(id: string): Promise<Order | null> {
    try {
      const res = await apiClient.get<any>(`/orders/${id}`);
      if (res.success && res.data) {
        return normalizeOrder(res.data);
      }
    } catch (err) {
      console.warn(`API getOrderById(${id}) failed, checking local cache`, err);
    }

    const orders = this.getStoredOrders();
    const found = orders.find((o) => o.id === id || o.orderNumber === id);
    return found || null;
  },

  /**
   * Create an authoritative order from a completed checkout session.
   */
  async createOrder(
    data: CreateOrderRequest | { checkoutSessionId: string; notes?: string },
    idempotencyKey?: string
  ): Promise<Order> {
    try {
      const headers: Record<string, string> = {};
      if (idempotencyKey) {
        headers["Idempotency-Key"] = idempotencyKey;
      }
      const res = await apiClient.post<any>("/orders", data, { headers });
      if (res.success && res.data) {
        const normalized = normalizeOrder(res.data);
        const current = this.getStoredOrders();
        this.saveStoredOrders([normalized, ...current.filter((o) => o.id !== normalized.id)]);
        return normalized;
      }
    } catch (err) {
      console.warn("API createOrder failed, generating local fallback order", err);
    }

    // Local fallback for offline/development demo
    const now = new Date().toISOString();
    const newOrder: Order = {
      id: "ord-" + Date.now(),
      orderNumber: generateOrderNumber(),
      userId: "usr-demo",
      status: "CONFIRMED",
      paymentStatus: "PENDING",
      fulfillmentStatus: "UNFULFILLED",
      subtotal: 0,
      subtotalAmount: 0,
      discount: 0,
      discountAmount: 0,
      deliveryFee: 0,
      tax: 0,
      taxAmount: 0,
      total: 0,
      totalAmount: 0,
      deliverySlot: "Express Delivery (15-20 mins)",
      estimatedDeliveryTime: "Estimated in 18 mins",
      items: [],
      trackingHistory: buildTrackingStepsFromStatus("CONFIRMED", now),
      createdAt: now,
      updatedAt: now,
    };

    const current = this.getStoredOrders();
    this.saveStoredOrders([newOrder, ...current]);
    return newOrder;
  },

  /**
   * Cancel an order in PENDING or CONFIRMED state.
   */
  async cancelOrder(id: string, reason?: string): Promise<Order | null> {
    try {
      const res = await apiClient.post<any>(`/orders/${id}/cancel`, {
        reason: reason || "Cancelled by customer",
      });
      if (res.success && res.data) {
        const normalized = normalizeOrder(res.data);
        const current = this.getStoredOrders();
        const updated = current.map((o) => (o.id === id || o.orderNumber === id ? normalized : o));
        this.saveStoredOrders(updated);
        return normalized;
      }
    } catch (err) {
      console.warn(`API cancelOrder(${id}) failed, applying local fallback`, err);
    }

    const current = this.getStoredOrders();
    const updated = current.map((o) => {
      if (o.id === id || o.orderNumber === id) {
        return {
          ...o,
          status: "CANCELLED" as OrderStatus,
          fulfillmentStatus: "CANCELLED" as any,
          updatedAt: new Date().toISOString(),
        };
      }
      return o;
    });
    this.saveStoredOrders(updated);
    return updated.find((o) => o.id === id || o.orderNumber === id) || null;
  },
};
