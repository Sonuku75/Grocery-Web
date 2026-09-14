"use client";

import React, { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { Phone, Lock, KeyRound, AlertCircle, ArrowLeft } from "lucide-react";
import { AccountProfile } from "@/types";

interface PhoneChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPhone?: string | null;
  onPhoneUpdated: (profile: AccountProfile) => void;
}

export function PhoneChangeModal({
  isOpen,
  onClose,
  currentPhone,
  onPhoneUpdated,
}: PhoneChangeModalProps) {
  const { showToast } = useToast();

  const [step, setStep] = useState<"INITIATE" | "VERIFY">("INITIATE");
  const [newPhone, setNewPhone] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setStep("INITIATE");
    setNewPhone("");
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

    const clean = newPhone.replace(/[\s\-\(\)]/g, "");
    const digits = clean.startsWith("+91")
      ? clean.slice(3)
      : clean.startsWith("0")
      ? clean.slice(1)
      : clean;

    if (!/^[6-9]\d{9}$/.test(digits)) {
      setError("Please provide a valid 10-digit Indian mobile number starting with 6-9.");
      return;
    }

    const formattedPhone = `+91${digits}`;
    if (currentPhone && currentPhone.replace(/\s+/g, "") === formattedPhone) {
      setError("The new phone number must be different from your current phone.");
      return;
    }

    if (!currentPassword) {
      setError("Current password is required to verify your identity.");
      return;
    }

    setIsLoading(true);
    try {
      await accountService.initiatePhoneChange({
        new_phone: formattedPhone,
        current_password: currentPassword,
      });
      showToast("Verification code sent to your new mobile number.", "info");
      setCurrentPassword("");
      setStep("VERIFY");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to initiate phone change.";
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
      const updatedProfile = await accountService.verifyPhoneChange({
        verification_code: code,
      });
      showToast("Mobile number updated and verified successfully!", "success");
      onPhoneUpdated(updatedProfile);
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
      title={step === "INITIATE" ? "Change Mobile Number" : "Verify Mobile Number"}
      description={
        step === "INITIATE"
          ? "Enter your new Indian mobile number and confirm your account password."
          : `Enter the 6-digit verification code dispatched to ${newPhone}.`
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

          {currentPhone && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                Current Mobile Number
              </label>
              <input
                type="text"
                value={currentPhone}
                disabled
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-500 shadow-xs"
              />
            </div>
          )}

          <Input
            label="New Mobile Phone Number"
            type="tel"
            inputMode="tel"
            value={newPhone}
            onChange={(e) => setNewPhone(e.target.value)}
            placeholder="+91 98765 43210"
            helperText="10-digit Indian mobile number (e.g. +91 9876543210)"
            leftIcon={<Phone className="w-4 h-4" />}
            autoComplete="tel"
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
              We sent a 6-digit SMS code to <strong className="text-slate-900">{newPhone}</strong>.
            </p>
            <p className="text-[11px] text-slate-400">
              The verification code expires in 15 minutes.
            </p>
          </div>

          <Input
            label="6-Digit SMS Verification Code"
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
                Confirm Phone
              </Button>
            </div>
          </div>
        </form>
      )}
    </Modal>
  );
}
