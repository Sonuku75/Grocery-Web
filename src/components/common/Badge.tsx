"use client";

import React, { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center font-semibold rounded-full tracking-wide transition-colors",
  {
    variants: {
      variant: {
        brand: "bg-brand-50 text-brand-700 border border-brand-200/80",
        accent: "bg-accent-50 text-accent-700 border border-accent-200/80",
        discount: "bg-rose-500 text-white shadow-xs font-bold",
        success: "bg-emerald-50 text-emerald-700 border border-emerald-200",
        warning: "bg-amber-50 text-amber-700 border border-amber-200",
        danger: "bg-rose-50 text-rose-700 border border-rose-200",
        neutral: "bg-slate-100 text-slate-700 border border-slate-200",
      },
      size: {
        sm: "text-[10px] px-2 py-0.5",
        md: "text-xs px-2.5 py-1",
        lg: "text-sm px-3 py-1.5",
      },
    },
    defaultVariants: {
      variant: "brand",
      size: "md",
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  children: ReactNode;
}

export function Badge({ className, variant, size, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size, className }))} {...props}>
      {children}
    </span>
  );
}
