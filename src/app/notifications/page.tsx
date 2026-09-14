"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  CheckCheck,
  Trash2,
  Package,
  CreditCard,
  ShieldAlert,
  Sparkles,
  ArrowLeft,
  Settings,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { NotificationItem } from "@/types";
import { notificationService } from "@/services/notificationService";
import { cn } from "@/lib/utils";

type FilterTab = "ALL" | "UNREAD" | "ORDERS" | "PAYMENTS" | "SECURITY" | "PROMOTIONS";

export default function NotificationsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Load notifications from API
  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationService.getNotifications({ limit: 50 });
      setNotifications(res.items);
      setUnreadCount(res.unreadCount);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login?redirect=/notifications");
      return;
    }
    if (isAuthenticated) {
      loadNotifications();
    }
  }, [isAuthenticated, authLoading]);

  // Handle Mark Single As Read
  const handleMarkAsRead = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setActionInProgress(id);
    try {
      await notificationService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: "READ" } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
      showToast("Notification marked as read");
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    } finally {
      setActionInProgress(null);
    }
  };

  // Handle Mark All As Read
  const handleMarkAllAsRead = async () => {
    setActionInProgress("all");
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, status: "READ" })));
      setUnreadCount(0);
      showToast("All notifications marked as read");
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    } finally {
      setActionInProgress(null);
    }
  };

  // Handle Delete Notification
  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setActionInProgress(`del-${id}`);
    try {
      await notificationService.deleteNotification(id);
      const deleted = notifications.find((n) => n.id === id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      if (deleted && deleted.status === "UNREAD") {
        setUnreadCount((c) => Math.max(0, c - 1));
      }
      showToast("Notification deleted");
    } catch (err) {
      console.error("Failed to delete notification:", err);
    } finally {
      setActionInProgress(null);
    }
  };

  // Format relative timestamp
  const formatTimeAgo = (dateString: string) => {
    try {
      const now = new Date();
      const date = new Date(dateString);
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (diffInSeconds < 60) return "Just now";
      const diffInMinutes = Math.floor(diffInSeconds / 60);
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      const diffInHours = Math.floor(diffInMinutes / 60);
      if (diffInHours < 24) return `${diffInHours}h ago`;
      const diffInDays = Math.floor(diffInHours / 24);
      if (diffInDays < 7) return `${diffInDays}d ago`;
      return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
    } catch {
      return "Recent";
    }
  };

  // Icon & color styling per notification type
  const getNotificationVisuals = (type: string) => {
    const t = type.toUpperCase();
    if (t.startsWith("ORDER_")) {
      return {
        icon: <Package className="w-5 h-5 text-emerald-600" />,
        bg: "bg-emerald-50 border-emerald-100",
        badge: "Order Update",
        badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      };
    }
    if (t.startsWith("PAYMENT_") || t.startsWith("REFUND_")) {
      return {
        icon: <CreditCard className="w-5 h-5 text-indigo-600" />,
        bg: "bg-indigo-50 border-indigo-100",
        badge: "Payment",
        badgeColor: "bg-indigo-50 text-indigo-700 border-indigo-200",
      };
    }
    if (t.includes("SECURITY") || t.includes("PASSWORD") || t.includes("LOGIN")) {
      return {
        icon: <ShieldAlert className="w-5 h-5 text-amber-600" />,
        bg: "bg-amber-50 border-amber-100",
        badge: "Security",
        badgeColor: "bg-amber-50 text-amber-700 border-amber-200",
      };
    }
    if (t.includes("PROMO") || t.includes("OFFER") || t.includes("DISCOUNT")) {
      return {
        icon: <Sparkles className="w-5 h-5 text-purple-600" />,
        bg: "bg-purple-50 border-purple-100",
        badge: "Offer",
        badgeColor: "bg-purple-50 text-purple-700 border-purple-200",
      };
    }
    return {
      icon: <Bell className="w-5 h-5 text-brand-600" />,
      bg: "bg-brand-50 border-brand-100",
      badge: "General",
      badgeColor: "bg-slate-100 text-slate-700 border-slate-200",
    };
  };

  // Filter items based on active tab
  const filteredNotifications = useMemo(() => {
    return notifications.filter((item) => {
      if (activeTab === "UNREAD") return item.status === "UNREAD";
      if (activeTab === "ORDERS") return item.type.toUpperCase().startsWith("ORDER_");
      if (activeTab === "PAYMENTS") {
        return (
          item.type.toUpperCase().startsWith("PAYMENT_") ||
          item.type.toUpperCase().startsWith("REFUND_")
        );
      }
      if (activeTab === "SECURITY") {
        return (
          item.type.toUpperCase().includes("SECURITY") ||
          item.type.toUpperCase().includes("PASSWORD")
        );
      }
      if (activeTab === "PROMOTIONS") {
        return (
          item.type.toUpperCase().includes("PROMO") ||
          item.type.toUpperCase().includes("OFFER")
        );
      }
      return true;
    });
  }, [notifications, activeTab]);

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      {/* Toast alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-lg text-sm font-medium animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link
                href="/account"
                className="p-2 -ml-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                aria-label="Back to Account"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 flex items-center gap-2.5">
                  <span>Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-2.5 py-0.5 rounded-full bg-brand-500 text-white text-xs font-bold shadow-sm">
                      {unreadCount} new
                    </span>
                  )}
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">
                  Stay updated on your orders, deliveries, and account security
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  disabled={actionInProgress === "all"}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors disabled:opacity-50"
                >
                  {actionInProgress === "all" ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCheck className="w-3.5 h-3.5 text-brand-600" />
                  )}
                  <span className="hidden sm:inline">Mark all read</span>
                </button>
              )}
              <Link
                href="/account/notifications"
                className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-xl transition-colors border border-slate-200"
                title="Notification Preferences"
              >
                <Settings className="w-4 h-4 text-slate-500" />
                <span className="hidden sm:inline">Preferences</span>
              </Link>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1 mt-4 overflow-x-auto pb-1 scrollbar-none">
            {[
              { key: "ALL", label: "All" },
              { key: "UNREAD", label: "Unread", count: unreadCount },
              { key: "ORDERS", label: "Orders" },
              { key: "PAYMENTS", label: "Payments" },
              { key: "SECURITY", label: "Security" },
              { key: "PROMOTIONS", label: "Offers" },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as FilterTab)}
                className={cn(
                  "px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5",
                  activeTab === tab.key
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100"
                )}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span
                    className={cn(
                      "px-1.5 py-0.2 rounded-full text-[10px] font-black",
                      activeTab === tab.key
                        ? "bg-white/20 text-white"
                        : "bg-slate-200 text-slate-700"
                    )}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Notification Stream */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                className="p-4 bg-white rounded-2xl border border-slate-100 animate-pulse flex items-start gap-4"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-100 shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-100 rounded w-1/3" />
                  <div className="h-3 bg-slate-100 rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredNotifications.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16 px-4 bg-white rounded-3xl border border-slate-100 shadow-sm mt-4">
            <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-4">
              <CheckCheck className="w-8 h-8" />
            </div>
            <h3 className="text-base font-bold text-slate-900">You're all caught up!</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              {activeTab === "UNREAD"
                ? "There are no unread notifications right now."
                : "No notifications matching this filter at the moment."}
            </p>
            {activeTab !== "ALL" && (
              <button
                onClick={() => setActiveTab("ALL")}
                className="mt-4 text-xs font-bold text-brand-600 hover:text-brand-700"
              >
                View all notifications →
              </button>
            )}
          </div>
        ) : (
          /* Notification Cards */
          <div className="space-y-3">
            {filteredNotifications.map((item) => {
              const visuals = getNotificationVisuals(item.type);
              const isUnread = item.status === "UNREAD";
              const orderId = item.data?.order_id || item.data?.orderId;

              return (
                <div
                  key={item.id}
                  onClick={() => isUnread && handleMarkAsRead(item.id)}
                  className={cn(
                    "group relative p-4 sm:p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex items-start gap-3.5 sm:gap-4",
                    isUnread
                      ? "bg-white border-brand-100 shadow-sm hover:border-brand-300 ring-1 ring-brand-500/5"
                      : "bg-white/70 border-slate-200/80 hover:bg-white hover:border-slate-300"
                  )}
                >
                  {/* Visual Icon Container */}
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border",
                      visuals.bg
                    )}
                  >
                    {visuals.icon}
                  </div>

                  {/* Body Content */}
                  <div className="flex-1 min-w-0 pr-8 sm:pr-12">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span
                        className={cn(
                          "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border",
                          visuals.badgeColor
                        )}
                      >
                        {visuals.badge}
                      </span>
                      <span className="text-[11px] text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTimeAgo(item.createdAt)}
                      </span>
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-brand-500 ring-2 ring-brand-100 shrink-0" />
                      )}
                    </div>

                    <h4
                      className={cn(
                        "text-sm font-bold leading-tight mb-1",
                        isUnread ? "text-slate-900" : "text-slate-700"
                      )}
                    >
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-600 leading-relaxed break-words">
                      {item.body}
                    </p>

                    {/* Dynamic Action Button (e.g. View Order) */}
                    {orderId && (
                      <div className="mt-3">
                        <Link
                          href={`/orders/${orderId}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition-colors"
                        >
                          <span>View Order</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    )}
                  </div>

                  {/* Floating Action Controls */}
                  <div className="absolute top-4 right-3.5 flex items-center gap-1">
                    {isUnread && (
                      <button
                        onClick={(e) => handleMarkAsRead(item.id, e)}
                        disabled={actionInProgress === item.id}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-slate-100 transition-colors"
                        title="Mark as read"
                      >
                        {actionInProgress === item.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCheck className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      disabled={actionInProgress === `del-${item.id}`}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                      title="Delete notification"
                    >
                      {actionInProgress === `del-${item.id}` ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
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
