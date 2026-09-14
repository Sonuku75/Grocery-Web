import { apiClient } from "@/lib/api";
import {
  InitiatePaymentRequest,
  InitiatePaymentResponse,
  Payment,
  PaymentMethod,
  VerifyPaymentRequest,
} from "@/types";

/**
 * Normalizes backend Payment representation to camelCase UI fields.
 */
export function normalizePayment(raw: any): Payment {
  if (!raw) return raw;
  return {
    id: raw.id,
    orderId: raw.orderId || raw.order_id,
    userId: raw.userId || raw.user_id,
    provider: raw.provider,
    providerPaymentId: raw.providerPaymentId || raw.provider_payment_id,
    providerOrderId: raw.providerOrderId || raw.provider_order_id,
    paymentMethod: (raw.paymentMethod || raw.payment_method) as PaymentMethod,
    amount: Number(raw.amount ?? 0),
    currency: raw.currency || "INR",
    status: raw.status,
    failureCode: raw.failureCode || raw.failure_code,
    failureMessage: raw.failureMessage || raw.failure_message,
    paidAt: raw.paidAt || raw.paid_at,
    createdAt: raw.createdAt || raw.created_at || new Date().toISOString(),
  };
}

export const paymentService = {
  /**
   * Initiates payment for an unfulfilled order using server-authoritative monetary amounts.
   */
  async initiatePayment(payload: InitiatePaymentRequest): Promise<InitiatePaymentResponse> {
    const res = await apiClient.post<any>("/payments", {
      orderId: payload.orderId,
      paymentMethod: payload.paymentMethod,
      provider: payload.provider,
    });

    const data = res.data;
    return {
      paymentId: data.paymentId || data.payment_id,
      orderId: data.orderId || data.order_id,
      amount: Number(data.amount ?? 0),
      currency: data.currency || "INR",
      provider: data.provider,
      providerOrderId: data.providerOrderId || data.provider_order_id,
      paymentMethod: (data.paymentMethod || data.payment_method) as PaymentMethod,
      status: data.status,
      clientSecret: data.clientSecret || data.client_secret,
      gatewayData: data.gatewayData || data.gateway_data,
    };
  },

  /**
   * Fetches latest payment details and status by ID.
   */
  async getPaymentStatus(paymentId: string): Promise<Payment> {
    const res = await apiClient.get<any>(`/payments/${paymentId}`);
    return normalizePayment(res.data);
  },

  /**
   * Submits gateway signature for server-side verification and status transition.
   */
  async verifyPayment(payload: VerifyPaymentRequest): Promise<Payment> {
    const res = await apiClient.post<any>("/payments/verify", {
      paymentId: payload.paymentId,
      providerPaymentId: payload.providerPaymentId,
      providerOrderId: payload.providerOrderId,
      providerSignature: payload.providerSignature,
    });
    return normalizePayment(res.data);
  },

  /**
   * Retries an unpaid order by generating a fresh payment session.
   */
  async retryPayment(
    orderId: string,
    paymentMethod?: PaymentMethod,
    provider?: string
  ): Promise<InitiatePaymentResponse> {
    const res = await apiClient.post<any>(`/orders/${orderId}/payment/retry`, {
      paymentMethod,
      provider,
    });

    const data = res.data;
    return {
      paymentId: data.paymentId || data.payment_id,
      orderId: data.orderId || data.order_id,
      amount: Number(data.amount ?? 0),
      currency: data.currency || "INR",
      provider: data.provider,
      providerOrderId: data.providerOrderId || data.provider_order_id,
      paymentMethod: (data.paymentMethod || data.payment_method) as PaymentMethod,
      status: data.status,
      clientSecret: data.clientSecret || data.client_secret,
      gatewayData: data.gatewayData || data.gateway_data,
    };
  },
};
