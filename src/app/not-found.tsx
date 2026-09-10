"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/common/Button";
import { ShoppingBag, ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-3xl bg-brand-50 text-brand-600 flex items-center justify-center mb-4 shadow-inner">
        <ShoppingBag className="w-8 h-8" />
      </div>
      <span className="text-4xl font-black text-brand-600 mb-1">404</span>
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Page Not Found</h1>
      <p className="text-xs sm:text-sm text-slate-500 max-w-sm mb-6 leading-relaxed">
        The aisle or item you were looking for seems to have been moved or doesn&apos;t exist.
      </p>
      <div className="flex gap-3">
        <Link href="/">
          <Button variant="primary" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Return to Home
          </Button>
        </Link>
        <Link href="/products">
          <Button variant="outline" leftIcon={<Search className="w-4 h-4" />}>
            Browse Catalog
          </Button>
        </Link>
      </div>
    </div>
  );
}
