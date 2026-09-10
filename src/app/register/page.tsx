"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { ShoppingBag, Lock, Mail, User, Phone, ArrowRight } from "lucide-react";
import { useToast } from "@/context/ToastContext";

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/profile";
  const { register } = useAuth();
  const { showToast } = useToast();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (!termsAccepted) {
      setError("Please accept the Terms of Service & Privacy Policy.");
      return;
    }

    setLoading(true);
    try {
      await register({
        fullName,
        email,
        mobile,
        password,
      });
      showToast("Account created successfully! Welcome to Cartify.", "success");
      router.push(redirect);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed. Please try again.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-100 p-8 shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-md">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Create Cartify Account
          </h1>
          <p className="text-xs text-slate-500">
            Enjoy instant 15-minute grocery deliveries and exclusive member deals.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <Input
            label="Full Name"
            placeholder="e.g. Alex Rivera"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            leftIcon={<User className="w-4 h-4" />}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="alex@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <Input
            label="Mobile Number"
            type="tel"
            placeholder="+1 (555) 000-0000"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            leftIcon={<Phone className="w-4 h-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="At least 6 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            minLength={6}
            required
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Re-type your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            minLength={6}
            required
          />

          <label className="flex items-start gap-2 pt-1 text-xs text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
            />
            <span>
              I agree to the{" "}
              <Link href="/terms" className="text-brand-600 hover:underline">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="/privacy" className="text-brand-600 hover:underline">
                Privacy Policy
              </Link>
              .
            </span>
          </label>

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
            Create Account
          </Button>
        </form>

        <p className="text-center text-xs text-slate-500">
          Already have an account?{" "}
          <Link
            href={`/login${redirect ? `?redirect=${encodeURIComponent(redirect)}` : ""}`}
            className="font-bold text-brand-600 hover:underline"
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading register...</div>}>
      <RegisterContent />
    </Suspense>
  );
}
