"use client";

import React, { useEffect, useState, use } from "react";
import Image from "next/image";
import Link from "next/link";
import { Order, OrderStatus } from "@/types";
import { orderService } from "@/services/orderService";
import { useCart } from "@/context/CartContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Badge } from "@/components/common/Badge";
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
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

interface OrderPageProps {
  params: Promise<{ id: string }>;
}

export default function OrderDetailsPage({ params }: OrderPageProps) {
  const { id } = use(params);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();
  const { addToCart, setIsCartDrawerOpen } = useCart();

  useEffect(() => {
    async function load() {
      try {
        const ord = await orderService.getOrderById(id);
        setOrder(ord);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleCancelOrder = async () => {
    if (!order) return;
    const cancelled = await orderService.cancelOrder(order.id);
    if (cancelled) {
      setOrder(cancelled);
      showToast("Order cancelled successfully.", "info");
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center text-xs text-slate-400">
        Loading order details...
      </div>
    );
  }

  if (!order) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center">
        <h2 className="text-xl font-bold text-slate-800">Order not found</h2>
        <Link href="/orders" className="mt-4 inline-block">
          <Button variant="primary" size="sm">Back to Orders</Button>
        </Link>
      </div>
    );
  }

  const TRACKING_STEPS: { status: OrderStatus; label: string; desc: string }[] = [
    { status: "order_placed", label: "Order Placed", desc: "Received at Cartify Hub" },
    { status: "confirmed", label: "Payment Confirmed", desc: "Verified inventory" },
    { status: "preparing", label: "Packing Fresh Produce", desc: "Thermal sealed" },
    { status: "out_for_delivery", label: "Out for Delivery", desc: "On electric bike" },
    { status: "delivered", label: "Delivered", desc: "Handed over safely" },
  ];

  const statusOrderIndex: Record<OrderStatus, number> = {
    order_placed: 0,
    confirmed: 1,
    preparing: 2,
    shipped: 3,
    out_for_delivery: 3,
    delivered: 4,
    cancelled: -1,
  };

  const currentIndex = statusOrderIndex[order.status];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb
        items={[
          { label: "My Orders", href: "/orders" },
          { label: order.orderNumber },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-900">
              Order {order.orderNumber}
            </h1>
            <Badge variant={order.status === "delivered" ? "success" : "brand"}>
              {order.status.replace(/_/g, " ").toUpperCase()}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Placed on {formatDate(order.createdAt)} • Payment: {order.paymentMethod.toUpperCase()} ({order.paymentStatus})
          </p>
        </div>

        {order.status !== "delivered" && order.status !== "cancelled" && (
          <Button
            variant="outline"
            size="sm"
            className="text-rose-600 hover:bg-rose-50 hover:border-rose-300"
            onClick={handleCancelOrder}
          >
            Cancel Order
          </Button>
        )}
      </div>

      {/* Tracking Stepper */}
      {order.status !== "cancelled" ? (
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-100 shadow-card">
          <h3 className="text-sm font-bold text-slate-900 mb-6 flex items-center gap-2">
            <Clock className="w-4 h-4 text-brand-600" />
            <span>Delivery Tracking Progress</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {TRACKING_STEPS.map((step, idx) => {
              const isCompleted = currentIndex >= idx;
              const isCurrent = currentIndex === idx;

              return (
                <div key={step.status} className="flex md:flex-col items-center md:text-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-bold text-xs transition-colors ${
                      isCompleted
                        ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                        : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
                  </div>
                  <div>
                    <h4
                      className={`text-xs font-bold ${
                        isCurrent ? "text-brand-600" : isCompleted ? "text-slate-900" : "text-slate-400"
                      }`}
                    >
                      {step.label}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">{step.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-3">
          <XCircle className="w-5 h-5" />
          <span>This order was cancelled. Any authorized charges have been automatically refunded.</span>
        </div>
      )}

      {/* Order Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Items list */}
        <div className="lg:col-span-8 p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-4">
          <h3 className="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">
            Items in This Delivery ({order.items.length})
          </h3>

          <div className="divide-y divide-slate-100">
            {order.items.map((item) => (
              <div key={item.id} className="py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="relative w-14 h-14 rounded-xl overflow-hidden bg-slate-50 border border-slate-100 shrink-0">
                    <Image
                      src={item.productImage}
                      alt={item.productName}
                      fill
                      className="object-cover"
                    />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{item.productName}</h4>
                    <p className="text-[11px] text-slate-400">
                      {item.unit} • {formatCurrency(item.unitPrice)} × {item.quantity}
                    </p>
                  </div>
                </div>
                <span className="text-xs font-black text-slate-900">
                  {formatCurrency(item.totalPrice)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Address & Payment breakdown */}
        <div className="lg:col-span-4 space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-4">
            <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
              Delivery Destination
            </h3>
            <div className="text-xs text-slate-600 space-y-1">
              <p className="font-bold text-slate-900">{order.address.fullName}</p>
              <p>{order.address.houseFlat}, {order.address.street}</p>
              <p>{order.address.area}, {order.address.city} {order.address.pincode}</p>
              <p className="text-slate-400 font-mono mt-1">{order.address.mobile}</p>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-3">
            <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
              Payment Summary
            </h3>
            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span className="font-bold text-slate-900">{formatCurrency(order.subtotal)}</span>
              </div>
              {order.discount > 0 && (
                <div className="flex justify-between text-brand-600 font-bold">
                  <span>Discount</span>
                  <span>-{formatCurrency(order.discount)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span>Delivery</span>
                <span>{order.deliveryFee === 0 ? <strong className="text-brand-600">FREE</strong> : formatCurrency(order.deliveryFee)}</span>
              </div>
              <div className="flex justify-between">
                <span>Taxes</span>
                <span>{formatCurrency(order.tax)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-slate-200 text-sm font-black text-slate-900">
                <span>Total</span>
                <span>{formatCurrency(order.total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
