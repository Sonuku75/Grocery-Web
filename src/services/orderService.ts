import { apiClient } from "@/lib/api";
import { Order, OrderStatus, TrackingStep } from "@/types";
import { MOCK_ORDERS } from "@/lib/mockData";
import { generateOrderNumber } from "@/lib/utils";

const STORAGE_KEY = "cartify_orders";

function buildInitialTrackingSteps(createdAt: string): TrackingStep[] {
  return [
    {
      status: "order_placed",
      title: "Order Placed",
      description: "Order received by Cartify Hub",
      timestamp: createdAt,
      completed: true,
      current: false,
    },
    {
      status: "confirmed",
      title: "Order Confirmed",
      description: "Store verified item inventory & cold-chain queue",
      timestamp: createdAt,
      completed: true,
      current: true,
    },
    {
      status: "preparing",
      title: "Packing Order",
      description: "Carefully picking fresh produce & sealing bag",
      timestamp: "",
      completed: false,
      current: false,
    },
    {
      status: "out_for_delivery",
      title: "Out for Delivery",
      description: "Assigned to Cartify electric delivery rider",
      timestamp: "",
      completed: false,
      current: false,
    },
    {
      status: "delivered",
      title: "Delivered",
      description: "Safe doorstep delivery with photo confirmation",
      timestamp: "",
      completed: false,
      current: false,
    },
  ];
}

export const orderService = {
  getStoredOrders(): Order[] {
    if (typeof window === "undefined") return MOCK_ORDERS;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(MOCK_ORDERS));
      return MOCK_ORDERS;
    }
    try {
      return JSON.parse(stored) as Order[];
    } catch {
      return MOCK_ORDERS;
    }
  },

  saveStoredOrders(orders: Order[]) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(orders));
  },

  async getOrders(): Promise<Order[]> {
    const res = await apiClient.get<Order[]>("/orders");
    if (res.success && res.data && res.data.length > 0) {
      this.saveStoredOrders(res.data);
      return res.data;
    }
    return this.getStoredOrders();
  },

  async getOrderById(id: string): Promise<Order | null> {
    const res = await apiClient.get<Order>(`/orders/${id}`);
    if (res.success && res.data) {
      return res.data;
    }

    const orders = this.getStoredOrders();
    const found = orders.find((o) => o.id === id || o.orderNumber === id);
    return found || null;
  },

  async createOrder(orderData: Partial<Order>): Promise<Order> {
    const res = await apiClient.post<Order>("/orders", orderData);
    if (res.success && res.data) {
      const current = this.getStoredOrders();
      this.saveStoredOrders([res.data, ...current]);
      return res.data;
    }

    const now = new Date().toISOString();
    const newOrder: Order = {
      id: "ord-" + Date.now(),
      orderNumber: generateOrderNumber(),
      userId: orderData.userId || "usr-demo",
      address: orderData.address!,
      items: orderData.items || [],
      subtotal: orderData.subtotal || 0,
      discount: orderData.discount || 0,
      deliveryFee: orderData.deliveryFee || 0,
      tax: orderData.tax || 0,
      total: orderData.total || 0,
      status: "confirmed",
      paymentStatus: orderData.paymentStatus || "paid",
      paymentMethod: orderData.paymentMethod || "card",
      paymentTransactionId: orderData.paymentTransactionId || "txn_" + Math.random().toString(36).substring(2, 10),
      deliverySlot: orderData.deliverySlot || "Express Delivery (15-20 mins)",
      estimatedDeliveryTime: "Estimated in 18 mins",
      trackingHistory: buildInitialTrackingSteps(now),
      createdAt: now,
      updatedAt: now,
    };

    const current = this.getStoredOrders();
    this.saveStoredOrders([newOrder, ...current]);
    return newOrder;
  },

  async cancelOrder(id: string): Promise<Order | null> {
    const res = await apiClient.post<Order>(`/orders/${id}/cancel`);
    if (res.success && res.data) {
      const current = this.getStoredOrders();
      const updated = current.map((o) => (o.id === id ? res.data : o));
      this.saveStoredOrders(updated);
      return res.data;
    }

    const current = this.getStoredOrders();
    const updated = current.map((o) => {
      if (o.id === id) {
        return {
          ...o,
          status: "cancelled" as OrderStatus,
          updatedAt: new Date().toISOString(),
        };
      }
      return o;
    });
    this.saveStoredOrders(updated);
    return updated.find((o) => o.id === id) || null;
  },
};
