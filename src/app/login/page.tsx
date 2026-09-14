"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { ShoppingBag, Lock, Mail, ArrowRight, UserCheck } from "lucide-react";
import { useToast } from "@/context/ToastContext";
import { getSafeRedirect } from "@/lib/urlSecurity";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = getSafeRedirect(searchParams.get("redirect"), "/profile");
  const { login } = useAuth();
  const { showToast } = useToast();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ identifier, password });
      showToast("Welcome back to Cartify!", "success");
      router.push(redirect);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in. Please verify your credentials.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIdentifier("alex.rivera@cartify.com");
    setPassword("cartify123");
    setLoading(true);
    try {
      await login({ identifier: "alex.rivera@cartify.com", password: "cartify123" });
      showToast("Signed in as Demo Customer (Alex Rivera)", "success");
      router.push(redirect);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-100 p-8 shadow-xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-md">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Sign In to Cartify
          </h1>
          <p className="text-xs text-slate-500">
            Access your fast 15-min delivery orders, saved addresses, and wishlist.
          </p>
        </div>

        {/* Demo Fast Login Helper */}
        <button
          type="button"
          onClick={handleDemoLogin}
          className="w-full p-3 rounded-2xl bg-brand-50 hover:bg-brand-100/80 border border-brand-200/80 text-brand-800 text-xs font-bold flex items-center justify-center gap-2 transition-colors"
        >
          <UserCheck className="w-4 h-4 text-brand-600" />
          <span>Quick 1-Click Demo Login</span>
        </button>

        <div className="relative flex items-center justify-center">
          <div className="border-t border-slate-200 w-full" />
          <span className="bg-white px-3 text-[11px] text-slate-400 font-semibold uppercase tracking-wider absolute">
            Or With Email / Mobile
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email or Mobile"
            placeholder="e.g. alex@example.com or +1 555-234-5678"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <div className="space-y-1">
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />
            <div className="flex justify-end">
              <Link
                href="/forgot-password"
                className="text-[11px] font-semibold text-brand-600 hover:underline"
              >
                Forgot Password?
              </Link>
            </div>
          </div>

          {error && (
            <p className="text-xs font-medium text-rose-500 bg-rose-50 p-2.5 rounded-xl border border-rose-200">
              {error}
            </p>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={loading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Sign In
          </Button>
        </form>

        {/* Bottom Link */}
        <p className="text-center text-xs text-slate-500">
          Don&apos;t have an account?{" "}
          <Link
            href={`/register${redirect ? `?redirect=${encodeURIComponent(redirect)}` : ""}`}
            className="font-bold text-brand-600 hover:underline"
          >
            Create an Account
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading sign in...</div>}>
      <LoginContent />
    </Suspense>
  );
}
