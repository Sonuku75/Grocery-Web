"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bell,
  CheckCircle2,
  Lock,
  Mail,
  MessageSquare,
  Smartphone,
  ShieldAlert,
  Loader2,
  Info,
  Package,
  CreditCard,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { NotificationPreferenceItem } from "@/types";
import { notificationService } from "@/services/notificationService";
import { cn } from "@/lib/utils";

interface CategoryMeta {
  key: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const CATEGORIES: CategoryMeta[] = [
  {
    key: "ORDER_UPDATES",
    title: "Orders & Delivery Updates",
    description: "Get real-time tracking, out-for-delivery alerts, and delivery confirmations.",
    icon: <Package className="w-5 h-5 text-emerald-600" />,
  },
  {
    key: "PAYMENT_UPDATES",
    title: "Payments & Refunds",
    description: "Instant receipts, transaction success, payment failures, and refund alerts.",
    icon: <CreditCard className="w-5 h-5 text-indigo-600" />,
  },
  {
    key: "PROMOTIONS",
    title: "Promotions & Discounts",
    description: "Exclusive coupons, festive offers, and personalized grocery recommendations.",
    icon: <Sparkles className="w-5 h-5 text-purple-600" />,
  },
  {
    key: "SECURITY_ALERTS",
    title: "Security & Account Activity",
    description: "Password changes, unrecognized logins, and critical account security notices.",
    icon: <ShieldAlert className="w-5 h-5 text-amber-600" />,
  },
];

const CHANNELS = [
  { key: "IN_APP", label: "In-App", icon: <Bell className="w-4 h-4" /> },
  { key: "EMAIL", label: "Email", icon: <Mail className="w-4 h-4" /> },
  { key: "SMS", label: "SMS", icon: <MessageSquare className="w-4 h-4" /> },
  { key: "PUSH", label: "Push", icon: <Smartphone className="w-4 h-4" /> },
];

export default function NotificationPreferencesPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [preferences, setPreferences] = useState<NotificationPreferenceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingKey, setUpdatingKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadPreferences = async () => {
    setLoading(true);
    try {
      const prefs = await notificationService.getPreferences();
      setPreferences(prefs);
    } catch (err) {
      console.error("Failed to load preferences:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login?redirect=/account/notifications");
      return;
    }
    if (isAuthenticated) {
      loadPreferences();
    }
  }, [isAuthenticated, authLoading]);

  // Find preference state
  const isEnabled = (category: string, channel: string): boolean => {
    const pref = preferences.find(
      (p) => p.category.toUpperCase() === category.toUpperCase() && p.channel.toUpperCase() === channel.toUpperCase()
    );
    // Security alerts are always enabled
    if (category === "SECURITY_ALERTS") return true;
    return pref ? (pref.isEnabled ?? pref.is_enabled ?? true) : true;
  };

  // Toggle preference handler
  const handleToggle = async (category: string, channel: string) => {
    if (category === "SECURITY_ALERTS") {
      showToast("Security alerts are mandatory and cannot be disabled");
      return;
    }

    const currentVal = isEnabled(category, channel);
    const targetVal = !currentVal;
    const key = `${category}:${channel}`;
    setUpdatingKey(key);

    // Optimistic state update
    setPreferences((prev) => {
      const existing = prev.find(
        (p) => p.category.toUpperCase() === category.toUpperCase() && p.channel.toUpperCase() === channel.toUpperCase()
      );
      if (existing) {
        return prev.map((p) =>
          p.category.toUpperCase() === category.toUpperCase() && p.channel.toUpperCase() === channel.toUpperCase()
            ? { ...p, isEnabled: targetVal, is_enabled: targetVal }
            : p
        );
      }
      return [
        ...prev,
        {
          category,
          channel,
          isEnabled: targetVal,
          is_enabled: targetVal,
          isMandatory: false,
          is_mandatory: false,
        },
      ];
    });

    try {
      await notificationService.updatePreference({
        category,
        channel,
        isEnabled: targetVal,
      });
      showToast(`${channel} alerts ${targetVal ? "enabled" : "disabled"}`);
    } catch (err) {
      console.error("Failed to update preference:", err);
      // Revert on failure
      setPreferences((prev) =>
        prev.map((p) =>
          p.category.toUpperCase() === category.toUpperCase() && p.channel.toUpperCase() === channel.toUpperCase()
            ? { ...p, isEnabled: currentVal, is_enabled: currentVal }
            : p
        )
      );
      showToast("Failed to update preference. Please try again.");
    } finally {
      setUpdatingKey(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-lg text-sm font-medium animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-5">
          <div className="flex items-center gap-3">
            <Link
              href="/notifications"
              className="p-2 -ml-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              aria-label="Back to Notifications"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-slate-900">
                Notification Preferences
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Customize how you receive updates across In-App, Email, SMS, and Push
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Preferences Container */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                className="p-6 bg-white rounded-2xl border border-slate-100 animate-pulse space-y-4"
              >
                <div className="h-5 bg-slate-100 rounded w-1/4" />
                <div className="h-3 bg-slate-100 rounded w-1/2" />
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  {[1, 2, 3, 4].map((c) => (
                    <div key={c} className="h-10 bg-slate-100 rounded-xl" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {CATEGORIES.map((cat) => {
              const isMandatoryCategory = cat.key === "SECURITY_ALERTS";

              return (
                <div
                  key={cat.key}
                  className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm hover:border-slate-300 transition-all"
                >
                  {/* Category Info Header */}
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0">
                        {cat.icon}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-sm sm:text-base font-bold text-slate-900">
                            {cat.title}
                          </h3>
                          {isMandatoryCategory && (
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                              <Lock className="w-2.5 h-2.5" /> Mandatory
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-1 max-w-xl leading-relaxed">
                          {cat.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Multi-Channel Toggle Matrix */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100">
                    {CHANNELS.map((ch) => {
                      const enabled = isEnabled(cat.key, ch.key);
                      const key = `${cat.key}:${ch.key}`;
                      const isUpdating = updatingKey === key;

                      return (
                        <div
                          key={ch.key}
                          onClick={() => !isMandatoryCategory && handleToggle(cat.key, ch.key)}
                          className={cn(
                            "p-3 rounded-xl border transition-all flex items-center justify-between gap-2 select-none",
                            isMandatoryCategory
                              ? "bg-slate-50 border-slate-200 text-slate-500 cursor-not-allowed"
                              : enabled
                              ? "bg-brand-50/40 border-brand-200 text-slate-900 cursor-pointer hover:bg-brand-50"
                              : "bg-white border-slate-200 text-slate-600 cursor-pointer hover:border-slate-300"
                          )}
                        >
                          <div className="flex items-center gap-2 text-xs font-semibold">
                            <span className={enabled ? "text-brand-600" : "text-slate-400"}>
                              {ch.icon}
                            </span>
                            <span>{ch.label}</span>
                          </div>

                          {/* Switch Indicator */}
                          {isMandatoryCategory ? (
                            <div className="w-7 h-4 rounded-full bg-slate-300 flex items-center px-0.5">
                              <div className="w-3 h-3 rounded-full bg-white shadow-sm ml-auto flex items-center justify-center">
                                <Lock className="w-2 h-2 text-slate-400" />
                              </div>
                            </div>
                          ) : isUpdating ? (
                            <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                          ) : (
                            <div
                              className={cn(
                                "w-8 h-4.5 rounded-full transition-colors relative flex items-center px-0.5",
                                enabled ? "bg-brand-600" : "bg-slate-300"
                              )}
                            >
                              <div
                                className={cn(
                                  "w-3.5 h-3.5 rounded-full bg-white shadow-sm transition-transform",
                                  enabled ? "translate-x-3.5" : "translate-x-0"
                                )}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Security Alert Guarantee Box */}
        <div className="mt-8 p-4 rounded-2xl bg-amber-50/70 border border-amber-200/80 flex items-start gap-3 text-xs text-amber-800">
          <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong>Security Protection:</strong> Critical notifications such as password resets,
            security alerts, and unauthorized login detections are delivered on all verified channels
            unconditionally to safeguard your Cartify account.
          </p>
        </div>
      </div>
    </div>
  );
}
