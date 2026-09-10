"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Compass, Search, ShoppingBag, User, PackageCheck } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { cn } from "@/lib/utils";

export function MobileBottomNav() {
  const pathname = usePathname();
  const { cart } = useCart();

  const NAV_ITEMS = [
    { label: "Home", href: "/", icon: Home },
    { label: "Categories", href: "/categories", icon: Compass },
    { label: "Search", href: "/search", icon: Search },
    { label: "Orders", href: "/orders", icon: PackageCheck },
    {
      label: "Cart",
      href: "/cart",
      icon: ShoppingBag,
      badge: cart.itemCount > 0 ? cart.itemCount : undefined,
    },
    { label: "Profile", href: "/profile", icon: User },
  ];

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200/80 px-2 py-1.5 shadow-lg">
      <nav aria-label="Mobile Navigation" className="flex items-center justify-around">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition-all",
                isActive
                  ? "text-brand-600 font-bold"
                  : "text-slate-500 hover:text-slate-900 font-medium"
              )}
            >
              <div className="relative">
                <Icon className={cn("w-5 h-5", isActive && "stroke-[2.5px]")} />
                {item.badge !== undefined && (
                  <span className="absolute -top-1.5 -right-2.5 min-w-4 h-4 px-1 rounded-full bg-accent-500 text-white text-[9px] font-bold flex items-center justify-center">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] mt-1">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
