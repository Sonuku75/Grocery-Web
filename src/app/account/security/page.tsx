"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AccountLayout } from "@/components/account/AccountLayout";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { EmailChangeModal } from "@/components/account/EmailChangeModal";
import { PhoneChangeModal } from "@/components/account/PhoneChangeModal";
import { DeleteAccountModal } from "@/components/account/DeleteAccountModal";
import { accountService } from "@/services/accountService";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { AccountProfile, AccountSecuritySummary } from "@/types";
import {
  ShieldCheck,
  Lock,
  KeyRound,
  Eye,
  EyeOff,
  Mail,
  Phone,
  Smartphone,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Clock,
  Trash2,
  Undo2,
  ArrowRight,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

export default function AccountSecurityPage() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [securitySummary, setSecuritySummary] = useState<AccountSecuritySummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Password form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Deletion state
  const [isCancellingDeletion, setIsCancellingDeletion] = useState(false);

  // Modals
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [isPhoneModalOpen, setIsPhoneModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [prof, sec] = await Promise.allSettled([
        accountService.getAccountOverview(),
        accountService.getSecuritySummary(),
      ]);

      if (prof.status === "fulfilled") setProfile(prof.value);
      if (sec.status === "fulfilled") setSecuritySummary(sec.value);
    } catch (err) {
      console.error("Failed to load security summary:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword === currentPassword) {
      setPasswordError("New password must be different from your current password.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await accountService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      showToast(res.message || "Password updated successfully. Other active sessions were invalidated.", "success");
      // Clear sensitive form state
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update password. Please check your current password.";
      setPasswordError(msg);
      showToast(msg, "error");
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleCancelDeletion = async () => {
    setIsCancellingDeletion(true);
    try {
      const res = await accountService.cancelDeletion();
      showToast(res.message || "Account deletion request cancelled successfully.", "success");
      if (profile) setProfile({ ...profile, has_pending_deletion: false });
      if (securitySummary) setSecuritySummary({ ...securitySummary, has_pending_deletion: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to cancel deletion.";
      showToast(msg, "error");
    } finally {
      setIsCancellingDeletion(false);
    }
  };

  return (
    <AccountLayout
      title="Security & Credentials"
      description="Manage your account password, email, phone number, and active device sessions."
      breadcrumbItems={[{ label: "Security Settings" }]}
    >
      {/* 1. Pending Deletion Alert */}
      {profile?.has_pending_deletion && (
        <div className="p-5 sm:p-6 rounded-3xl bg-rose-50 border border-rose-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fade-in">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h2 className="text-sm font-bold text-rose-900">Deletion Request Active</h2>
              <p className="text-xs text-rose-700 max-w-xl">
                Your account is pending deletion. You can cancel this request at any time during the 30-day grace period.
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="danger"
            size="sm"
            isLoading={isCancellingDeletion}
            onClick={handleCancelDeletion}
            leftIcon={<Undo2 className="w-3.5 h-3.5" />}
            className="shrink-0"
          >
            Cancel Deletion
          </Button>
        </div>
      )}

      {/* 2. Password Change Section */}
      <section
        aria-label="Password Modification Form"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-6"
      >
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
                <KeyRound className="w-4 h-4" />
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">Change Password</h2>
            </div>
            <p className="text-xs text-slate-500">
              Update your account password. For your security, changing your password signs out all other active devices.
            </p>
          </div>
          {securitySummary?.password_last_changed_at && (
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-slate-400">
              <Clock className="w-3.5 h-3.5" />
              Last changed: {formatDate(securitySummary.password_last_changed_at)}
            </span>
          )}
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
          {passwordError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{passwordError}</span>
            </div>
          )}

          {/* Current Password */}
          <Input
            label="Current Password"
            type={showCurrent ? "text" : "password"}
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="••••••••"
            leftIcon={<Lock className="w-4 h-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                aria-label={showCurrent ? "Hide current password" : "Show current password"}
                className="hover:text-slate-600 transition-colors p-1"
              >
                {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
            autoComplete="current-password"
            required
          />

          {/* New Password */}
          <Input
            label="New Password"
            type={showNew ? "text" : "password"}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="••••••••"
            helperText="Minimum 8 characters. Must be different from current password."
            leftIcon={<Lock className="w-4 h-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                aria-label={showNew ? "Hide new password" : "Show new password"}
                className="hover:text-slate-600 transition-colors p-1"
              >
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
            autoComplete="new-password"
            required
          />

          {/* Confirm New Password */}
          <Input
            label="Confirm New Password"
            type={showConfirm ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            leftIcon={<Lock className="w-4 h-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                aria-label={showConfirm ? "Hide confirmation password" : "Show confirmation password"}
                className="hover:text-slate-600 transition-colors p-1"
              >
                {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
            autoComplete="new-password"
            required
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              isLoading={passwordLoading}
              disabled={passwordLoading || !currentPassword || !newPassword || !confirmPassword}
            >
              Update Password
            </Button>
          </div>
        </form>
      </section>

      {/* 3. Credential Management: Email & Phone */}
      <section
        aria-label="Verified Contact Credentials"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-6"
      >
        <div className="space-y-1">
          <h2 className="text-base sm:text-lg font-bold text-slate-900">Contact Credentials</h2>
          <p className="text-xs text-slate-500">
            Updating your primary email or phone number requires two-factor cryptographic verification.
          </p>
        </div>

        <div className="divide-y divide-slate-100">
          {/* Email Row */}
          <div className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                <Mail className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-900">
                    {profile?.email || user?.email}
                  </span>
                  <Badge variant="success">Verified</Badge>
                </div>
                <p className="text-xs text-slate-500">
                  Primary email used for sign in, order confirmations, and receipt dispatch.
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEmailModalOpen(true)}
              className="shrink-0 self-end sm:self-center text-xs"
            >
              Change Email
            </Button>
          </div>

          {/* Phone Row */}
          <div className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <Phone className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-900">
                    {profile?.phone || "No phone number linked"}
                  </span>
                  {profile?.phone ? (
                    <Badge variant="success">Verified</Badge>
                  ) : (
                    <Badge variant="neutral">Not Added</Badge>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  Used for delivery driver updates, SMS OTP authentication, and parcel tracking.
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPhoneModalOpen(true)}
              className="shrink-0 self-end sm:self-center text-xs"
            >
              {profile?.phone ? "Change Phone" : "Add Phone"}
            </Button>
          </div>
        </div>
      </section>

      {/* 4. Active Sessions Card */}
      <section
        aria-label="Active Multi-Device Sessions"
        className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-6"
      >
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 mt-0.5">
            <Smartphone className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">Multi-Device Sessions</h2>
              <Badge variant="brand">{securitySummary?.active_sessions || 1} Active</Badge>
            </div>
            <p className="text-xs text-slate-500 max-w-xl">
              Inspect devices logged into your account and revoke sessions you don&apos;t recognize to protect against unauthorized access.
            </p>
          </div>
        </div>

        <Link href="/account/sessions" className="shrink-0">
          <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
            Manage Sessions
          </Button>
        </Link>
      </section>

      {/* 5. Danger Zone */}
      <section
        aria-label="Danger Zone Deletion"
        className="bg-white rounded-3xl border border-rose-100 p-6 sm:p-8 shadow-xs space-y-4"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-rose-900">Danger Zone</h2>
            <p className="text-xs text-slate-500">
              Irreversible account actions and deletion workflows.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-rose-50/50 border border-rose-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-900">Account Deletion</p>
            <p className="text-xs text-slate-500 max-w-xl">
              Schedule account deletion with a 30-day grace period. In-flight orders will prevent deletion until delivered or cancelled.
            </p>
          </div>
          {profile?.has_pending_deletion ? (
            <Button
              variant="outline"
              size="sm"
              isLoading={isCancellingDeletion}
              onClick={handleCancelDeletion}
              className="shrink-0 text-xs"
            >
              Cancel Deletion Request
            </Button>
          ) : (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setIsDeleteModalOpen(true)}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              className="shrink-0 text-xs"
            >
              Delete Account
            </Button>
          )}
        </div>
      </section>

      {/* Modals */}
      <EmailChangeModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        currentEmail={profile?.email || user?.email || ""}
        onEmailUpdated={(updated) => setProfile(updated)}
      />

      <PhoneChangeModal
        isOpen={isPhoneModalOpen}
        onClose={() => setIsPhoneModalOpen(false)}
        currentPhone={profile?.phone}
        onPhoneUpdated={(updated) => setProfile(updated)}
      />

      <DeleteAccountModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onDeletionScheduled={() => {
          if (profile) setProfile({ ...profile, has_pending_deletion: true });
        }}
      />
    </AccountLayout>
  );
}
