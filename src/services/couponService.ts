import { Coupon } from "@/types";
import { MOCK_COUPONS } from "@/lib/mockData";
import { apiClient, isMockMode } from "@/lib/api";

export const couponService = {
  /**
   * Fetches active coupons from the backend API if online,
   * falling back to curated mock coupons if mock mode is active or backend is unreachable.
   */
  async getAvailableCoupons(): Promise<Coupon[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<any>("/coupons");
        const items = res.data?.items || res.data || [];
        if (Array.isArray(items) && items.length > 0) {
          return items.map((c: any) => ({
            id: c.id,
            code: c.code,
            name: c.name || c.code,
            description: c.description || "",
            discountType:
              (c.discountType || c.discount_type || "percent").toString().toLowerCase() === "percentage"
                ? "percent"
                : (c.discountType || c.discount_type || "fixed").toString().toLowerCase() === "fixed_amount"
                ? "fixed"
                : (c.discountType || c.discount_type || "percent"),
            discountValue: Number(c.discountValue ?? c.discount_value ?? 0),
            minOrderAmount: Number(c.minimumOrderValue ?? c.minimum_order_value ?? c.minOrderAmount ?? 0),
            minimumOrderValue: Number(c.minimumOrderValue ?? c.minimum_order_value ?? c.minOrderAmount ?? 0),
            maxDiscount: c.maximumDiscount != null ? Number(c.maximumDiscount) : c.maximum_discount != null ? Number(c.maximum_discount) : undefined,
            maximumDiscount: c.maximumDiscount != null ? Number(c.maximumDiscount) : c.maximum_discount != null ? Number(c.maximum_discount) : undefined,
            validUntil: c.expiresAt || c.expires_at || c.validUntil || "",
            expiresAt: c.expiresAt || c.expires_at || c.validUntil || "",
            isActive: c.isActive ?? c.is_active ?? true,
          }));
        }
      } catch (err) {
        console.warn("Failed to fetch live coupons, falling back to mock", err);
      }
    }
    return MOCK_COUPONS;
  },

  /**
   * Validates a coupon code against an active order/cart.
   * If authenticated, tests against the live `/cart/coupon/validate` endpoint.
   */
  async validateCoupon(
    code: string,
    currentTotal: number
  ): Promise<{ valid: boolean; coupon?: Coupon; discount?: number; message: string }> {
    const hasToken = typeof window !== "undefined" && !!apiClient.getAccessToken();
    if (!isMockMode() && hasToken) {
      try {
        const res = await apiClient.post<any>("/cart/coupon/validate", { code });
        if (res.data) {
          const rawC = res.data.coupon;
          const couponObj: Coupon | undefined = rawC
            ? {
                id: rawC.id,
                code: rawC.code,
                name: rawC.name || rawC.code,
                description: rawC.description || "",
                discountType:
                  (rawC.discountType || rawC.discount_type || "percent").toString().toLowerCase() === "percentage"
                    ? "percent"
                    : "fixed",
                discountValue: Number(rawC.discountValue ?? rawC.discount_value ?? 0),
                minOrderAmount: Number(rawC.minimumOrderValue ?? rawC.minimum_order_value ?? 0),
                minimumOrderValue: Number(rawC.minimumOrderValue ?? rawC.minimum_order_value ?? 0),
                maxDiscount: rawC.maximumDiscount != null ? Number(rawC.maximumDiscount) : undefined,
                maximumDiscount: rawC.maximumDiscount != null ? Number(rawC.maximumDiscount) : undefined,
                validUntil: rawC.expiresAt || rawC.expires_at || "",
                expiresAt: rawC.expiresAt || rawC.expires_at || "",
                isActive: rawC.isActive ?? rawC.is_active ?? true,
              }
            : undefined;

          return {
            valid: Boolean(res.data.valid),
            discount: Number(res.data.discount ?? 0),
            message:
              res.data.message ||
              res.message ||
              (res.data.valid ? "Coupon applied successfully!" : "Coupon is invalid."),
            coupon: couponObj,
          };
        }
      } catch (err: any) {
        return {
          valid: false,
          discount: 0,
          message: err?.message || err?.error?.message || "Coupon validation failed.",
        };
      }
    }

    // Local / unauthenticated fallback
    const coupon = MOCK_COUPONS.find((c) => c.code.toUpperCase() === code.trim().toUpperCase());
    if (!coupon) {
      return { valid: false, discount: 0, message: "Invalid coupon code. Try SAVE20 or FLAT150." };
    }
    if (currentTotal < coupon.minOrderAmount) {
      return {
        valid: false,
        discount: 0,
        message: `Order must be at least ₹${coupon.minOrderAmount} to redeem this offer.`,
      };
    }

    let discount = 0;
    if (coupon.discountType === "percent") {
      discount = (currentTotal * coupon.discountValue) / 100;
      if (coupon.maxDiscount) discount = Math.min(discount, coupon.maxDiscount);
    } else {
      discount = coupon.discountValue;
    }
    discount = Math.min(discount, currentTotal);

    return {
      valid: true,
      coupon,
      discount,
      message: `Coupon ${coupon.code} applied successfully!`,
    };
  },
};
