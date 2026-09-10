"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { ShoppingBag, Clock, Leaf, ShieldCheck, HeartHandshake, Award } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      <Breadcrumb items={[{ label: "About Cartify" }]} />

      {/* Hero section */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <span className="text-xs font-black uppercase tracking-wider text-brand-700 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
          The Cartify Story
        </span>
        <h1 className="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight">
          Reinventing Everyday Grocery for the Modern Generation.
        </h1>
        <p className="text-sm sm:text-base text-slate-500 leading-relaxed">
          Founded with a simple mission: delivering uncompromised farm-fresh quality to your kitchen in under 15 minutes, while empowering ethical regenerative farmers.
        </p>
      </div>

      {/* Showcase Image */}
      <div className="relative aspect-21/9 rounded-3xl overflow-hidden shadow-xl border border-slate-100">
        <Image
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?w=1600&auto=format&fit=crop&q=80"
          alt="Cartify Fresh Market"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent flex items-end p-8">
          <div className="text-white max-w-xl">
            <h3 className="text-xl font-bold">From Soil to Doorstep in Record Time</h3>
            <p className="text-xs text-slate-300 mt-1">
              Our hyper-local cold-chain network ensures produce retains its natural vitamins, crispness, and aroma.
            </p>
          </div>
        </div>
      </div>

      {/* Pillars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-8 rounded-3xl bg-white border border-slate-100 shadow-card space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">15-Minute Micro-Hubs</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            By situating intelligent micro-fulfillment hubs inside neighborhood districts, orders are packed within 3 minutes and swiftly delivered on zero-emission electric bikes.
          </p>
        </div>

        <div className="p-8 rounded-3xl bg-white border border-slate-100 shadow-card space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Leaf className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Regenerative Farming</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            We bypass middlemen and wholesale storage depots. Produce is harvested at peak maturity and chilled immediately, keeping nutrients intact.
          </p>
        </div>

        <div className="p-8 rounded-3xl bg-white border border-slate-100 shadow-card space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">100% Quality Pledge</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Every apple, avocado, and dairy carton is individually inspected. If anything doesn&apos;t meet your standards, we refund it with one single tap.
          </p>
        </div>
      </div>

      {/* Call to action */}
      <div className="p-8 sm:p-12 rounded-3xl bg-brand-900 text-white text-center space-y-4">
        <h2 className="text-2xl sm:text-3xl font-black">Experience the Cartify Difference Today</h2>
        <p className="text-xs sm:text-sm text-brand-200 max-w-md mx-auto">
          Join thousands of happy households enjoying fresh produce delivered straight to their doorstep.
        </p>
        <div className="pt-2">
          <Link href="/products">
            <Button variant="accent" size="lg">
              Start Shopping Now
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
