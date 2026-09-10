"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/common/Button";
import { ShoppingBag, KeyRound, CheckCircle2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

function OtpContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mobile = searchParams.get("mobile") || "+1 (555) 234-5678";
  const redirect = searchParams.get("redirect") || "/profile";
  const { showToast } = useToast();

  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [timer, setTimer] = useState(45);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (timer > 0) {
      const interval = setInterval(() => setTimer((t) => t - 1), 1000);
      return () => clearInterval(interval);
    }
  }, [timer]);

  const handleChange = (index: number, val: string) => {
    if (!/^\d*$/.test(val)) return;
    const newOtp = [...otp];
    newOtp[index] = val.slice(-1);
    setOtp(newOtp);

    // Focus next input
    if (val && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-input-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    const entered = otp.join("");
    if (entered.length < 6) {
      showToast("Please enter complete 6-digit code", "error");
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      showToast("Mobile verified successfully!", "success");
      router.push(redirect);
    }, 600);
  };

  const resendOtp = () => {
    setTimer(45);
    showToast("A new verification code has been dispatched.", "info");
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-100 p-8 shadow-xl space-y-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-md">
          <KeyRound className="w-6 h-6" />
        </div>

        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Verify Phone Number
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            We sent a 6-digit verification code to <strong>{mobile}</strong>
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-6">
          <div className="flex justify-center gap-2">
            {otp.map((digit, idx) => (
              <input
                key={idx}
                id={`otp-input-${idx}`}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                className="w-11 h-12 text-center text-lg font-black rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 outline-none transition-all shadow-xs"
              />
            ))}
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={loading}
          >
            Verify & Proceed
          </Button>
        </form>

        <div className="text-xs text-slate-500">
          {timer > 0 ? (
            <span>Resend code in <strong className="text-slate-800">{timer}s</strong></span>
          ) : (
            <button
              type="button"
              onClick={resendOtp}
              className="font-bold text-brand-600 hover:underline"
            >
              Resend Verification Code
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerifyOtpPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading OTP verification...</div>}>
      <OtpContent />
    </Suspense>
  );
}
