"use client";

import React, { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { Mail, Lock, KeyRound, CheckCircle2, AlertCircle, ArrowLeft } from "lucide-react";
import { AccountProfile } from "@/types";

interface EmailChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentEmail: string;
  onEmailUpdated: (profile: AccountProfile) => void;
}

export function EmailChangeModal({
  isOpen,
  onClose,
  currentEmail,
  onEmailUpdated,
}: EmailChangeModalProps) {
  const { showToast } = useToast();

  const [step, setStep] = useState<"INITIATE" | "VERIFY">("INITIATE");
  const [newEmail, setNewEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setStep("INITIATE");
    setNewEmail("");
    setCurrentPassword("");
    setVerificationCode("");
    setError(null);
    setIsLoading(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleInitiate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = newEmail.trim().toLowerCase();
    if (!trimmedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setError("Please provide a valid email address.");
      return;
    }

    if (trimmedEmail === currentEmail.toLowerCase()) {
      setError("The new email must be different from your current email.");
      return;
    }

    if (!currentPassword) {
      setError("Current password is required to verify your identity.");
      return;
    }

    setIsLoading(true);
    try {
      await accountService.initiateEmailChange({
        new_email: trimmedEmail,
        current_password: currentPassword,
      });
      showToast("Verification code dispatched to your new email address.", "info");
      // Clear password from state immediately after step 1
      setCurrentPassword("");
      setStep("VERIFY");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to initiate email change.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const code = verificationCode.trim();
    if (!code || code.length < 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setIsLoading(true);
    try {
      const updatedProfile = await accountService.verifyEmailChange({
        verification_code: code,
      });
      showToast("Email address changed and verified successfully!", "success");
      onEmailUpdated(updatedProfile);
      handleClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification code is invalid or has expired.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={step === "INITIATE" ? "Change Email Address" : "Verify New Email"}
      description={
        step === "INITIATE"
          ? "Enter your new email address and confirm your account password."
          : `Enter the 6-digit verification code sent to ${newEmail}.`
      }
      maxWidth="md"
    >
      {step === "INITIATE" ? (
        <form onSubmit={handleInitiate} className="space-y-4 pt-2">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
              Current Email
            </label>
            <input
              type="text"
              value={currentEmail}
              disabled
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-500 shadow-xs"
            />
          </div>

          <Input
            label="New Email Address"
            type="email"
            inputMode="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            placeholder="new.email@example.com"
            leftIcon={<Mail className="w-4 h-4" />}
            autoComplete="email"
            required
          />

          <Input
            label="Current Account Password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="••••••••"
            helperText="Required to authorize this credential change."
            leftIcon={<Lock className="w-4 h-4" />}
            autoComplete="current-password"
            required
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
              disabled={isLoading}
            >
              Continue to Verification
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleVerify} className="space-y-4 pt-2">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="text-center py-2 space-y-1">
            <div className="w-12 h-12 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mx-auto">
              <KeyRound className="w-6 h-6" />
            </div>
            <p className="text-xs text-slate-600">
              We sent a 6-digit code to <strong className="text-slate-900">{newEmail}</strong>.
            </p>
            <p className="text-[11px] text-slate-400">
              The code expires in 15 minutes.
            </p>
          </div>

          <Input
            label="6-Digit Verification Code"
            type="text"
            inputMode="numeric"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="123456"
            className="text-center tracking-widest text-lg font-bold"
            maxLength={6}
            autoComplete="one-time-code"
            required
          />

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setStep("INITIATE");
                setVerificationCode("");
                setError(null);
              }}
              disabled={isLoading}
              leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
            >
              Back
            </Button>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleClose}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isLoading}
                disabled={isLoading || verificationCode.length < 6}
              >
                Confirm Email
              </Button>
            </div>
          </div>
        </form>
      )}
    </Modal>
  );
}
