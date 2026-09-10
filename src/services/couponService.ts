import { Coupon } from "@/types";
import { MOCK_COUPONS } from "@/lib/mockData";

export const couponService = {
  async getAvailableCoupons(): Promise<Coupon[]> {
    return MOCK_COUPONS;
  },

  async validateCoupon(code: string, currentTotal: number): Promise<{ valid: boolean; coupon?: Coupon; message: string }> {
    const coupon = MOCK_COUPONS.find((c) => c.code.toUpperCase() === code.trim().toUpperCase());
    if (!coupon) {
      return { valid: false, message: "Invalid coupon code." };
    }
    if (currentTotal < coupon.minOrderAmount) {
      return {
        valid: false,
        message: `Order must be at least $${coupon.minOrderAmount} to redeem this offer.`,
      };
    }
    return { valid: true, coupon, message: `Coupon ${coupon.code} applied!` };
  },
};
