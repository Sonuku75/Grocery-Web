"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Category } from "@/types";
import { categoryService } from "@/services/categoryService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { ArrowRight, Sparkles } from "lucide-react";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await categoryService.getCategories();
        setCategories(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb items={[{ label: "Categories" }]} />

      <div>
        <div className="flex items-center gap-2 text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Curated Aisles</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Browse All Categories
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Explore farm-fresh organic produce, pantry staples, morning bakery items, and household goods.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {categories.map((cat) => (
          <Link
            key={cat.id}
            href={`/products?category=${cat.id}`}
            className="group flex flex-col rounded-3xl bg-white border border-slate-100 shadow-card hover:shadow-card-hover overflow-hidden transition-all duration-300"
          >
            <div className="relative aspect-4/3 w-full bg-slate-50 overflow-hidden">
              <Image
                src={cat.imageUrl}
                alt={cat.name}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-300"
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-70 group-hover:opacity-85 transition-opacity" />
              <div className="absolute bottom-3 left-4 right-4 text-white">
                <span className="text-[11px] font-semibold text-brand-200">
                  {cat.itemCount || 30}+ Products
                </span>
                <h3 className="text-lg font-black tracking-tight">{cat.name}</h3>
              </div>
            </div>

            <div className="p-4 flex-1 flex flex-col justify-between">
              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-3">
                {cat.description}
              </p>
              <div className="flex items-center text-xs font-bold text-brand-600 group-hover:text-brand-700">
                <span>Shop Category</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
