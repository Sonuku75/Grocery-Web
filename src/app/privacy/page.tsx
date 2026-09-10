"use client";

import React from "react";
import { Breadcrumb } from "@/components/common/Breadcrumb";

export default function PrivacyPolicyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Breadcrumb items={[{ label: "Privacy Policy" }]} />

      <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-10 shadow-card space-y-6 text-slate-700 text-xs sm:text-sm leading-relaxed">
        <div className="border-b border-slate-100 pb-4">
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900">
            Cartify Privacy Policy
          </h1>
          <p className="text-xs text-slate-400 mt-1">Last Updated: March 2026</p>
        </div>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">1. Information We Collect</h2>
          <p>
            When you register for Cartify, place orders, or browse our grocery catalog, we collect personal information such as your name, delivery address, phone number, email address, and order transaction history.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">2. How We Use Your Data</h2>
          <p>
            Your information is used strictly to fulfill grocery orders in 15 minutes, communicate delivery status updates via SMS/notifications, securely process payments, and improve inventory forecasting at your local fulfillment hub.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">3. Multi-Platform Security</h2>
          <p>
            Whether accessing Cartify through our website, Android application, or iOS application, your authentication is protected using industry-standard JWT encryption and TLS 1.3 encryption. We never sell your personal data to third parties.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-bold text-slate-900">4. Your Rights</h2>
          <p>
            You can request access to, modification of, or deletion of your personal account data at any time by contacting our privacy compliance team at privacy@cartify.com.
          </p>
        </section>
      </div>
    </div>
  );
}
