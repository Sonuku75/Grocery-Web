"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { authService } from "@/services/authService";
import { Mail, ArrowLeft, CheckCircle2, ShoppingBag } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-100 p-8 shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-md">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Forgot Password?
          </h1>
          <p className="text-xs text-slate-500">
            Enter the email address registered with your Cartify account.
          </p>
        </div>

        {submitted ? (
          <div className="text-center space-y-4 py-4 animate-fade-in">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Check Your Email</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              We&apos;ve sent password reset instructions to <strong>{email}</strong>.
            </p>
            <div className="pt-2">
              <Link href="/login">
                <Button variant="outline" size="sm">
                  Back to Sign In
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              placeholder="alex@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4" />}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={loading}
            >
              Send Reset Link
            </Button>

            <div className="text-center pt-2">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-brand-600 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Sign In</span>
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
