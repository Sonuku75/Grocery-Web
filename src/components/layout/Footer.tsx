"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ShoppingBag, Mail, Phone, Clock, ShieldCheck, HeartHandshake, CheckCircle2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export function Footer() {
  const [email, setEmail] = useState("");
  const { showToast } = useToast();

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      showToast("Thank you for subscribing to Cartify Fresh Drops!", "success");
      setEmail("");
    }
  };

  return (
    <footer className="bg-slate-900 text-slate-300 pt-16 pb-24 md:pb-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Value props banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-slate-800">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-900/60 text-brand-400 flex items-center justify-center shrink-0 border border-brand-800">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base">15-Minute Express Delivery</h4>
              <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                Hyper-local micro fulfillment centers keep your groceries crisp, fresh, and at your door in minutes.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-900/60 text-brand-400 flex items-center justify-center shrink-0 border border-brand-800">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base">100% Quality Guaranteed</h4>
              <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                Handpicked farm-fresh produce and certified organic essentials. No questions asked return or replacement.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-900/60 text-brand-400 flex items-center justify-center shrink-0 border border-brand-800">
              <HeartHandshake className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base">Direct From Ethical Farmers</h4>
              <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                We partner directly with sustainable growers, paying fair wages and delivering uncompromised nutrition.
              </p>
            </div>
          </div>
        </div>

        {/* Navigation columns */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 py-12">
          {/* Col 1: Brand story */}
          <div className="col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center text-white font-black shadow-md">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <span className="text-2xl font-black tracking-tight text-white">
                Cart<span className="text-brand-400">ify</span>
              </span>
            </Link>
            <p className="text-slate-400 text-xs leading-relaxed max-w-sm">
              Cartify is the modern everyday grocery and household essential startup. Built for speed, quality, and effortless daily shopping.
            </p>
            <div className="pt-2">
              <p className="text-xs font-semibold text-slate-200 mb-2">
                Download the Cartify Mobile App (Coming Soon)
              </p>
              <div className="flex items-center gap-2">
                <div className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-[11px] font-semibold text-slate-300">
                  📱 iOS App Store
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-[11px] font-semibold text-slate-300">
                  🤖 Google Play Store
                </div>
              </div>
            </div>
          </div>

          {/* Col 2: Categories */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">
              Categories
            </h4>
            <ul className="space-y-2.5 text-xs text-slate-400">
              <li>
                <Link href="/products?category=cat-fruits-veg" className="hover:text-brand-400 transition-colors">
                  Fruits & Vegetables
                </Link>
              </li>
              <li>
                <Link href="/products?category=cat-dairy-breakfast" className="hover:text-brand-400 transition-colors">
                  Dairy & Breakfast
                </Link>
              </li>
              <li>
                <Link href="/products?category=cat-bakery" className="hover:text-brand-400 transition-colors">
                  Bakery & Breads
                </Link>
              </li>
              <li>
                <Link href="/products?category=cat-beverages" className="hover:text-brand-400 transition-colors">
                  Beverages & Juices
                </Link>
              </li>
              <li>
                <Link href="/products?category=cat-meat-seafood" className="hover:text-brand-400 transition-colors">
                  Meat & Seafood
                </Link>
              </li>
              <li>
                <Link href="/categories" className="text-brand-400 font-semibold hover:underline">
                  All Categories →
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Customer Care */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">
              Customer Support
            </h4>
            <ul className="space-y-2.5 text-xs text-slate-400">
              <li>
                <Link href="/orders" className="hover:text-brand-400 transition-colors">
                  Track Your Order
                </Link>
              </li>
              <li>
                <Link href="/profile" className="hover:text-brand-400 transition-colors">
                  My Profile
                </Link>
              </li>
              <li>
                <Link href="/addresses" className="hover:text-brand-400 transition-colors">
                  Saved Addresses
                </Link>
              </li>
              <li>
                <Link href="/wishlist" className="hover:text-brand-400 transition-colors">
                  Wishlist
                </Link>
              </li>
              <li>
                <Link href="/faq" className="hover:text-brand-400 transition-colors">
                  Help & FAQs
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-brand-400 transition-colors">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Newsletter & Legal */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">
              Stay In The Loop
            </h4>
            <p className="text-xs text-slate-400 mb-3 leading-relaxed">
              Get weekly seasonal recipes, fresh harvest updates, and member-exclusive promo codes.
            </p>
            <form onSubmit={handleSubscribe} className="space-y-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full h-9 px-3 text-xs rounded-xl bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                required
              />
              <button
                type="submit"
                className="w-full h-9 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Subscribe
              </button>
            </form>
            <div className="pt-3 flex gap-3 text-[11px] text-slate-500">
              <Link href="/privacy" className="hover:text-slate-300">
                Privacy
              </Link>
              <span>•</span>
              <Link href="/terms" className="hover:text-slate-300">
                Terms
              </Link>
              <span>•</span>
              <Link href="/about" className="hover:text-slate-300">
                About
              </Link>
            </div>
          </div>
        </div>

        {/* Copyright and payment guarantee */}
        <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} Cartify Inc. All rights reserved. Designed for Web, iOS & Android.</p>
          <div className="flex items-center gap-3 text-slate-400">
            <span>Visa</span>
            <span>•</span>
            <span>Mastercard</span>
            <span>•</span>
            <span>Apple Pay</span>
            <span>•</span>
            <span>UPI</span>
            <span>•</span>
            <span>Cash on Delivery</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
