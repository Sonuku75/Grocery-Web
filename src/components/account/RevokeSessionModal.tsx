"use client";

import React, { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { Button } from "@/components/common/Button";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";
import { Smartphone, LogOut, AlertCircle, ShieldAlert } from "lucide-react";
import { UserSession } from "@/types";

export type RevokeMode = "SINGLE" | "OTHERS" | "ALL";

interface RevokeSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: RevokeMode;
  targetSession?: UserSession | null;
  onRevocationComplete: () => void;
}

export function RevokeSessionModal({
  isOpen,
  onClose,
  mode,
  targetSession,
  onRevocationComplete,
}: RevokeSessionModalProps) {
  const { showToast } = useToast();
  const { logout } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getTitle = () => {
    switch (mode) {
      case "SINGLE":
        return `Sign Out Device: ${targetSession?.device_name || targetSession?.deviceName || "Device"}`;
      case "OTHERS":
        return "Sign Out All Other Devices";
      case "ALL":
        return "Sign Out All Devices (Including Current)";
    }
  };

  const getDescription = () => {
    switch (mode) {
      case "SINGLE":
        return "Are you sure you want to revoke this session? That device will immediately lose access and need to sign in again.";
      case "OTHERS":
        return "This will invalidate all active sessions except your current browser. Other devices will be signed out immediately.";
      case "ALL":
        return "This will revoke ALL active sessions including your current device. You will be signed out immediately.";
    }
  };

  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (mode === "SINGLE" && targetSession) {
        await accountService.revokeSession(targetSession.id);
        showToast("Device session revoked successfully.", "success");
      } else if (mode === "OTHERS") {
        const res = await accountService.revokeOtherSessions();
        showToast(res.message || "Other active sessions have been signed out.", "success");
      } else if (mode === "ALL") {
        await accountService.revokeAllSessions();
        showToast("All sessions revoked. Redirecting to login...", "info");
        await logout();
        return;
      }
      onRevocationComplete();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to revoke session.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={getTitle()}
      description={getDescription()}
      maxWidth="md"
    >
      <div className="space-y-4 pt-2">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200/80 text-xs text-amber-800 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-amber-900">Security Note</p>
            <p className="text-amber-700 leading-relaxed">
              Session tokens are verified against cryptographic hashes. Revoking will immediately terminate access on target devices.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant={mode === "ALL" ? "danger" : "primary"}
            isLoading={isLoading}
            onClick={handleConfirm}
          >
            {mode === "ALL" ? "Sign Out Everywhere" : "Confirm Sign Out"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
