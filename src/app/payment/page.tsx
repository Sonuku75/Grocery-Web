"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { Input } from "@/components/common/Input";
import {
  CreditCard,
  QrCode,
  ShieldCheck,
  CheckCircle2,
  Lock,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  Wallet,
  Building2,
  Banknote,
  Sparkles,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";
import { paymentService } from "@/services/paymentService";
import { orderService } from "@/services/orderService";
import { Order, Payment, PaymentMethod } from "@/types";
import { formatCurrency } from "@/lib/utils";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const orderId = searchParams.get("orderId");
  const initialPaymentId = searchParams.get("paymentId");

  const [order, setOrder] = useState<Order | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>("UPI");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load Order and Payment Status
  useEffect(() => {
    async function loadData() {
      if (!orderId && !initialPaymentId) {
        setLoading(false);
        return;
      }

      try {
        if (orderId) {
          try {
            const fetchedOrder = await orderService.getOrderById(orderId);
            setOrder(fetchedOrder);
          } catch (e) {
            console.warn("Could not load order details directly:", e);
          }
        }

        if (initialPaymentId) {
          const fetchedPayment = await paymentService.getPaymentStatus(initialPaymentId);
          setPayment(fetchedPayment);
          if (fetchedPayment.paymentMethod) {
            setSelectedMethod(fetchedPayment.paymentMethod);
          }
        }
      } catch (err: any) {
        console.error("Error loading payment info:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [orderId, initialPaymentId]);

  // Handle Initiating / Paying
  const handleAuthorizePayment = async (e?: React.FormEvent, simulateFail: boolean = false) => {
    if (e) e.preventDefault();
    setProcessing(true);
    setErrorMessage(null);

    try {
      let activePaymentId = payment?.id || initialPaymentId;

      // If no active payment, initiate one first
      if (!activePaymentId && orderId) {
        const initRes = await paymentService.initiatePayment({
          orderId,
          paymentMethod: selectedMethod,
          provider: "mock",
        });
        activePaymentId = initRes.paymentId;
      }

      if (!activePaymentId) {
        showToast("No active payment or order reference found.", "error");
        setProcessing(false);
        return;
      }

      setProcessing(false);
      setVerifying(true);

      // Submit verification with mock signature
      const sig = simulateFail ? "mock_invalid_signature" : "mock_valid_signature";
      const paymentIdToSubmit = simulateFail ? "pay_fail_simulated" : "pay_mock_success";

      const verifiedPayment = await paymentService.verifyPayment({
        paymentId: activePaymentId,
        providerPaymentId: paymentIdToSubmit,
        providerSignature: sig,
      });

      setPayment(verifiedPayment);
      showToast("Payment verified and processed successfully!", "success");

      // Redirect to orders page after short delay
      setTimeout(() => {
        router.push(order?.orderNumber ? `/orders/${order.orderNumber}` : "/orders");
      }, 1200);
    } catch (err: any) {
      console.error("Payment authorization error:", err);
      const msg = err?.message || "Payment verification failed. Please retry.";
      setErrorMessage(msg);
      showToast(msg, "error");
    } finally {
      setProcessing(false);
      setVerifying(false);
    }
  };

  const handleRetry = async () => {
    if (!orderId) {
      showToast("Cannot retry without order ID.", "error");
      return;
    }

    setProcessing(true);
    setErrorMessage(null);
    try {
      const retryRes = await paymentService.retryPayment(orderId, selectedMethod, "mock");
      const freshPayment = await paymentService.getPaymentStatus(retryRes.paymentId);
      setPayment(freshPayment);
      showToast("Fresh payment attempt created.", "info");
    } catch (err: any) {
      showToast(err?.message || "Failed to retry payment", "error");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center p-4">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-600 mb-4" />
        <p className="text-sm text-slate-500">Connecting to high-security payment gateway...</p>
      </div>
    );
  }

  const isAlreadyPaid = payment?.status === "PAID";
  const amountToDisplay = payment?.amount ?? order?.total ?? 0;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Breadcrumb
        items={[
          { label: "Checkout", href: "/checkout" },
          { label: "Payment Gateway" },
        ]}
      />

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 sm:p-10 shadow-sm space-y-6">
        {/* Header with 256-bit SSL Lock */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 text-[10px] font-bold uppercase tracking-wider mb-1.5">
              <Sparkles className="w-3 h-3" />
              Module 12 • High-Security Payment Gateway
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Authoritative Payment Gateway
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              HMAC-SHA256 signature verified • Zero client-side price tampering
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 px-3 py-1.5 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40">
            <Lock className="w-3.5 h-3.5" />
            <span>256-bit SSL</span>
          </div>
        </div>

        {/* Order & Amount Snapshot */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Order Reference
            </span>
            <span className="text-sm font-mono font-bold text-slate-900 dark:text-white">
              {order?.orderNumber || orderId || "CRT-SESSION"}
            </span>
          </div>
          <div className="text-right">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Amount Payable
            </span>
            <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
              {formatCurrency(Number(amountToDisplay))}
            </span>
          </div>
        </div>

        {/* Success Banner if already paid */}
        {isAlreadyPaid && (
          <div className="p-5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center space-y-3">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-emerald-900 dark:text-emerald-200">
              Payment Confirmed &amp; Captured!
            </h3>
            <p className="text-xs text-emerald-700 dark:text-emerald-300">
              Transaction reference: <span className="font-mono">{payment?.id}</span>
            </p>
            <div className="pt-2">
              <Link
                href="/orders"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition"
              >
                Track Order
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs flex-1">
              <strong>Payment Failed:</strong> {errorMessage}
              <div className="mt-2">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-bold text-[11px] transition"
                >
                  Retry Payment Attempt
                </button>
              </div>
            </div>
          </div>
        )}

        {!isAlreadyPaid && (
          <>
            {/* Method selection */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Select Payment Channel
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                {[
                  { id: "UPI" as PaymentMethod, title: "UPI / QR", icon: QrCode },
                  { id: "CARD" as PaymentMethod, title: "Card", icon: CreditCard },
                  { id: "NET_BANKING" as PaymentMethod, title: "Net Banking", icon: Building2 },
                  { id: "WALLET" as PaymentMethod, title: "Wallets", icon: Wallet },
                  { id: "COD" as PaymentMethod, title: "Cash On Delivery", icon: Banknote },
                ].map((m) => {
                  const Icon = m.icon;
                  const isSelected = selectedMethod === m.id;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setSelectedMethod(m.id)}
                      className={`p-3 rounded-2xl border-2 flex flex-col items-center text-center gap-1.5 transition-all ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 font-bold ring-1 ring-emerald-600"
                          : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-[11px] leading-tight">{m.title}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Method Details */}
            <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60">
              {selectedMethod === "UPI" && (
                <div className="text-center space-y-3">
                  <QrCode className="w-14 h-14 mx-auto text-emerald-600" />
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                      Instant UPI Auto-Verification
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Supports Google Pay, PhonePe, Paytm, BHIM and all UPI apps.
                    </p>
                  </div>
                </div>
              )}

              {selectedMethod === "CARD" && (
                <div className="space-y-3 max-w-md mx-auto">
                  <Input label="Name on Card" defaultValue="Alex Rivera" disabled />
                  <Input label="Card Number" defaultValue="•••• •••• •••• 4242" disabled />
                  <div className="grid grid-cols-2 gap-3">
                    <Input label="Valid Thru" defaultValue="12/28" disabled />
                    <Input label="CVV" defaultValue="•••" disabled />
                  </div>
                </div>
              )}

              {selectedMethod === "NET_BANKING" && (
                <div className="text-center space-y-2">
                  <Building2 className="w-10 h-10 mx-auto text-emerald-600" />
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Supports 50+ Indian Banks via Gateway Direct Transfer
                  </p>
                </div>
              )}

              {selectedMethod === "WALLET" && (
                <div className="text-center space-y-2">
                  <Wallet className="w-10 h-10 mx-auto text-emerald-600" />
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Amazon Pay, Mobikwik, PhonePe Wallet &amp; Freecharge
                  </p>
                </div>
              )}

              {selectedMethod === "COD" && (
                <div className="text-center space-y-2">
                  <Banknote className="w-10 h-10 mx-auto text-emerald-600" />
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Pay exact cash upon arrival at your doorstep.
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons with Sandbox Simulator controls */}
            <div className="space-y-3 pt-2">
              <Button
                type="button"
                variant="primary"
                size="lg"
                className="w-full py-4 text-sm font-bold"
                isLoading={processing || verifying}
                onClick={(e) => handleAuthorizePayment(e, false)}
                leftIcon={<CheckCircle2 className="w-5 h-5" />}
              >
                {verifying
                  ? "Verifying Gateway HMAC Signature..."
                  : processing
                  ? "Contacting Gateway..."
                  : `Pay & Confirm • ${formatCurrency(Number(amountToDisplay))}`}
              </Button>

              {/* Dev Simulation Option */}
              <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
                <span>Sandbox Testing Controls:</span>
                <button
                  type="button"
                  onClick={(e) => handleAuthorizePayment(e, true)}
                  className="text-rose-500 hover:text-rose-700 font-semibold underline text-[11px]"
                >
                  Simulate Payment Failure
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function PaymentPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <RefreshCw className="w-8 h-8 animate-spin text-emerald-600" />
        </div>
      }
    >
      <PaymentContent />
    </Suspense>
  );
}
