"use client";

import React from "react";
import { Breadcrumb } from "@/components/common/Breadcrumb";

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Breadcrumb items={[{ label: "Terms & Conditions" }]} />

      <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-10 shadow-card space-y-6 text-slate-700 text-xs sm:text-sm leading-relaxed">
        <div className="border-b border-slate-100 pb-4">
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900">
            Terms of Service
          </h1>
          <p className="text-xs text-slate-400 mt-1">Last Updated: March 2026</p>
        </div>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">1. Acceptance of Terms</h2>
          <p>
            By accessing or using Cartify services across our web application, iOS application, or Android application, you agree to be bound by these Terms of Service.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">2. Service Availability & Delivery</h2>
          <p>
            Cartify offers 15-minute express delivery subject to store hours, courier availability, and local weather safety conditions. While we strive to meet our delivery targets, external factors such as traffic may occasionally impact timelines.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">3. Pricing & Billing</h2>
          <p>
            Product prices are displayed in USD and include all applicable local sales taxes where noted. Discounts and coupons are subject to terms specified at redemption. Cartify reserves the right to modify prices or correct pricing discrepancies.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">4. Fresh Produce Satisfaction</h2>
          <p>
            Cartify guarantees farm-fresh quality. If any item is found suboptimal, customers can claim a direct refund or credit within 24 hours of delivery.
          </p>
        </section>
      </div>
    </div>
  );
}
