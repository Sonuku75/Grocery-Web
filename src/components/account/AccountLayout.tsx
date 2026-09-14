"use client";

import React, { useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { AccountNav } from "./AccountNav";
import { notificationService } from "@/services/notificationService";
import { wishlistService } from "@/services/wishlistService";
import { ShieldCheck, User as UserIcon, Loader2 } from "lucide-react";

interface AccountLayoutProps {
  title: string;
  description?: string;
  breadcrumbItems?: { label: string; href?: string }[];
  children: ReactNode;
  rightAction?: ReactNode;
}

export function AccountLayout({
  title,
  description,
  breadcrumbItems = [],
  children,
  rightAction,
}: AccountLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading: authLoading, isAuthenticated } = useAuth();

  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [wishlistCount, setWishlistCount] = useState(0);

  // Authentication guard
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [authLoading, isAuthenticated, router, pathname]);

  // Load badge counts
  useEffect(() => {
    if (isAuthenticated) {
      notificationService
        .getUnreadCount()
        .then((count) => setUnreadNotifications(count))
        .catch(() => {});

      wishlistService
        .getWishlist(undefined, 1)
        .then((res) => setWishlistCount(res.count))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  if (authLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading your account...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  const defaultBreadcrumbs = [
    { label: "Account", href: "/account" },
    ...breadcrumbItems,
  ];

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Breadcrumb items={defaultBreadcrumbs} />
        </div>

        {/* Page Header Banner */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200/60">
                  Customer Account
                </span>
                {user?.isVerified && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Verified
                  </span>
                )}
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                {title}
              </h1>
              {description && (
                <p className="text-sm text-slate-500 max-w-2xl">{description}</p>
              )}
            </div>

            {rightAction && <div className="shrink-0">{rightAction}</div>}
          </div>
        </div>

        {/* Main Grid: Sidebar + Content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Navigation Sidebar / Mobile Tabs */}
          <aside className="lg:col-span-3 lg:sticky lg:top-24">
            <AccountNav
              unreadNotificationCount={unreadNotifications}
              wishlistCount={wishlistCount}
            />
          </aside>

          {/* Page Content */}
          <main className="lg:col-span-9 space-y-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
