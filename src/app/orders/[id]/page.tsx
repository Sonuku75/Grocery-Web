"use client";

import React, { useEffect, useState, use } from "react";
import Image from "next/image";
import Link from "next/link";
import { Order, OrderStatus } from "@/types";
import { orderService } from "@/services/orderService";
import { useCart } from "@/context/CartContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  CheckCircle2,
  Clock,
  MapPin,
  CreditCard,
  RotateCcw,
  AlertCircle,
  XCircle,
  ShoppingBag,
  Truck,
  Copy,
  Check,
  Printer,
  ChevronRight,
  ShieldCheck,
  Receipt,
  FileText,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

interface OrderPageProps {
  params: Promise<{ id: string }>;
}

export default function OrderDetailsPage({ params }: OrderPageProps) {
  const { id } = use(params);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedNumber, setCopiedNumber] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const { showToast } = useToast();
  const { addToCart } = useCart();

  useEffect(() => {
    async function load() {
      try {
        const ord = await orderService.getOrderById(id);
        setOrder(ord);
      } catch (err) {
        console.error("Failed to load order details:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleCopyOrderNumber = () => {
    if (!order) return;
    navigator.clipboard.writeText(order.orderNumber);
    setCopiedNumber(true);
    showToast("Order number copied to clipboard", "info");
    setTimeout(() => setCopiedNumber(false), 2000);
  };

  const handleCancelOrder = async () => {
    if (!order || cancelling) return;
    setCancelling(true);
    try {
      const cancelled = await orderService.cancelOrder(
        order.orderNumber || order.id,
        cancelReason.trim() || "Cancelled by customer"
      );
      if (cancelled) {
        setOrder(cancelled);
        showToast("Order cancelled successfully.", "info");
        setIsCancelModalOpen(false);
      }
    } catch (err: any) {
      showToast(err?.message || "Failed to cancel order.", "error");
    } finally {
      setCancelling(false);
    }
  };

  const handlePrintReceipt = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="inline-block w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
            Loading order snapshot and tracking timeline...
          </p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 py-16">
        <div className="max-w-md mx-auto px-4 text-center space-y-4">
          <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 text-slate-400 rounded-3xl flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Order Not Found</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            The requested order could not be located or you may not have permission to view it.
          </p>
          <Link href="/orders" className="inline-block pt-2">
            <Button variant="primary" size="md">
              Return to My Orders
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const normalizedStatus = (order.status || "").toUpperCase();
  const isCancelled = normalizedStatus === "CANCELLED" || normalizedStatus === "FAILED";
  const isDelivered = normalizedStatus === "DELIVERED";
  const isCancellable = normalizedStatus === "PENDING" || normalizedStatus === "CONFIRMED";

  const TRACKING_STEPS = [
    { key: "PENDING", label: "Order Placed", desc: "Received at Cartify Hub" },
    { key: "CONFIRMED", label: "Confirmed", desc: "Inventory locked & verified" },
    { key: "PROCESSING", label: "Packing", desc: "Fresh produce sealed" },
    { key: "SHIPPED", label: "Shipped", desc: "Dispatched from warehouse" },
    { key: "OUT_FOR_DELIVERY", label: "Out for Delivery", desc: "With electric rider" },
    { key: "DELIVERED", label: "Delivered", desc: "Handed over safely" },
  ];

  const statusProgressIndex: Record<string, number> = {
    PENDING: 0,
    ORDER_PLACED: 0,
    CONFIRMED: 1,
    PROCESSING: 2,
    PREPARING: 2,
    SHIPPED: 3,
    OUT_FOR_DELIVERY: 4,
    DELIVERED: 5,
    CANCELLED: -1,
    FAILED: -1,
  };

  const currentStepIdx = statusProgressIndex[normalizedStatus] ?? 0;

  // Address Snapshot Data
  const addr = order.addressSnapshot || (order.address ? {
    fullName: order.address.fullName || order.address.recipientName || "Customer",
    phone: order.address.phone || (order.address as any).mobile || "",
    addressLine1: order.address.addressLine1 || (order.address as any).houseFlat || "",
    addressLine2: order.address.addressLine2 || (order.address as any).street || "",
    city: order.address.city || "",
    state: order.address.state || "",
    postalCode: order.address.postalCode || (order.address as any).pincode || "",
  } : null);

  const subtotal = order.subtotalAmount ?? order.subtotal ?? 0;
  const discount = order.discountAmount ?? order.discount ?? 0;
  const deliveryFee = order.deliveryFee ?? 0;
  const tax = order.taxAmount ?? order.tax ?? 0;
  const total = order.totalAmount ?? order.total ?? 0;

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <Breadcrumb
          items={[
            { label: "My Orders", href: "/orders" },
            { label: `#${order.orderNumber}` },
          ]}
        />

        {/* Top Header Card */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  Order #{order.orderNumber}
                </h1>
                <button
                  type="button"
                  onClick={handleCopyOrderNumber}
                  title="Copy Order Number"
                  className="p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition"
                >
                  {copiedNumber ? (
                    <Check className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                    isDelivered
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                      : isCancelled
                      ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                      : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
                  }`}
                >
                  {isDelivered ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : isCancelled ? (
                    <XCircle className="w-3.5 h-3.5" />
                  ) : (
                    <Truck className="w-3.5 h-3.5" />
                  )}
                  {normalizedStatus.replace(/_/g, " ")}
                </span>
              </div>

              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Placed on {formatDate(order.createdAt)} • Payment:{" "}
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {order.paymentStatus}
                </span>{" "}
                ({(order.paymentMethod || "COD").toUpperCase()})
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Printer className="w-4 h-4" />}
                onClick={handlePrintReceipt}
              >
                Print Receipt
              </Button>

              {isCancellable && (
                <Button
                  variant="outline"
                  size="sm"
                  className="text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:border-rose-300"
                  onClick={() => setIsCancelModalOpen(true)}
                >
                  Cancel Order
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Live Delivery Stepper or Cancelled Banner */}
        {!isCancelled ? (
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-600" />
                <span>Delivery Tracking Progress</span>
              </h3>
              {order.deliverySlot && (
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60">
                  {order.deliverySlot}
                </span>
              )}
            </div>

            {/* Step Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 relative">
              {TRACKING_STEPS.map((step, idx) => {
                const isCompleted = currentStepIdx >= idx;
                const isCurrent = currentStepIdx === idx;

                return (
                  <div
                    key={step.key}
                    className="flex flex-col items-center text-center gap-2.5 p-3 rounded-2xl transition bg-slate-50/50 dark:bg-slate-800/20 border border-slate-100 dark:border-slate-800"
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                        isCompleted
                          ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/20 ring-4 ring-emerald-50 dark:ring-emerald-950/40"
                          : "bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400"
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
                    </div>
                    <div className="space-y-0.5">
                      <h4
                        className={`text-xs font-bold ${
                          isCurrent
                            ? "text-emerald-600 dark:text-emerald-400"
                            : isCompleted
                            ? "text-slate-900 dark:text-white"
                            : "text-slate-400"
                        }`}
                      >
                        {step.label}
                      </h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                        {step.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="p-6 rounded-3xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-sm text-rose-800 dark:text-rose-300 flex items-start gap-4">
            <XCircle className="w-6 h-6 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-bold text-base">This Order Has Been Cancelled</h4>
              <p className="text-xs text-rose-700 dark:text-rose-300">
                The items in this order will not be delivered. If your payment was captured, a full refund has been automatically initiated back to your original payment method.
              </p>
            </div>
          </div>
        )}

        {/* Order Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Authoritative Purchase-time Items Snapshot */}
          <div className="lg:col-span-8 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600" />
                <span>Purchased Items Snapshot ({order.items.length})</span>
              </h3>
              <span className="text-xs text-slate-400">Locked at time of order</span>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {order.items.map((item) => {
                const img =
                  item.thumbnailUrl ||
                  item.productImage ||
                  "/images/placeholder.svg";

                return (
                  <div
                    key={item.id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="relative w-16 h-16 rounded-2xl overflow-hidden bg-slate-50 dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700 shrink-0">
                        <Image
                          src={img}
                          alt={item.productName}
                          fill
                          className="object-cover"
                        />
                      </div>
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                          {item.productName}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                          {item.variantName && (
                            <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 font-medium">
                              {item.variantName}
                            </span>
                          )}
                          {item.sku && (
                            <span className="font-mono text-[11px] text-slate-400">
                              SKU: {item.sku}
                            </span>
                          )}
                          <span>•</span>
                          <span>
                            {formatCurrency(item.unitPrice)} × {item.quantity}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right sm:text-right">
                      {item.mrp && item.mrp > item.unitPrice && (
                        <div className="text-xs line-through text-slate-400">
                          {formatCurrency(item.mrp * item.quantity)}
                        </div>
                      )}
                      <div className="text-sm font-extrabold text-slate-900 dark:text-white">
                        {formatCurrency(item.lineTotal ?? item.totalPrice ?? item.unitPrice * item.quantity)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Address & Payment Breakdown */}
          <div className="lg:col-span-4 space-y-6">
            {/* Delivery Destination Snapshot */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
                <MapPin className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Delivery Destination
                </h3>
              </div>

              {addr ? (
                <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5 leading-relaxed">
                  <p className="font-bold text-slate-900 dark:text-white text-sm">
                    {addr.fullName}
                  </p>
                  <p>{addr.addressLine1}</p>
                  {addr.addressLine2 && <p>{addr.addressLine2}</p>}
                  <p>
                    {addr.city}, {addr.state} {addr.postalCode}
                  </p>
                  {addr.phone && (
                    <p className="font-mono text-slate-500 dark:text-slate-400 pt-1">
                      Phone: {addr.phone}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Address snapshot attached to order.</p>
              )}

              {order.notes && (
                <div className="mt-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-400">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">Notes: </span>
                  {order.notes}
                </div>
              )}
            </div>

            {/* Authoritative Financial Breakdown */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
                <CreditCard className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Payment Summary
                </h3>
              </div>

              <div className="space-y-2.5 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {formatCurrency(subtotal)}
                  </span>
                </div>

                {discount > 0 && (
                  <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-medium">
                    <span>
                      Coupon Discount {order.couponCode ? `(${order.couponCode})` : ""}
                    </span>
                    <span>-{formatCurrency(discount)}</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span>Delivery Fee</span>
                  <span>
                    {deliveryFee === 0 ? (
                      <strong className="text-emerald-600 font-bold">FREE</strong>
                    ) : (
                      formatCurrency(deliveryFee)
                    )}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span>Taxes &amp; Packaging</span>
                  <span className="text-slate-900 dark:text-white font-medium">
                    {formatCurrency(tax)}
                  </span>
                </div>

                <div className="flex justify-between pt-3 border-t border-slate-200 dark:border-slate-700 text-base font-extrabold text-slate-900 dark:text-white">
                  <span>Total Paid</span>
                  <span className="text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(total)}
                  </span>
                </div>
              </div>

              <div className="pt-2 text-[11px] text-slate-400 text-center flex items-center justify-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>100% Secure &amp; Verified Transaction</span>
              </div>
            </div>
          </div>
        </div>

        {/* Cancellation Modal */}
        {isCancelModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
            <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-md w-full p-6 sm:p-8 space-y-4 shadow-2xl border border-slate-200 dark:border-slate-800">
              <div className="w-12 h-12 rounded-full bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>

              <div className="text-center space-y-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Cancel Order #{order.orderNumber}?
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Are you sure you want to cancel this order? This action is permanent and cannot be undone.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reason for cancellation (Optional)
                </label>
                <textarea
                  rows={3}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Changed my mind, ordered duplicate items..."
                  className="w-full p-3 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <Button
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => setIsCancelModalOpen(false)}
                  disabled={cancelling}
                >
                  Keep Order
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  className="w-full !bg-rose-600 hover:!bg-rose-700 !text-white"
                  onClick={handleCancelOrder}
                  disabled={cancelling}
                >
                  {cancelling ? "Cancelling..." : "Confirm Cancel"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
