"use client";

import React, { ReactNode } from "react";
import Link from "next/link";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionText,
  actionHref,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-3xl bg-white border border-slate-100 shadow-card max-w-lg mx-auto",
        className
      )}
    >
      <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-4 shadow-inner">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 max-w-xs mb-6 leading-relaxed">{description}</p>
      {actionText && actionHref && (
        <Link href={actionHref}>
          <Button variant="primary">{actionText}</Button>
        </Link>
      )}
      {actionText && !actionHref && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
}
