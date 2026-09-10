"use client";

import React, { useState } from "react";
import Image from "next/image";

interface ProductGalleryProps {
  images: string[];
  productName: string;
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const [selectedImage, setSelectedImage] = useState(0);

  return (
    <div className="flex flex-col-reverse md:flex-row gap-4">
      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex md:flex-col gap-2.5 overflow-x-auto md:overflow-y-auto max-h-[460px] pb-1">
          {images.map((img, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedImage(idx)}
              className={`relative w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden border-2 transition-all shrink-0 ${
                selectedImage === idx
                  ? "border-brand-600 ring-2 ring-brand-100"
                  : "border-slate-200 hover:border-slate-300"
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
          ))}
        </div>
      )}

      {/* Main Large Display Image */}
      <div className="flex-1 relative aspect-square sm:aspect-4/3 md:aspect-square max-h-[480px] rounded-3xl overflow-hidden bg-slate-50 border border-slate-100 shadow-card">
        <Image
          src={images[selectedImage] || images[0]}
          alt={productName}
          fill
          className="object-cover object-center transition-all duration-300"
          priority
          sizes="(max-width: 768px) 100vw, 50vw"
        />
      </div>
    </div>
  );
}
