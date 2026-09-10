"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Order, OrderStatus } from "@/types";
import { orderService } from "@/services/orderService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { formatCurrency, formatDate } from "@/lib/utils";
import { PackageCheck, ArrowRight, Clock, ChevronRight } from "lucide-react";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await orderService.getOrders();
        setOrders(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const getStatusBadge = (status: OrderStatus) => {
    switch (status) {
      case "delivered":
        return <Badge variant="success">Delivered</Badge>;
      case "out_for_delivery":
        return <Badge variant="accent">⚡ Out for Delivery</Badge>;
      case "preparing":
      case "confirmed":
        return <Badge variant="brand">Processing</Badge>;
      case "cancelled":
        return <Badge variant="danger">Cancelled</Badge>;
      default:
        return <Badge variant="neutral">Order Placed</Badge>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Breadcrumb items={[{ label: "My Orders" }]} />

      <div className="pb-2 border-b border-slate-100">
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          My Order History
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          View, track, and re-order your previous grocery deliveries.
        </p>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading your orders...</div>
      ) : orders.length === 0 ? (
        <EmptyState
          icon={<PackageCheck className="w-10 h-10" />}
          title="No Orders Yet"
          description="You haven't placed any orders yet. Try our lightning fast 15-min delivery now."
          actionText="Start Shopping"
          actionHref="/products"
        />
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="p-5 sm:p-6 rounded-3xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover transition-all space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-slate-900">
                      {order.orderNumber}
                    </span>
                    {getStatusBadge(order.status)}
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Placed on {formatDate(order.createdAt)}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-sm font-black text-slate-900">
                    {formatCurrency(order.total)}
                  </span>
                  <Link href={`/orders/${order.id}`}>
                    <Button
                      variant="outline"
                      size="sm"
                      rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                    >
                      View Details
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Items row */}
              <div className="flex items-center gap-3 overflow-x-auto pb-1">
                {order.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-50 border border-slate-100 shrink-0 max-w-xs"
                  >
                    <div className="relative w-10 h-10 rounded-lg overflow-hidden bg-white shrink-0">
                      <Image
                        src={item.productImage}
                        alt={item.productName}
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div className="min-w-0 pr-2">
                      <p className="text-xs font-bold text-slate-800 truncate">{item.productName}</p>
                      <p className="text-[10px] text-slate-400">Qty: {item.quantity} • {item.unit}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
