"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { ShoppingBag, Lock, CheckCircle2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function ResetPasswordPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
      showToast("Password updated successfully! You may now sign in.", "success");
      setTimeout(() => router.push("/login"), 2000);
    }, 800);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-100 p-8 shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-md">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Reset Your Password
          </h1>
          <p className="text-xs text-slate-500">
            Choose a strong new password for your Cartify account.
          </p>
        </div>

        {success ? (
          <div className="text-center space-y-3 py-4 animate-fade-in">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Password Reset Complete</h3>
            <p className="text-xs text-slate-500">
              Redirecting you to the sign in page...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="New Password"
              type="password"
              placeholder="At least 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />

            <Input
              label="Confirm New Password"
              type="password"
              placeholder="Re-type new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />

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
            >
              Update Password
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
