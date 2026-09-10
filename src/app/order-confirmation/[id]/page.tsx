"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { Order } from "@/types";
import { orderService } from "@/services/orderService";
import { Button } from "@/components/common/Button";
import { formatCurrency } from "@/lib/utils";
import { CheckCircle2, Clock, MapPin, PackageCheck, ShoppingBag, ArrowRight } from "lucide-react";

interface ConfirmationPageProps {
  params: Promise<{ id: string }>;
}

export default function OrderConfirmationPage({ params }: ConfirmationPageProps) {
  const { id } = use(params);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center">
        <div className="inline-block w-8 h-8 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-semibold text-slate-500">Confirming order details...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white rounded-3xl border border-slate-100 p-8 sm:p-10 shadow-xl text-center space-y-6 animate-scale-in">
        <div className="w-16 h-16 rounded-3xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-md">
          <CheckCircle2 className="w-9 h-9" />
        </div>

        <div>
          <span className="text-xs font-black uppercase tracking-wider text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full">
            Order Confirmed & Picked
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-2">
            Thank You For Ordering!
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-md mx-auto">
            Your fresh grocery order has been queued at the Cartify local hub and will arrive in 15 minutes.
          </p>
        </div>

        {order && (
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100 text-left space-y-4 max-w-lg mx-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 text-xs">
              <span className="text-slate-500">Order Number:</span>
              <strong className="font-mono text-slate-900">{order.orderNumber}</strong>
            </div>

            <div className="flex items-start gap-3 text-xs text-slate-600">
              <Clock className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-800">Estimated Delivery:</span>
                <p className="text-slate-500">{order.deliverySlot || "15-Minute Express Delivery"}</p>
              </div>
            </div>

            <div className="flex items-start gap-3 text-xs text-slate-600">
              <MapPin className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-800">Delivering to:</span>
                <p className="text-slate-500">
                  {order.address.houseFlat}, {order.address.street}, {order.address.city}
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-sm font-bold text-slate-900">
              <span>Total Paid ({order.paymentMethod.toUpperCase()}):</span>
              <span className="text-brand-700">{formatCurrency(order.total)}</span>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
          <Link href={`/orders/${id}`} className="w-full sm:w-auto">
            <Button
              variant="primary"
              size="md"
              leftIcon={<PackageCheck className="w-4 h-4" />}
            >
              Track Live Order Status
            </Button>
          </Link>
          <Link href="/products" className="w-full sm:w-auto">
            <Button
              variant="outline"
              size="md"
              leftIcon={<ShoppingBag className="w-4 h-4" />}
            >
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
