"use client";

import React, { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { AlertTriangle, Lock, ShieldAlert, CheckCircle2 } from "lucide-react";
import { AccountDeletionResponse } from "@/types";

interface DeleteAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeletionScheduled: (res: AccountDeletionResponse) => void;
}

export function DeleteAccountModal({
  isOpen,
  onClose,
  onDeletionScheduled,
}: DeleteAccountModalProps) {
  const { showToast } = useToast();

  const [password, setPassword] = useState("");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setPassword("");
    setReason("");
    setError(null);
    setIsSubmitting(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!password) {
      setError("Please confirm your current password to proceed.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await accountService.requestDeletion({
        current_password: password,
        reason: reason.trim() || undefined,
      });

      showToast("Account deletion scheduled with a 30-day grace period.", "warning");
      onDeletionScheduled(res);
      handleClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to schedule account deletion.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Request Account Deletion"
      description="Please review the implications of deleting your Cartify account."
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {/* Warning Banner */}
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200/80 text-xs text-rose-800 space-y-2">
          <div className="flex items-center gap-2 font-bold text-rose-900 text-sm">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>Important Deletion Notice</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-rose-700 leading-relaxed">
            <li>Your account will enter a <strong>30-day grace period</strong>.</li>
            <li>You can cancel the deletion at any time during this grace period.</li>
            <li>Active orders cannot be in progress when requesting deletion.</li>
            <li>Historical tax invoices and payment transactions are preserved per statutory regulations.</li>
          </ul>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Reason */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
            Reason for leaving (Optional)
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="">Select a reason...</option>
            <option value="Moving to another location">Moving to another location</option>
            <option value="Duplicate or unused account">Duplicate or unused account</option>
            <option value="Privacy concerns">Privacy concerns</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Current Password */}
        <Input
          label="Confirm Current Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          helperText="Step-up authentication is required for destructive account requests."
          leftIcon={<Lock className="w-4 h-4" />}
          autoComplete="current-password"
          required
        />

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button
            type="button"
            variant="ghost"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Keep Account
          </Button>
          <Button
            type="submit"
            variant="danger"
            isLoading={isSubmitting}
            disabled={isSubmitting || !password}
          >
            Schedule Deletion
          </Button>
        </div>
      </form>
    </Modal>
  );
}
