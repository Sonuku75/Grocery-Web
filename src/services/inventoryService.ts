import { apiClient, isMockMode } from "@/lib/api";
import { CustomerInventoryResponse, AdminInventoryResponse, AdminInventoryListResponse, AdminAdjustStockPayload } from "@/types";

export const inventoryService = {
  /**
   * Retrieves live customer-safe inventory availability for a variant.
   */
  async getVariantStock(variantId: string): Promise<CustomerInventoryResponse> {
    if (!variantId) {
      return {
        variantId: "",
        availableQuantity: 0,
        isAvailable: false,
        isLowStock: false,
      };
    }

    if (isMockMode()) {
      return {
        variantId,
        availableQuantity: 99,
        isAvailable: true,
        isLowStock: false,
      };
    }

    try {
      const response = await apiClient.get<CustomerInventoryResponse>(
        `/inventory/variants/${encodeURIComponent(variantId)}`
      );
      if (response.data) {
        return {
          variantId: response.data.variantId || response.data.variant_id || variantId,
          availableQuantity: Number(response.data.availableQuantity ?? response.data.available_quantity ?? 0),
          isAvailable: Boolean(response.data.isAvailable ?? response.data.is_available ?? false),
          isLowStock: Boolean(response.data.isLowStock ?? response.data.is_low_stock ?? false),
        };
      }
      return {
        variantId,
        availableQuantity: 0,
        isAvailable: false,
        isLowStock: false,
      };
    } catch (error) {
      console.warn(`[inventoryService] Failed to load stock for variant ${variantId}:`, error);
      // Fallback gracefully to prevent customer UI crashes
      return {
        variantId,
        availableQuantity: 99,
        isAvailable: true,
        isLowStock: false,
      };
    }
  },

  /**
   * Admin: List inventory with optional filters.
   */
  async listAdminInventory(params?: {
    productId?: string;
    variantId?: string;
    lowStock?: boolean;
    outOfStock?: boolean;
    isActive?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<AdminInventoryListResponse> {
    const query = new URLSearchParams();
    if (params?.productId) query.set("product_id", params.productId);
    if (params?.variantId) query.set("variant_id", params.variantId);
    if (params?.lowStock !== undefined) query.set("low_stock", String(params.lowStock));
    if (params?.outOfStock !== undefined) query.set("out_of_stock", String(params.outOfStock));
    if (params?.isActive !== undefined) query.set("is_active", String(params.isActive));
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    const endpoint = `/admin/inventory${qs ? `?${qs}` : ""}`;
    const response = await apiClient.get<AdminInventoryListResponse>(endpoint);
    return response.data;
  },

  /**
   * Admin: Adjust stock quantity for a variant with audit trail reason.
   */
  async adjustStock(
    variantId: string,
    payload: AdminAdjustStockPayload
  ): Promise<AdminInventoryResponse> {
    const response = await apiClient.post<AdminInventoryResponse>(
      `/admin/inventory/${encodeURIComponent(variantId)}/adjust`,
      {
        quantityChange: payload.quantityChange,
        transactionType: payload.transactionType || (payload.quantityChange > 0 ? "RESTOCK" : "ADJUSTMENT"),
        reason: payload.reason,
        referenceType: payload.referenceType,
        referenceId: payload.referenceId,
      }
    );
    return response.data;
  },
};
