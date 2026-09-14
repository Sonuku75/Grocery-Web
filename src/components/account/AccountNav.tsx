"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  User,
  PackageCheck,
  MapPin,
  Heart,
  Bell,
  ShieldCheck,
  Smartphone,
  LayoutDashboard,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number | string;
}

interface AccountNavProps {
  unreadNotificationCount?: number;
  wishlistCount?: number;
  className?: string;
}

export function AccountNav({
  unreadNotificationCount = 0,
  wishlistCount = 0,
  className,
}: AccountNavProps) {
  const pathname = usePathname();
  const { logout } = useAuth();

  const navItems: NavItem[] = [
    {
      label: "Account Overview",
      href: "/account",
      icon: LayoutDashboard,
    },
    {
      label: "My Profile",
      href: "/profile",
      icon: User,
    },
    {
      label: "My Orders",
      href: "/orders",
      icon: PackageCheck,
    },
    {
      label: "Saved Addresses",
      href: "/addresses",
      icon: MapPin,
    },
    {
      label: "Wishlist",
      href: "/wishlist",
      icon: Heart,
      badge: wishlistCount > 0 ? wishlistCount : undefined,
    },
    {
      label: "Notifications",
      href: "/account/notifications",
      icon: Bell,
      badge: unreadNotificationCount > 0 ? unreadNotificationCount : undefined,
    },
    {
      label: "Security Settings",
      href: "/account/security",
      icon: ShieldCheck,
    },
    {
      label: "Active Sessions",
      href: "/account/sessions",
      icon: Smartphone,
    },
  ];

  return (
    <nav
      aria-label="Account navigation"
      className={cn("w-full", className)}
    >
      {/* Mobile Horizontal Tabs */}
      <div className="lg:hidden w-full overflow-x-auto scrollbar-none pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        <div className="flex items-center gap-2 min-w-max">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-150 active:scale-95",
                  isActive
                    ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <Icon className={cn("w-4 h-4", isActive ? "text-white" : "text-slate-500")} />
                <span>{item.label}</span>
                {item.badge !== undefined && (
                  <span
                    className={cn(
                      "px-1.5 py-0.5 rounded-full text-[10px] font-bold leading-none",
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-brand-100 text-brand-700"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Desktop Vertical Sidebar */}
      <div className="hidden lg:flex flex-col bg-white rounded-3xl border border-slate-100 p-3 shadow-xs space-y-1">
        <div className="px-3.5 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Account Menu
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-700 font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-brand-600" : "text-slate-400"
                  )}
                />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-xs font-bold leading-none",
                    isActive
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-700"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <div className="pt-3 mt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={() => logout()}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-rose-600 hover:bg-rose-50 transition-colors"
          >
            <LogOut className="w-4 h-4 text-rose-500" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
