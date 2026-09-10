"use client";

import React, { useState } from "react";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { ChevronDown, HelpCircle } from "lucide-react";

export default function FaqPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const FAQS = [
    {
      q: "How does Cartify deliver in 15 minutes?",
      a: "We operate localized micro-fulfillment hubs stocked exclusively with top-velocity fresh produce and groceries. When an order is placed, automated batch scanners enable our pickers to bag your order in under 3 minutes, handing it directly to our neighborhood electric bike couriers.",
    },
    {
      q: "Is there a minimum order requirement?",
      a: "No! There is zero minimum order requirement on Cartify. You can order a single avocado or your entire week's grocery list. Orders over $35 receive completely free delivery.",
    },
    {
      q: "What is the return or refund policy if an item arrives damaged?",
      a: "We offer a 100% no-questions-asked fresh guarantee. If your fruit, milk, or bakery item doesn't meet your satisfaction, open your order in the Cartify app or website and click 'Request Refund'. Funds will be refunded back immediately.",
    },
    {
      q: "Are the fruits and vegetables organic and pesticide-free?",
      a: "All items labeled 'Organic' on Cartify are certified USDA Organic or grown by certified regenerative agriculture partners. We prioritize ethical local California and regional growers.",
    },
    {
      q: "How does the mobile app sync with the website?",
      a: "Cartify utilizes a unified API architecture. Your single user account, saved delivery addresses, wishlist, active cart, and order tracking timeline synchronize automatically across the website, Android, and iOS applications.",
    },
    {
      q: "What payment options are supported?",
      a: "We accept Visa, Mastercard, American Express, Apple Pay, Google Pay, UPI payments, and Cash / Scan-on-Delivery.",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Breadcrumb items={[{ label: "Frequently Asked Questions" }]} />

      <div className="text-center space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2.5 py-1 rounded-full">
          Help Center
        </span>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">
          Frequently Asked Questions
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Everything you need to know about 15-minute grocery deliveries, refunds, and organic sourcing.
        </p>
      </div>

      <div className="space-y-3 pt-4">
        {FAQS.map((faq, index) => {
          const isOpen = openIndex === index;
          return (
            <div
              key={index}
              className="rounded-2xl border border-slate-100 bg-white shadow-card overflow-hidden transition-all"
            >
              <button
                onClick={() => setOpenIndex(isOpen ? null : index)}
                className="w-full p-5 text-left flex items-center justify-between gap-4 font-bold text-slate-900 text-sm hover:text-brand-600 transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  <HelpCircle className="w-4 h-4 text-brand-500 shrink-0" />
                  {faq.q}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${
                    isOpen ? "rotate-180 text-brand-600" : ""
                  }`}
                />
              </button>
              {isOpen && (
                <div className="px-5 pb-5 pt-1 text-xs text-slate-600 leading-relaxed border-t border-slate-50">
                  {faq.a}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
