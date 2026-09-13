"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { Order, OrderStatus } from "@/types";
import { orderService } from "@/services/orderService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  PackageCheck,
  ArrowRight,
  Clock,
  ChevronRight,
  Search,
  Copy,
  Check,
  ShoppingBag,
  Truck,
  AlertCircle,
  XCircle,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

type FilterTab = "ALL" | "ACTIVE" | "DELIVERED" | "CANCELLED";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");
  const [copiedNumber, setCopiedNumber] = useState<string | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const data = await orderService.getOrders({ limit: 50 });
        setOrders(data);
      } catch (err) {
        console.error("Failed to fetch orders:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleCopyOrderNumber = (orderNumber: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(orderNumber);
    setCopiedNumber(orderNumber);
    showToast(`Order #${orderNumber} copied to clipboard`, "info");
    setTimeout(() => setCopiedNumber(null), 2000);
  };

  const getNormalizedStatus = (status: string): string => {
    const s = (status || "").toUpperCase();
    if (s === "ORDER_PLACED") return "PENDING";
    if (s === "PREPARING") return "PROCESSING";
    return s;
  };

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      const normStatus = getNormalizedStatus(order.status);

      // Filter Tab
      if (activeTab === "ACTIVE") {
        if (!["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY"].includes(normStatus)) {
          return false;
        }
      } else if (activeTab === "DELIVERED") {
        if (normStatus !== "DELIVERED") return false;
      } else if (activeTab === "CANCELLED") {
        if (normStatus !== "CANCELLED" && normStatus !== "FAILED") return false;
      }

      // Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesNum = order.orderNumber.toLowerCase().includes(q);
        const matchesItem = order.items.some((it) => it.productName.toLowerCase().includes(q));
        if (!matchesNum && !matchesItem) return false;
      }

      return true;
    });
  }, [orders, activeTab, searchQuery]);

  const renderStatusBadge = (rawStatus: string) => {
    const s = getNormalizedStatus(rawStatus);
    switch (s) {
      case "DELIVERED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Delivered
          </span>
        );
      case "OUT_FOR_DELIVERY":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60 animate-pulse">
            <Truck className="w-3.5 h-3.5" />
            Out for Delivery
          </span>
        );
      case "SHIPPED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-200/60 dark:border-sky-800/60">
            <Truck className="w-3.5 h-3.5" />
            Shipped
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/60">
            <Clock className="w-3.5 h-3.5" />
            Packing &amp; Processing
          </span>
        );
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
            <Check className="w-3.5 h-3.5" />
            Confirmed
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200/60 dark:border-rose-800/60">
            <XCircle className="w-3.5 h-3.5" />
            Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <Clock className="w-3.5 h-3.5" />
            Order Placed
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <Breadcrumb items={[{ label: "My Orders" }]} />

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Order History
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Track real-time delivery status, view purchase snapshots, and download invoices.
            </p>
          </div>
          <Link href="/products">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<ShoppingBag className="w-4 h-4" />}
            >
              Shop More Groceries
            </Button>
          </Link>
        </div>

        {/* Filters & Search Toolbar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 p-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm w-full md:w-auto overflow-x-auto">
            {(
              [
                { id: "ALL", label: "All Orders", count: orders.length },
                {
                  id: "ACTIVE",
                  label: "In Progress",
                  count: orders.filter((o) =>
                    ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY"].includes(
                      getNormalizedStatus(o.status)
                    )
                  ).length,
                },
                {
                  id: "DELIVERED",
                  label: "Delivered",
                  count: orders.filter((o) => getNormalizedStatus(o.status) === "DELIVERED").length,
                },
                {
                  id: "CANCELLED",
                  label: "Cancelled",
                  count: orders.filter((o) =>
                    ["CANCELLED", "FAILED"].includes(getNormalizedStatus(o.status))
                  ).length,
                },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition whitespace-nowrap flex items-center gap-1.5 ${
                  activeTab === tab.id
                    ? "bg-emerald-600 text-white shadow-sm font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    activeTab === tab.id
                      ? "bg-white/20 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Order # or item..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-slate-900 dark:text-white placeholder:text-slate-400 transition"
            />
          </div>
        </div>

        {/* Content Section */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm animate-pulse space-y-4"
              >
                <div className="h-5 bg-slate-100 dark:bg-slate-800 rounded w-1/3" />
                <div className="h-16 bg-slate-50 dark:bg-slate-800/50 rounded-2xl" />
              </div>
            ))}
          </div>
        ) : filteredOrders.length === 0 ? (
          <EmptyState
            icon={<PackageCheck className="w-12 h-12 text-slate-400" />}
            title={searchQuery ? "No matching orders found" : "No orders in this category"}
            description={
              searchQuery
                ? "We couldn't find any orders matching your search query. Check your order number or clear filters."
                : "You haven't placed any orders matching this filter yet. Browse fresh groceries to order now."
            }
            actionText={searchQuery ? "Clear Search" : "Start Shopping"}
            actionHref={searchQuery ? undefined : "/products"}
            onAction={searchQuery ? () => setSearchQuery("") : undefined}
          />
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => {
              const total = order.totalAmount ?? order.total ?? 0;
              const itemCount = order.items.reduce((acc, it) => acc + (it.quantity || 1), 0);

              return (
                <div
                  key={order.id}
                  className="p-5 sm:p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all space-y-4 group"
                >
                  {/* Top Bar: Order ID, Status Badge, Date, Total */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800/80">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-bold text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
                          #{order.orderNumber}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => handleCopyOrderNumber(order.orderNumber, e)}
                          title="Copy order number"
                          className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded transition"
                        >
                          {copiedNumber === order.orderNumber ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        {renderStatusBadge(order.status)}
                      </div>

                      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                        <span>Placed on {formatDate(order.createdAt)}</span>
                        {order.deliverySlot && (
                          <>
                            <span>•</span>
                            <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-medium">
                              <Clock className="w-3 h-3" />
                              {order.deliverySlot}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-4">
                      <div className="text-left sm:text-right">
                        <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
                          Total Amount
                        </div>
                        <div className="text-base font-extrabold text-slate-900 dark:text-white">
                          {formatCurrency(total)}
                        </div>
                      </div>

                      <Link href={`/orders/${order.orderNumber || order.id}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          rightIcon={<ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />}
                        >
                          View Details
                        </Button>
                      </Link>
                    </div>
                  </div>

                  {/* Purchased Items Preview */}
                  <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none">
                    {order.items.slice(0, 4).map((item) => {
                      const imageSrc =
                        item.thumbnailUrl ||
                        item.productImage ||
                        "/images/placeholder.svg";

                      return (
                        <div
                          key={item.id}
                          className="flex items-center gap-3 p-2.5 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 shrink-0 min-w-[220px] max-w-[280px]"
                        >
                          <div className="relative w-12 h-12 rounded-xl overflow-hidden bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shrink-0">
                            <Image
                              src={imageSrc}
                              alt={item.productName}
                              fill
                              className="object-cover"
                            />
                          </div>
                          <div className="min-w-0 pr-1 space-y-0.5">
                            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                              {item.productName}
                            </p>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400">
                              Qty: {item.quantity} {item.variantName ? `• ${item.variantName}` : ""}
                            </p>
                          </div>
                        </div>
                      );
                    })}

                    {order.items.length > 4 && (
                      <Link
                        href={`/orders/${order.orderNumber || order.id}`}
                        className="flex items-center justify-center p-3 rounded-2xl bg-slate-100/70 dark:bg-slate-800/60 border border-dashed border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-emerald-600 shrink-0 transition"
                      >
                        +{order.items.length - 4} more items
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
