"use client";

import React from "react";
import { Product } from "@/types";
import { ProductCard } from "./ProductCard";
import { ProductSkeleton } from "@/components/common/Skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { ShoppingBag } from "lucide-react";

interface ProductGridProps {
  products: Product[];
  isLoading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
}

export function ProductGrid({
  products,
  isLoading = false,
  emptyTitle = "No products found",
  emptyDescription = "Try adjusting your filters, price range, or search keywords to find what you need.",
}: ProductGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-5">
        {Array.from({ length: 8 }).map((_, i) => (
          <ProductSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <EmptyState
        icon={<ShoppingBag className="w-8 h-8" />}
        title={emptyTitle}
        description={emptyDescription}
        actionText="Browse All Products"
        actionHref="/products"
      />
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-5">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
