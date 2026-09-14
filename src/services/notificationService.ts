import { apiClient } from "@/lib/api";
import {
  DeviceItem,
  DeviceListResponse,
  NotificationItem,
  NotificationListResponse,
  NotificationPreferenceItem,
  NotificationPreferencesResponse,
  RegisterDeviceRequest,
  UnreadCountResponse,
  UpdateNotificationPreferenceRequest,
} from "@/types";

const NOTIFICATIONS_STORAGE_KEY = "cartify_notifications";

export function normalizeNotification(raw: any): NotificationItem {
  if (!raw) return raw;
  return {
    id: raw.id || "",
    userId: raw.userId || raw.user_id || "",
    type: raw.type || "GENERAL",
    title: raw.title || "",
    body: raw.body || "",
    data: raw.data || {},
    priority: raw.priority || "MEDIUM",
    status: raw.status || "UNREAD",
    referenceKey: raw.referenceKey || raw.reference_key || null,
    createdAt: raw.createdAt || raw.created_at || new Date().toISOString(),
    readAt: raw.readAt || raw.read_at || null,
    expiresAt: raw.expiresAt || raw.expires_at || null,
  };
}

export const notificationService = {
  /**
   * Fetches customer notifications with optional filters and cursor pagination.
   */
  async getNotifications(params?: {
    unreadOnly?: boolean;
    type?: string;
    limit?: number;
    cursor?: string;
  }): Promise<NotificationListResponse> {
    try {
      const response = await apiClient.get<NotificationListResponse>(
        "/notifications",
        {
          params: {
            unreadOnly: params?.unreadOnly,
            type: params?.type,
            limit: params?.limit || 20,
            cursor: params?.cursor,
          },
        }
      );

      const data = response.data;
      const rawItems = data?.items || [];
      const items = rawItems.map(normalizeNotification);
      return {
        items,
        total: data?.total ?? items.length,
        unreadCount: data?.unreadCount ?? (data as any)?.unread_count ?? items.filter((n: NotificationItem) => n.status === "UNREAD").length,
        nextCursor: data?.nextCursor || (data as any)?.next_cursor || null,
      };
    } catch (error) {
      console.warn("API notifications fetch failed, using local cache if available:", error);
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
        if (stored) {
          try {
            const cached: NotificationItem[] = JSON.parse(stored);
            return {
              items: cached,
              total: cached.length,
              unreadCount: cached.filter((c) => c.status === "UNREAD").length,
              nextCursor: null,
            };
          } catch {
            // fallback
          }
        }
      }
      return { items: [], total: 0, unreadCount: 0, nextCursor: null };
    }
  },

  /**
   * Returns current count of unread notifications for badge display.
   */
  async getUnreadCount(): Promise<number> {
    try {
      const response = await apiClient.get<UnreadCountResponse>(
        "/notifications/unread-count"
      );
      const data = response.data;
      return data?.unreadCount ?? (data as any)?.unread_count ?? 0;
    } catch {
      return 0;
    }
  },

  /**
   * Marks a single notification as read.
   */
  async markAsRead(notificationId: string): Promise<NotificationItem> {
    const response = await apiClient.patch<NotificationItem>(
      `/notifications/${notificationId}/read`
    );
    return normalizeNotification(response.data);
  },

  /**
   * Marks all customer notifications as read.
   */
  async markAllAsRead(): Promise<{ updatedCount: number }> {
    const response = await apiClient.post<{ updatedCount: number }>(
      "/notifications/read-all"
    );
    return response.data || { updatedCount: 0 };
  },

  /**
   * Deletes a customer notification.
   */
  async deleteNotification(notificationId: string): Promise<void> {
    await apiClient.delete(`/notifications/${notificationId}`);
  },

  /**
   * Fetches customer's notification preferences matrix across all categories and channels.
   */
  async getPreferences(): Promise<NotificationPreferenceItem[]> {
    try {
      const response = await apiClient.get<NotificationPreferencesResponse>(
        "/notification-preferences"
      );
      return response.data?.preferences || [];
    } catch (error) {
      console.warn("Failed to fetch notification preferences from backend:", error);
      return [];
    }
  },

  /**
   * Updates a specific category and channel preference.
   */
  async updatePreference(
    payload: UpdateNotificationPreferenceRequest
  ): Promise<NotificationPreferenceItem> {
    const response = await apiClient.put<NotificationPreferenceItem>(
      "/notification-preferences",
      payload
    );
    return response.data;
  },

  /**
   * Registers a web or mobile push device token.
   */
  async registerDevice(payload: RegisterDeviceRequest): Promise<DeviceItem> {
    const response = await apiClient.post<DeviceItem>("/devices", payload);
    return response.data;
  },

  /**
   * Lists customer's registered push devices (tokens masked).
   */
  async getDevices(): Promise<DeviceItem[]> {
    try {
      const response = await apiClient.get<DeviceListResponse>("/devices");
      return response.data?.items || [];
    } catch {
      return [];
    }
  },

  /**
   * Deactivates a registered push device on logout or user request.
   */
  async deactivateDevice(deviceId: string): Promise<void> {
    await apiClient.delete(`/devices/${deviceId}`);
  },
};
