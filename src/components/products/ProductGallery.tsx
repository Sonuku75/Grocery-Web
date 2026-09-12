"use client";

import React, { useState, useRef } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface ProductGalleryProps {
  images: string[];
  productName: string;
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const displayImages = images && images.length > 0
    ? images
    : ["https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800"];

  const [selectedImage, setSelectedImage] = useState(0);
  const mobileScrollRef = useRef<HTMLDivElement>(null);

  const handlePrev = (e: React.MouseEvent) => {
    e.preventDefault();
    setSelectedImage((prev) => (prev > 0 ? prev - 1 : displayImages.length - 1));
  };

  const handleNext = (e: React.MouseEvent) => {
    e.preventDefault();
    setSelectedImage((prev) => (prev < displayImages.length - 1 ? prev + 1 : 0));
  };

  return (
    <div className="flex flex-col-reverse md:flex-row gap-3 sm:gap-4 select-none">
      {/* Desktop Vertical Thumbnails */}
      {displayImages.length > 1 && (
        <div className="hidden md:flex md:flex-col gap-2.5 overflow-y-auto max-h-[500px] pr-1 scrollbar-thin">
          {displayImages.map((img, idx) => {
            const isCurrent = selectedImage === idx;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedImage(idx)}
                aria-label={`View photo ${idx + 1}`}
                className={`relative w-18 h-18 lg:w-20 lg:h-20 rounded-2xl overflow-hidden border-2 transition-all duration-200 shrink-0 focus:outline-none focus:ring-2 focus:ring-brand-500/20 active:scale-95 ${
                  isCurrent
                    ? "border-brand-600 ring-2 ring-brand-100 shadow-xs"
                    : "border-slate-100 hover:border-slate-300 opacity-75 hover:opacity-100"
                }`}
              >
                <Image
                  src={img}
                  alt={`${productName} view ${idx + 1}`}
                  fill
                  className="object-cover"
                  sizes="80px"
                />
              </button>
            );
          })}
        </div>
      )}

      {/* Main Display Image Frame */}
      <div className="flex-1 relative aspect-square sm:aspect-4/3 md:aspect-square max-h-[500px] rounded-3xl overflow-hidden bg-slate-50 border border-slate-100 shadow-card group">
        <Image
          src={displayImages[selectedImage] || displayImages[0]}
          alt={`${productName} - primary view`}
          fill
          className="object-cover object-center transition-transform duration-500 md:group-hover:scale-105 motion-reduce:transition-none motion-reduce:hover:scale-100"
          priority
          sizes="(max-width: 768px) 100vw, 50vw"
        />

        {/* Carousel Navigation Arrows */}
        {displayImages.length > 1 && (
          <div className="absolute inset-x-2.5 top-1/2 -translate-y-1/2 flex items-center justify-between pointer-events-none">
            <button
              type="button"
              onClick={handlePrev}
              aria-label="Previous product image"
              className="pointer-events-auto w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-white/90 backdrop-blur-xs shadow-md border border-slate-100 flex items-center justify-center text-slate-700 hover:text-brand-600 hover:bg-white active:scale-95 transition-all opacity-80 hover:opacity-100"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={handleNext}
              aria-label="Next product image"
              className="pointer-events-auto w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-white/90 backdrop-blur-xs shadow-md border border-slate-100 flex items-center justify-center text-slate-700 hover:text-brand-600 hover:bg-white active:scale-95 transition-all opacity-80 hover:opacity-100"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Mobile / Tablet Pagination Dots */}
        {displayImages.length > 1 && (
          <div className="absolute bottom-3 inset-x-0 flex items-center justify-center gap-1.5 z-10 md:hidden pointer-events-none">
            {displayImages.map((_, idx) => (
              <span
                key={idx}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  selectedImage === idx
                    ? "w-5 bg-brand-600 shadow-xs"
                    : "w-1.5 bg-slate-300/80"
                }`}
              />
            ))}
          </div>
        )}
      </div>

      {/* Mobile Horizontal Thumbnail Bar */}
      {displayImages.length > 1 && (
        <div
          ref={mobileScrollRef}
          className="flex md:hidden gap-2 overflow-x-auto pb-1 scrollbar-none snap-x"
        >
          {displayImages.map((img, idx) => {
            const isCurrent = selectedImage === idx;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedImage(idx)}
                aria-label={`View photo ${idx + 1}`}
                className={`relative w-14 h-14 rounded-xl overflow-hidden border-2 shrink-0 snap-center transition-all ${
                  isCurrent
                    ? "border-brand-600 ring-2 ring-brand-100 shadow-xs"
                    : "border-slate-100 opacity-70"
                }`}
              >
                <Image
                  src={img}
                  alt={`${productName} thumbnail ${idx + 1}`}
                  fill
                  className="object-cover"
                  sizes="56px"
                />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
