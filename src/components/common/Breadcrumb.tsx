"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center text-xs font-medium text-slate-500 py-2.5">
      <ol className="flex items-center gap-1.5 flex-wrap">
        <li className="inline-flex items-center">
          <Link
            href="/"
            className="flex items-center gap-1 text-slate-500 hover:text-brand-600 transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Home</span>
          </Link>
        </li>

        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="inline-flex items-center gap-1.5">
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              {isLast || !item.href ? (
                <span className="text-slate-800 font-semibold truncate max-w-xs">
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-slate-500 hover:text-brand-600 transition-colors truncate max-w-xs"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
