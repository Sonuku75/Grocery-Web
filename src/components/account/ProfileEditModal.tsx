"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { AccountProfile, AccountProfileUpdatePayload } from "@/types";
import { accountService } from "@/services/accountService";
import { useToast } from "@/context/ToastContext";
import { User, Phone, Calendar, FileText, Mail, Info, AlertCircle } from "lucide-react";

interface ProfileEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: AccountProfile | null;
  onProfileUpdated: (updated: AccountProfile) => void;
  onOpenEmailChange?: () => void;
}

export function ProfileEditModal({
  isOpen,
  onClose,
  profile,
  onProfileUpdated,
  onOpenEmailChange,
}: ProfileEditModalProps) {
  const { showToast } = useToast();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [bio, setBio] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (profile) {
      setName(profile.name || "");
      setPhone(profile.phone || "");
      setDateOfBirth(profile.date_of_birth || profile.dateOfBirth || "");
      setBio(profile.bio || "");
      setErrors({});
    }
  }, [profile, isOpen]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 2) {
      errs.name = "Name must be at least 2 characters long.";
    } else if (trimmedName.length > 100) {
      errs.name = "Name cannot exceed 100 characters.";
    }

    if (phone) {
      const cleanPhone = phone.replace(/[\s\-\(\)]/g, "");
      const digits = cleanPhone.startsWith("+91")
        ? cleanPhone.slice(3)
        : cleanPhone.startsWith("0")
        ? cleanPhone.slice(1)
        : cleanPhone;

      if (!/^[6-9]\d{9}$/.test(digits)) {
        errs.phone = "Enter a valid 10-digit Indian mobile number (starts with 6-9).";
      }
    }

    if (dateOfBirth) {
      const dobDate = new Date(dateOfBirth);
      const today = new Date();
      if (dobDate >= today) {
        errs.dateOfBirth = "Date of birth must be in the past.";
      } else {
        const age = today.getFullYear() - dobDate.getFullYear();
        if (age < 13) {
          errs.dateOfBirth = "You must be at least 13 years old.";
        } else if (age > 120) {
          errs.dateOfBirth = "Please provide a valid date of birth.";
        }
      }
    }

    if (bio && bio.length > 500) {
      errs.bio = "Bio cannot exceed 500 characters.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const payload: AccountProfileUpdatePayload = {
        name: name.trim(),
        phone: phone.trim() ? phone.trim() : undefined,
        date_of_birth: dateOfBirth || undefined,
        bio: bio.trim() || undefined,
      };

      const updated = await accountService.updateProfile(payload);
      showToast("Profile details updated successfully!", "success");
      onProfileUpdated(updated);
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update profile details.";
      showToast(message, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Personal Profile"
      description="Update your name, contact information, and personal preferences."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {/* Full Name */}
        <Input
          label="Full Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Alex Rivera"
          error={errors.name}
          leftIcon={<User className="w-4 h-4" />}
          autoComplete="name"
          required
        />

        {/* Read-only Email display with change trigger */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
            Email Address
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                <Mail className="w-4 h-4" />
              </div>
              <input
                type="email"
                value={profile?.email || ""}
                disabled
                className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-2.5 text-sm text-slate-500 cursor-not-allowed shadow-xs"
              />
            </div>
            {onOpenEmailChange && (
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={() => {
                  onClose();
                  onOpenEmailChange();
                }}
                className="shrink-0 text-xs"
              >
                Change Email
              </Button>
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-400 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 shrink-0" />
            Email changes require password verification and OTP confirmation.
          </p>
        </div>

        {/* Phone Number */}
        <Input
          label="Mobile Phone Number"
          type="tel"
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+91 98765 43210"
          error={errors.phone}
          helperText="Format: 10-digit Indian mobile number starting with 6-9"
          leftIcon={<Phone className="w-4 h-4" />}
          autoComplete="tel"
        />

        {/* Date of Birth */}
        <Input
          label="Date of Birth"
          type="date"
          value={dateOfBirth}
          onChange={(e) => setDateOfBirth(e.target.value)}
          error={errors.dateOfBirth}
          leftIcon={<Calendar className="w-4 h-4" />}
        />

        {/* Bio */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
            About You (Bio)
          </label>
          <div className="relative">
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="A brief sentence about your food preferences or household..."
              maxLength={500}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 shadow-xs focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-colors"
            />
          </div>
          <div className="flex justify-between items-center mt-1 text-[11px] text-slate-400">
            <span>Optional personal summary</span>
            <span>{bio.length}/500</span>
          </div>
          {errors.bio && <p className="mt-1 text-xs text-rose-500">{errors.bio}</p>}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
}
