"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Category } from "@/types";

interface CategoryCardProps {
  category: Category;
}

export function CategoryCard({ category }: CategoryCardProps) {
  return (
    <Link
      href={`/categories/${category.slug || category.id}`}
      className="group flex flex-col items-center p-3 rounded-2xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover hover:border-brand-200 transition-all duration-200 text-center"
    >
      <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-2xl overflow-hidden bg-brand-50/50 mb-3 group-hover:scale-105 transition-transform duration-300">
        <Image
          src={category.imageUrl || "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&auto=format&fit=crop&q=80"}
          alt={category.name}
          fill
          className="object-cover"
          sizes="96px"
        />
      </div>
      <h3 className="text-xs sm:text-sm font-bold text-slate-800 group-hover:text-brand-600 transition-colors line-clamp-1">
        {category.name}
      </h3>
      {category.itemCount && (
        <span className="text-[11px] text-slate-400 font-medium mt-0.5">
          {category.itemCount}+ items
        </span>
      )}
    </Link>
  );
}
