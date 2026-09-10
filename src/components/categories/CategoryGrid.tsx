"use client";

import React from "react";
import { Category } from "@/types";
import { CategoryCard } from "./CategoryCard";
import { CategorySkeleton } from "@/components/common/Skeleton";

interface CategoryGridProps {
  categories: Category[];
  isLoading?: boolean;
}

export function CategoryGrid({ categories, isLoading = false }: CategoryGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 sm:gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <CategorySkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 sm:gap-4">
      {categories.map((category) => (
        <CategoryCard key={category.id} category={category} />
      ))}
    </div>
  );
}
