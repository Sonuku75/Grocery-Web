"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { Input } from "@/components/common/Input";
import { CreditCard, QrCode, ShieldCheck, CheckCircle2, Lock } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function PaymentPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [selectedMethod, setSelectedMethod] = useState<"card" | "upi" | "netbanking">("card");
  const [loading, setLoading] = useState(false);

  const handlePay = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      showToast("Payment simulated successfully!", "success");
      router.push("/orders");
    }, 1200);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Breadcrumb
        items={[
          { label: "Checkout", href: "/checkout" },
          { label: "Payment Gateway" },
        ]}
      />

      <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-10 shadow-card space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900">
              Secure Checkout & Payment
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Select your payment method. 256-bit encrypted SSL.
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl">
            <Lock className="w-3.5 h-3.5" />
            <span>Secure</span>
          </div>
        </div>

        {/* Method selection */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { id: "card" as const, title: "Credit / Debit Card", icon: CreditCard },
            { id: "upi" as const, title: "Instant UPI", icon: QrCode },
            { id: "netbanking" as const, title: "Net Banking", icon: ShieldCheck },
          ].map((m) => {
            const Icon = m.icon;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => setSelectedMethod(m.id)}
                className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all ${
                  selectedMethod === m.id
                    ? "border-brand-600 bg-brand-50/50 text-brand-700 font-bold shadow-xs"
                    : "border-slate-200 text-slate-600 hover:border-slate-300"
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs">{m.title}</span>
              </button>
            );
          })}
        </div>

        {/* Form area */}
        <form onSubmit={handlePay} className="space-y-4 pt-2">
          {selectedMethod === "card" && (
            <div className="space-y-3">
              <Input
                label="Cardholder Full Name"
                defaultValue="Alex Rivera"
                required
              />
              <Input
                label="Card Number"
                defaultValue="4242 4242 4242 4242"
                required
              />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Expiry (MM/YY)" defaultValue="12/28" required />
                <Input label="CVV" type="password" defaultValue="888" required />
              </div>
            </div>
          )}

          {selectedMethod === "upi" && (
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center space-y-3">
              <QrCode className="w-16 h-16 mx-auto text-brand-600" />
              <p className="text-xs font-bold text-slate-800">Scan QR Code or Enter UPI ID</p>
              <Input
                placeholder="e.g. alex@okaxis or 9876543210@paytm"
                defaultValue="alex@okaxis"
              />
            </div>
          )}

          {selectedMethod === "netbanking" && (
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase">
                Choose Bank
              </label>
              <select className="w-full px-4 py-2.5 text-xs rounded-xl border border-slate-200 bg-white">
                <option>Chase Bank</option>
                <option>Bank of America</option>
                <option>Wells Fargo</option>
                <option>Citibank</option>
              </select>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <Link href="/checkout" className="text-xs font-bold text-slate-500 hover:text-slate-800">
              ← Return to Checkout
            </Link>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              leftIcon={<CheckCircle2 className="w-5 h-5" />}
            >
              Authorize Payment
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
