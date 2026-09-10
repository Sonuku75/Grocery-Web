"use client";

import React from "react";
import { cn } from "@/lib/utils";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-xl bg-slate-200/70", className)}
      {...props}
    />
  );
}

export function ProductSkeleton() {
  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white p-3.5 shadow-card">
      <Skeleton className="h-44 w-full rounded-xl mb-3" />
      <div className="space-y-2">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-3 w-24" />
        <div className="flex items-center justify-between pt-2">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-8 w-20 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function CategorySkeleton() {
  return (
    <div className="flex flex-col items-center p-3 rounded-2xl border border-slate-100 bg-white">
      <Skeleton className="h-16 w-16 rounded-full mb-2" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}

export function OrderSkeleton() {
  return (
    <div className="p-5 rounded-2xl border border-slate-100 bg-white shadow-card space-y-4">
      <div className="flex justify-between items-center">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>
      <div className="flex gap-4">
        <Skeleton className="h-16 w-16 rounded-xl" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <div className="pt-2 border-t border-slate-100 flex justify-between">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-5 w-20" />
      </div>
    </div>
  );
}
