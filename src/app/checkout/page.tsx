"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Address, CheckoutConfirmResponse, CheckoutSummary, PaymentMethod } from "@/types";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { addressService } from "@/services/addressService";
import { checkoutService } from "@/services/checkoutService";
import { orderService } from "@/services/orderService";
import { paymentService } from "@/services/paymentService";
import { AddressModal } from "@/components/addresses/AddressModal";
import { Button } from "@/components/common/Button";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { formatCurrency } from "@/lib/utils";
import {
  MapPin,
  Clock,
  CheckCircle2,
  Plus,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  Check,
  Truck,
  Lock,
  Sparkles,
  PackageCheck,
  ShoppingBag,
  RefreshCw,
  Copy,
  CreditCard,
  QrCode,
  Building2,
  Wallet,
  Banknote,
} from "lucide-react";

const DELIVERY_SLOTS = [
  {
    id: "express-15",
    title: "Express 15-Minute Delivery",
    time: "⚡ Instant Dispatch • Arriving in 10-15 mins",
    badge: "Fastest",
  },
  {
    id: "today-morning",
    title: "Today Morning",
    time: "7:00 AM – 9:00 AM",
    badge: "Eco Saver",
  },
  {
    id: "today-afternoon",
    title: "Today Afternoon",
    time: "1:00 PM – 3:00 PM",
    badge: null,
  },
  {
    id: "today-evening",
    title: "Today Evening",
    time: "6:00 PM – 8:00 PM",
    badge: "Popular",
  },
  {
    id: "tomorrow-morning",
    title: "Tomorrow Morning",
    time: "7:00 AM – 9:00 AM",
    badge: null,
  },
];

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, refreshCart } = useCart();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { showToast } = useToast();

  const [checkoutSummary, setCheckoutSummary] = useState<CheckoutSummary | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>("");
  const [deliverySlot, setDeliverySlot] = useState("Today • Express 15-Minute Delivery");
  const [notes, setNotes] = useState("");
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<PaymentMethod>("UPI");

  const [isAddressModalOpen, setIsAddressModalOpen] = useState(false);
  const [isSwitchAddressOpen, setIsSwitchAddressOpen] = useState(false);

  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [confirmedData, setConfirmedData] = useState<CheckoutConfirmResponse | null>(null);
  const [copiedSessionId, setCopiedSessionId] = useState(false);

  // 1. Initial Data Fetching & Authorization
  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push("/login?redirect=/checkout");
      return;
    }

    async function initializeCheckout() {
      setLoading(true);
      try {
        // Load user delivery addresses
        const addrs = await addressService.getAddresses();
        setAddresses(addrs);
        const defaultAddr = addrs.find((a) => a.isDefault || a.is_default) || addrs[0];
        const initialAddrId = defaultAddr?.id || "";
        setSelectedAddressId(initialAddrId);

        // Fetch authoritative checkout preview
        if (cart.items.length > 0) {
          const preview = await checkoutService.previewCheckout({
            addressId: initialAddrId || undefined,
            deliverySlot,
          });
          setCheckoutSummary(preview);
        }
      } catch (err: any) {
        console.error("Failed to initialize checkout preview", err);
        showToast(
          err?.message || "Failed to load checkout session. Please try again.",
          "error"
        );
      } finally {
        setLoading(false);
      }
    }

    initializeCheckout();
  }, [isAuthenticated, authLoading, cart.items.length]);

  // 2. Handle Address Change
  const handleSelectAddress = async (addrId: string) => {
    setSelectedAddressId(addrId);
    setIsSwitchAddressOpen(false);
    try {
      const updated = await checkoutService.previewCheckout({
        addressId: addrId,
        deliverySlot,
      });
      setCheckoutSummary(updated);
      showToast("Delivery address updated for checkout", "success");
    } catch (err: any) {
      showToast(err?.message || "Failed to update address", "error");
    }
  };

  // 3. Handle Create Address
  const handleCreateAddress = async (data: Parameters<typeof addressService.addAddress>[0]) => {
    try {
      const created = await addressService.addAddress(data);
      setAddresses((prev) => [created, ...prev]);
      setSelectedAddressId(created.id);
      setIsAddressModalOpen(false);

      const updated = await checkoutService.previewCheckout({
        addressId: created.id,
        deliverySlot,
      });
      setCheckoutSummary(updated);
      showToast("Address saved and attached to checkout", "success");
    } catch (err: any) {
      showToast(err?.message || "Failed to save address", "error");
    }
  };

  // 4. Handle Delivery Slot Change
  const handleSelectSlot = async (slotTitle: string) => {
    setDeliverySlot(slotTitle);
    try {
      const updated = await checkoutService.previewCheckout({
        addressId: selectedAddressId || undefined,
        deliverySlot: slotTitle,
      });
      setCheckoutSummary(updated);
    } catch (err) {
      console.warn("Could not sync slot change immediately", err);
    }
  };

  // 5. Handle Confirm Checkout (Idempotent handoff to Module 10)
  const handleConfirmCheckout = async () => {
    if (!checkoutSummary) {
      showToast("Checkout session not ready", "error");
      return;
    }

    if (!selectedAddressId && !checkoutSummary.address) {
      showToast("Please select or add a delivery address to proceed", "error");
      setIsSwitchAddressOpen(true);
      return;
    }

    if (confirming) return; // double-click protection

    setConfirming(true);
    try {
      // Generate a unique idempotency key for this confirmation attempt
      const idempotencyKey =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : "idem-" + Date.now() + "-" + Math.random().toString(36).substring(2, 7);

      const result = await checkoutService.confirmCheckout(
        {
          checkoutSessionId: checkoutSummary.id,
          deliverySlot,
          notes: notes.trim() || undefined,
        },
        idempotencyKey
      );

      setConfirmedData(result);

      // Module 10 & 12: Seamlessly convert confirmed checkout session to an Order and initiate Payment
      try {
        const placedOrder = await orderService.createOrder(
          {
            checkoutSessionId: checkoutSummary.id,
            notes: notes.trim() || undefined,
          },
          idempotencyKey
        );
        if (refreshCart) {
          await refreshCart();
        }

        // Module 12: High-security payment initiation
        try {
          const paymentRes = await paymentService.initiatePayment({
            orderId: placedOrder.id,
            paymentMethod: selectedPaymentMethod,
            provider: "mock",
          });

          if (selectedPaymentMethod === "COD") {
            showToast(`Order #${placedOrder.orderNumber} placed with Cash on Delivery!`, "success");
            router.push(`/orders/${placedOrder.orderNumber || placedOrder.id}`);
            return;
          } else {
            showToast("Order placed! Connecting to payment gateway...", "info");
            router.push(`/payment?orderId=${placedOrder.id}&paymentId=${paymentRes.paymentId}`);
            return;
          }
        } catch (payErr: any) {
          console.warn("Payment initiation fallback:", payErr);
          showToast(`Order #${placedOrder.orderNumber} placed! Proceeding to payment...`, "success");
          router.push(`/payment?orderId=${placedOrder.id}`);
          return;
        }
      } catch (orderErr: any) {
        console.warn("Direct order routing fallback:", orderErr);
        showToast("Checkout locked! Click below to view and track your order.", "success");
      }
    } catch (err: any) {
      console.error("Confirmation error:", err);
      showToast(
        err?.message || "Failed to confirm checkout. Please refresh and try again.",
        "error"
      );
    } finally {
      setConfirming(false);
    }
  };

  const handleCopySessionId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedSessionId(true);
    showToast("Session ID copied to clipboard", "info");
    setTimeout(() => setCopiedSessionId(false), 2500);
  };

  const selectedAddress =
    addresses.find((a) => a.id === selectedAddressId) ||
    (checkoutSummary?.address ? (checkoutSummary.address as unknown as Address) : null);

  // Free delivery progress calculation
  const subtotal = checkoutSummary?.subtotal ?? cart.subtotal;
  const freeThreshold = 499;
  const amountNeeded = Math.max(0, freeThreshold - subtotal);
  const freeProgress = Math.min(100, Math.round((subtotal / freeThreshold) * 100));

  // Loading State
  if (authLoading || (loading && !checkoutSummary)) {
    return (
      <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex p-4 rounded-3xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 animate-pulse mb-6">
            <RefreshCw className="w-8 h-8 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Preparing Express Checkout...
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Verifying live catalog prices, inventory availability, and delivery routes.
          </p>
        </div>
      </div>
    );
  }

  // Confirmation Handoff State (READY_FOR_ORDER)
  if (confirmedData) {
    const summary = confirmedData.summary;
    return (
      <div className="min-h-screen bg-slate-50/60 dark:bg-slate-950 py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-xl overflow-hidden p-8 sm:p-10 text-center">
            {/* Animated Checkmark Badge */}
            <div className="w-20 h-20 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-6 ring-8 ring-emerald-50/60 dark:ring-emerald-950/20">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-100/70 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 text-xs font-semibold tracking-wide uppercase mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              Checkout Complete • Ready for Order
            </div>

            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Checkout Confirmed &amp; Locked
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-2 text-sm sm:text-base max-w-lg mx-auto">
              Your cart items, delivery address, and authoritative totals have been verified and reserved.
            </p>

            {/* Session Reference ID */}
            <div className="mt-6 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-2xl p-4 flex items-center justify-between">
              <div className="text-left">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">
                  Checkout Session ID
                </span>
                <span className="text-sm font-mono font-medium text-slate-800 dark:text-slate-200">
                  {confirmedData.checkoutSessionId}
                </span>
              </div>
              <button
                onClick={() => handleCopySessionId(confirmedData.checkoutSessionId)}
                className="p-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition"
                title="Copy Session ID"
              >
                {copiedSessionId ? <Check className="w-5 h-5 text-emerald-600" /> : <Copy className="w-5 h-5" />}
              </button>
            </div>

            {/* Order Readiness Card */}
            <div className="mt-6 text-left border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 rounded-2xl p-5 space-y-3.5">
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                    Deliver To ({summary.address?.label || "Home"})
                  </div>
                  <div className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {summary.address?.recipientName} • {summary.address?.phone}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {summary.address?.addressLine1}, {summary.address?.city}, {summary.address?.postalCode}
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
                <Clock className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                    Selected Delivery Slot
                  </div>
                  <div className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {summary.deliverySlot || "Today • Express 15-Minute Delivery"}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
                <div>
                  <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                    Total Payable
                  </div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(summary.total)}
                  </div>
                </div>
                <div className="text-right text-xs text-slate-500 dark:text-slate-400">
                  {summary.items.length} {summary.items.length === 1 ? "item" : "items"} reserved
                </div>
              </div>
            </div>

            {/* Module 10 Order Active Alert */}
            <div className="mt-6 p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/70 dark:border-emerald-800/60 text-left flex items-start gap-3">
              <PackageCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              <div className="text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed">
                <strong>Module 10 (Orders &amp; Order Management) Active:</strong> Your order is created and locked with immutable purchase snapshots. You can track real-time delivery status, view invoices, or manage your order anytime.
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/orders"
                className="w-full sm:w-auto px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition shadow-sm flex items-center justify-center gap-2"
              >
                <PackageCheck className="w-4 h-4" />
                View &amp; Track My Orders
              </Link>
              <Link
                href="/"
                className="w-full sm:w-auto px-6 py-3 rounded-2xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-sm transition flex items-center justify-center gap-2"
              >
                <ShoppingBag className="w-4 h-4" />
                Continue Shopping
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty Cart State
  if (cart.items.length === 0 && (!checkoutSummary || checkoutSummary.items.length === 0)) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center py-12">
          <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4">
            <ShoppingBag className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Your Cart is Empty
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-2 text-sm">
            Add your daily essentials and fresh groceries to initiate checkout.
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition shadow-sm"
            >
              Explore Products
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/60 dark:bg-slate-950 pb-20 pt-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb & Title */}
        <div className="mb-8">
          <Breadcrumb
            items={[
              { label: "Home", href: "/" },
              { label: "Cart", href: "/cart" },
              { label: "Express Checkout" },
            ]}
          />
          <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                Express Checkout
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                Review your items, choose delivery slot, and verify order totals.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              Authoritative Server Pricing Locked
            </div>
          </div>
        </div>

        {/* Price Change Warning Alert */}
        {checkoutSummary?.priceChanged && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-sm">
              <span className="font-semibold block">Live Price Update Detected</span>
              <p className="text-xs text-amber-800 dark:text-amber-300 mt-0.5">
                {checkoutSummary.warningMessage ||
                  "One or more item prices have updated to current catalog rates."}
              </p>
            </div>
          </div>
        )}

        {/* Main 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Details & Selections */}
          <div className="lg:col-span-8 space-y-6">
            {/* 1. Delivery Address Card */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm">
                    1
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Delivery Address
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  {addresses.length > 0 && (
                    <button
                      onClick={() => setIsSwitchAddressOpen(true)}
                      className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 px-3 py-1.5 rounded-xl hover:bg-emerald-50 dark:hover:bg-emerald-950/30 transition"
                    >
                      Change Address
                    </button>
                  )}
                  <button
                    onClick={() => setIsAddressModalOpen(true)}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    New
                  </button>
                </div>
              </div>

              {selectedAddress ? (
                <div className="p-4 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-300">
                        {selectedAddress.label || selectedAddress.addressType || "Home"}
                      </span>
                      <span className="font-semibold text-slate-900 dark:text-white text-sm">
                        {selectedAddress.fullName || selectedAddress.recipientName}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        • {selectedAddress.mobile || selectedAddress.phone}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                      {selectedAddress.houseFlat || selectedAddress.addressLine1},{" "}
                      {selectedAddress.street || selectedAddress.addressLine2 ? `${selectedAddress.street || selectedAddress.addressLine2}, ` : ""}
                      {selectedAddress.city}, {selectedAddress.state} – {selectedAddress.pincode || selectedAddress.postalCode}
                    </p>
                  </div>
                  <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4" />
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 text-center">
                  <MapPin className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    No delivery address selected
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 mb-3">
                    Add or select an address to enable delivery calculation.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsAddressModalOpen(true)}
                    className="gap-1.5"
                  >
                    <Plus className="w-4 h-4" />
                    Add Delivery Address
                  </Button>
                </div>
              )}
            </div>

            {/* 2. Delivery Slot Selection Card */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Delivery Schedule
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Choose when you want your groceries delivered
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {DELIVERY_SLOTS.map((slot) => {
                  const isSelected = deliverySlot === slot.title;
                  return (
                    <div
                      key={slot.id}
                      onClick={() => handleSelectSlot(slot.title)}
                      className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 ring-1 ring-emerald-600"
                          : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-semibold text-slate-900 dark:text-white">
                          {slot.title}
                        </span>
                        {slot.badge && (
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                            {slot.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {slot.time}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Delivery Instructions */}
              <div className="mt-4">
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                  Delivery Instructions (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Leave with security, ring bell twice..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  maxLength={150}
                  className="w-full px-4 py-2.5 rounded-2xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-slate-900 dark:text-white"
                />
              </div>
            </div>

            {/* 3. Review Order Items Snapshot */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm">
                    3
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                      Order Items Snapshot
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {checkoutSummary?.items.length || cart.items.length} items reserved
                    </p>
                  </div>
                </div>
                <Link
                  href="/cart"
                  className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 flex items-center gap-1"
                >
                  Edit in Cart
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-80 overflow-y-auto pr-1">
                {(checkoutSummary?.items || []).map((item, idx) => (
                  <div key={item.variantId || idx} className="py-3.5 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 overflow-hidden relative shrink-0">
                        {item.thumbnailUrl ? (
                          <Image
                            src={item.thumbnailUrl}
                            alt={item.productTitle}
                            fill
                            className="object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">
                            🛒
                          </div>
                        )}
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-slate-900 dark:text-white line-clamp-1">
                          {item.productTitle}
                        </h4>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-2 mt-0.5">
                          {item.unit && <span>{item.unit}</span>}
                          <span>Qty: {item.quantity}</span>
                          <span>• {formatCurrency(item.unitPrice)} each</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white shrink-0">
                      {formatCurrency(item.lineTotal)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 4. Payment Method Selection (Module 12) */}
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm">
                  4
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                    Payment Method
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Select how you want to pay • 256-bit SSL encrypted
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  {
                    id: "UPI" as PaymentMethod,
                    title: "UPI / QR Code",
                    description: "Google Pay, PhonePe, Paytm, BHIM",
                    icon: QrCode,
                    badge: "Fastest",
                  },
                  {
                    id: "CARD" as PaymentMethod,
                    title: "Credit / Debit Card",
                    description: "Visa, Mastercard, RuPay",
                    icon: CreditCard,
                    badge: null,
                  },
                  {
                    id: "NET_BANKING" as PaymentMethod,
                    title: "Net Banking",
                    description: "SBI, HDFC, ICICI, Axis & more",
                    icon: Building2,
                    badge: null,
                  },
                  {
                    id: "WALLET" as PaymentMethod,
                    title: "Wallets",
                    description: "Amazon Pay, Mobikwik & more",
                    icon: Wallet,
                    badge: null,
                  },
                  {
                    id: "COD" as PaymentMethod,
                    title: "Cash on Delivery",
                    description: "Pay cash at your doorstep",
                    icon: Banknote,
                    badge: "Zero Extra Fee",
                  },
                ].map((pm) => {
                  const Icon = pm.icon;
                  const isSelected = selectedPaymentMethod === pm.id;
                  return (
                    <div
                      key={pm.id}
                      onClick={() => setSelectedPaymentMethod(pm.id)}
                      className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 ring-1 ring-emerald-600"
                          : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <Icon
                            className={`w-4 h-4 ${
                              isSelected
                                ? "text-emerald-600 dark:text-emerald-400"
                                : "text-slate-500"
                            }`}
                          />
                          <span className="text-xs font-bold text-slate-900 dark:text-white">
                            {pm.title}
                          </span>
                        </div>
                        {pm.badge && (
                          <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                            {pm.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        {pm.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Authoritative Pricing Summary (Sticky) */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight mb-4 flex items-center justify-between">
                <span>Payment Summary</span>
                <span className="text-xs font-normal text-slate-400">Authoritative</span>
              </h2>

              {/* Free delivery indicator / progress bar */}
              <div className="mb-5 p-3.5 rounded-2xl bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-100 dark:border-emerald-800/40">
                <div className="flex items-center justify-between text-xs font-semibold text-emerald-800 dark:text-emerald-300 mb-1.5">
                  <span className="flex items-center gap-1.5">
                    <Truck className="w-4 h-4" />
                    {subtotal >= freeThreshold ? "Free Delivery Unlocked!" : `Add ${formatCurrency(amountNeeded)} for Free Delivery`}
                  </span>
                  <span>{freeProgress}%</span>
                </div>
                <div className="w-full h-1.5 bg-emerald-200/60 dark:bg-emerald-900/60 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-600 dark:bg-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${freeProgress}%` }}
                  />
                </div>
              </div>

              {/* Price Breakdown */}
              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-4">
                <div className="flex justify-between">
                  <span>Items Subtotal</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {formatCurrency(checkoutSummary?.subtotal ?? cart.subtotal)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="flex items-center gap-1">
                    Delivery Fee
                    {subtotal >= freeThreshold && (
                      <span className="text-[10px] bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 font-bold px-1.5 py-0.2 rounded">
                        PROMO
                      </span>
                    )}
                  </span>
                  <span className="font-semibold">
                    {(checkoutSummary?.deliveryFee ?? cart.deliveryFee) === 0 ? (
                      <span className="text-emerald-600 dark:text-emerald-400 uppercase font-bold text-xs">
                        FREE
                      </span>
                    ) : (
                      formatCurrency(checkoutSummary?.deliveryFee ?? cart.deliveryFee)
                    )}
                  </span>
                </div>

                {(checkoutSummary?.discount ?? cart.discount) > 0 && (
                  <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-medium">
                    <span>Coupon Discount</span>
                    <span>-{formatCurrency(checkoutSummary?.discount ?? cart.discount)}</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span>Taxes &amp; Platform Fees</span>
                  <span className="text-slate-500">Included</span>
                </div>
              </div>

              {/* Total Payable */}
              <div className="pt-4 mb-6">
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-sm font-bold text-slate-900 dark:text-white block">
                      Total Amount
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Inclusive of all GST &amp; fees
                    </span>
                  </div>
                  <div className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                    {formatCurrency(checkoutSummary?.total ?? cart.total)}
                  </div>
                </div>
              </div>

              {/* 30-Minute Guarantee Badge */}
              <div className="mb-6 p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center gap-2.5 text-xs text-slate-500 dark:text-slate-400">
                <Clock className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Pricing &amp; items locked for 30 minutes</span>
              </div>

              {/* Confirm Checkout Primary Button */}
              <button
                onClick={handleConfirmCheckout}
                disabled={confirming || (!selectedAddressId && !checkoutSummary?.address)}
                className={`w-full py-4 rounded-2xl font-bold text-sm text-white shadow-lg transition-all flex items-center justify-center gap-2 ${
                  confirming || (!selectedAddressId && !checkoutSummary?.address)
                    ? "bg-slate-300 dark:bg-slate-800 cursor-not-allowed text-slate-500"
                    : "bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] shadow-emerald-500/20"
                }`}
              >
                {confirming ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Locking Checkout Session...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    Confirm Checkout • {formatCurrency(checkoutSummary?.total ?? cart.total)}
                  </>
                )}
              </button>

              <p className="text-center text-[11px] text-slate-400 mt-3 flex items-center justify-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Double-click safe with Idempotency Protection
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Switch Address Modal / Drawer */}
      {isSwitchAddressOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Select Delivery Address
              </h3>
              <button
                onClick={() => setIsSwitchAddressOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {addresses.map((addr) => {
                const isSelected = addr.id === selectedAddressId;
                return (
                  <div
                    key={addr.id}
                    onClick={() => handleSelectAddress(addr.id)}
                    className={`p-4 rounded-2xl border cursor-pointer transition ${
                      isSelected
                        ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {addr.label || addr.addressType || "Home"}
                        </span>
                        <span className="text-sm font-semibold text-slate-900 dark:text-white">
                          {addr.fullName || addr.recipientName}
                        </span>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-emerald-600" />}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mt-1">
                      {addr.houseFlat || addr.addressLine1}, {addr.city}, {addr.pincode || addr.postalCode}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <button
                onClick={() => {
                  setIsSwitchAddressOpen(false);
                  setIsAddressModalOpen(true);
                }}
                className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add New Address
              </button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsSwitchAddressOpen(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Address Creation Modal */}
      <AddressModal
        isOpen={isAddressModalOpen}
        onClose={() => setIsAddressModalOpen(false)}
        onSave={handleCreateAddress}
      />
    </div>
  );
}
