import { apiClient, isMockMode } from "@/lib/api";
import {
  AccountChangePasswordPayload,
  AccountDeletionCancelResponse,
  AccountDeletionPayload,
  AccountDeletionResponse,
  AccountProfile,
  AccountProfileUpdatePayload,
  AccountSecuritySummary,
  InitiateEmailChangePayload,
  InitiatePhoneChangePayload,
  SecurityEventSummary,
  SessionRevokeResponse,
  UserSession,
  VerifyEmailChangePayload,
  VerifyPhoneChangePayload,
} from "@/types";

const MOCK_STORAGE_KEY = "cartify_account_profile";
const MOCK_SESSIONS_KEY = "cartify_account_sessions";

const DEFAULT_MOCK_PROFILE: AccountProfile = {
  id: "usr-demo",
  name: "Alex Rivera",
  email: "alex.rivera@cartify.com",
  phone: "+919876543210",
  avatar_url: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
  date_of_birth: "1994-06-15",
  bio: "Organic grocery enthusiast and weekly meal prepper.",
  is_verified: true,
  created_at: "2026-01-15T08:00:00Z",
  has_pending_deletion: false,
};

const DEFAULT_MOCK_SESSIONS: UserSession[] = [
  {
    id: "sess-curr-1",
    device_name: "Chrome on macOS",
    platform: "Desktop (macOS)",
    ip_address: "192.168.*.*",
    last_seen_at: new Date().toISOString(),
    created_at: "2026-09-10T10:00:00Z",
    expires_at: "2026-10-10T10:00:00Z",
    is_current: true,
  },
  {
    id: "sess-mob-2",
    device_name: "Cartify App on iPhone 15",
    platform: "Mobile (iOS)",
    ip_address: "103.21.*.*",
    last_seen_at: "2026-09-13T18:45:00Z",
    created_at: "2026-09-01T12:00:00Z",
    expires_at: "2026-10-01T12:00:00Z",
    is_current: false,
  },
];

function getStoredMockProfile(): AccountProfile {
  if (typeof window === "undefined") return DEFAULT_MOCK_PROFILE;
  try {
    const raw = localStorage.getItem(MOCK_STORAGE_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_MOCK_PROFILE;
  } catch {
    return DEFAULT_MOCK_PROFILE;
  }
}

function saveStoredMockProfile(profile: AccountProfile): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(profile));
  } catch {}
}

function getStoredMockSessions(): UserSession[] {
  if (typeof window === "undefined") return DEFAULT_MOCK_SESSIONS;
  try {
    const raw = localStorage.getItem(MOCK_SESSIONS_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_MOCK_SESSIONS;
  } catch {
    return DEFAULT_MOCK_SESSIONS;
  }
}

function saveStoredMockSessions(sessions: UserSession[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(MOCK_SESSIONS_KEY, JSON.stringify(sessions));
  } catch {}
}

export const accountService = {
  /**
   * Fetch current authenticated customer's account overview and profile.
   * Calls GET /api/v1/account
   */
  async getAccountOverview(): Promise<AccountProfile> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<AccountProfile>("/account");
        if (res.success && res.data) {
          return res.data;
        }
      } catch (err) {
        console.warn("API /account call failed, falling back to mock profile:", err);
      }
    }
    return getStoredMockProfile();
  },

  /**
   * Update customer profile attributes (name, phone, bio, avatar_url, date_of_birth).
   * Direct email changes are rejected by backend and must use initiateEmailChange.
   * Calls PATCH /api/v1/account/profile
   */
  async updateProfile(payload: AccountProfileUpdatePayload): Promise<AccountProfile> {
    if (!isMockMode()) {
      const res = await apiClient.patch<AccountProfile>("/account/profile", payload);
      if (res.success && res.data) {
        saveStoredMockProfile(res.data);
        return res.data;
      }
      throw new Error(res.error || "Failed to update profile.");
    }

    const current = getStoredMockProfile();
    const updated: AccountProfile = {
      ...current,
      name: payload.name ? payload.name.trim() : current.name,
      phone: payload.phone || current.phone,
      avatar_url: payload.avatar_url || current.avatar_url,
      date_of_birth: payload.date_of_birth !== undefined ? payload.date_of_birth : current.date_of_birth,
      bio: payload.bio !== undefined ? payload.bio : current.bio,
    };
    saveStoredMockProfile(updated);
    return updated;
  },

  /**
   * Initiate staged email change with current password confirmation.
   * Calls POST /api/v1/account/email-change
   */
  async initiateEmailChange(payload: InitiateEmailChangePayload): Promise<{ message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<{ message: string }>("/account/email-change", payload);
      if (res.success) {
        return res.data || { message: res.message || "Verification code sent to new email." };
      }
      throw new Error(res.error || "Failed to initiate email change.");
    }
    return { message: "Verification code sent to " + payload.new_email };
  },

  /**
   * Verify staged email change using 6-digit OTP code.
   * Calls POST /api/v1/account/email-change/verify
   */
  async verifyEmailChange(payload: VerifyEmailChangePayload): Promise<AccountProfile> {
    if (!isMockMode()) {
      const res = await apiClient.post<AccountProfile>("/account/email-change/verify", payload);
      if (res.success && res.data) {
        saveStoredMockProfile(res.data);
        return res.data;
      }
      throw new Error(res.error || "Verification failed. Invalid or expired code.");
    }

    const current = getStoredMockProfile();
    saveStoredMockProfile(current);
    return current;
  },

  /**
   * Initiate staged phone change with current password confirmation.
   * Calls POST /api/v1/account/phone-change
   */
  async initiatePhoneChange(payload: InitiatePhoneChangePayload): Promise<{ message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<{ message: string }>("/account/phone-change", payload);
      if (res.success) {
        return res.data || { message: res.message || "Verification code sent to new phone." };
      }
      throw new Error(res.error || "Failed to initiate phone change.");
    }
    return { message: "Verification code sent to " + payload.new_phone };
  },

  /**
   * Verify staged phone change using 6-digit OTP code.
   * Calls POST /api/v1/account/phone-change/verify
   */
  async verifyPhoneChange(payload: VerifyPhoneChangePayload): Promise<AccountProfile> {
    if (!isMockMode()) {
      const res = await apiClient.post<AccountProfile>("/account/phone-change/verify", payload);
      if (res.success && res.data) {
        saveStoredMockProfile(res.data);
        return res.data;
      }
      throw new Error(res.error || "Verification failed. Invalid or expired code.");
    }

    const current = getStoredMockProfile();
    saveStoredMockProfile(current);
    return current;
  },

  /**
   * Step-up password change. Enforces current password check, new != current.
   * Automatically terminates all active sessions and refresh tokens on backend.
   * Calls POST /api/v1/account/change-password
   */
  async changePassword(payload: AccountChangePasswordPayload): Promise<{ message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<{ message: string }>("/account/change-password", payload);
      if (res.success) {
        return res.data || { message: res.message || "Password changed successfully." };
      }
      throw new Error(res.error || "Failed to change password.");
    }
    return { message: "Password updated successfully." };
  },

  /**
   * Retrieve active multi-device sessions.
   * Calls GET /api/v1/account/sessions
   */
  async getSessions(): Promise<UserSession[]> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<UserSession[]>("/account/sessions");
        if (res.success && res.data) {
          return res.data;
        }
      } catch (err) {
        console.warn("API /account/sessions call failed, falling back to mock sessions:", err);
      }
    }
    return getStoredMockSessions();
  },

  /**
   * Revoke a specific session by its session ID.
   * Calls DELETE /api/v1/account/sessions/{session_id}
   */
  async revokeSession(sessionId: string): Promise<SessionRevokeResponse> {
    if (!isMockMode()) {
      const res = await apiClient.delete<SessionRevokeResponse>(`/account/sessions/${sessionId}`);
      if (res.success && res.data) {
        return res.data;
      }
      throw new Error(res.error || "Failed to revoke session.");
    }

    const current = getStoredMockSessions();
    const filtered = current.filter((s) => s.id !== sessionId);
    saveStoredMockSessions(filtered);
    return { revoked_count: 1, message: "Session revoked successfully." };
  },

  /**
   * Revoke all other active sessions, preserving the current device's session.
   * Calls POST /api/v1/account/sessions/revoke-others
   */
  async revokeOtherSessions(): Promise<SessionRevokeResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<SessionRevokeResponse>("/account/sessions/revoke-others");
      if (res.success && res.data) {
        return res.data;
      }
      throw new Error(res.error || "Failed to revoke other sessions.");
    }

    const current = getStoredMockSessions();
    const kept = current.filter((s) => s.is_current);
    saveStoredMockSessions(kept);
    return {
      revoked_count: Math.max(0, current.length - kept.length),
      message: "Other sessions revoked successfully.",
    };
  },

  /**
   * Revoke all active sessions including the current one.
   * Calls POST /api/v1/account/sessions/revoke-all
   */
  async revokeAllSessions(): Promise<SessionRevokeResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<SessionRevokeResponse>("/account/sessions/revoke-all");
      if (res.success && res.data) {
        apiClient.clearTokens();
        return res.data;
      }
      throw new Error(res.error || "Failed to revoke sessions.");
    }

    saveStoredMockSessions([]);
    apiClient.clearTokens();
    return { revoked_count: 2, message: "All sessions revoked. You must sign in again." };
  },

  /**
   * Retrieve account security summary (email verified, phone verified, sessions count, etc.).
   * Calls GET /api/v1/account/security
   */
  async getSecuritySummary(): Promise<AccountSecuritySummary> {
    if (!isMockMode()) {
      try {
        const res = await apiClient.get<AccountSecuritySummary>("/account/security");
        if (res.success && res.data) {
          return res.data;
        }
      } catch (err) {
        console.warn("API /account/security failed, falling back to mock:", err);
      }
    }

    const profile = getStoredMockProfile();
    const sessions = getStoredMockSessions();
    return {
      email_verified: profile.is_verified,
      phone_verified: !!profile.phone,
      active_sessions: sessions.length,
      has_pending_deletion: profile.has_pending_deletion,
      last_security_event_at: new Date().toISOString(),
      password_last_changed_at: "2026-08-01T14:30:00Z",
    };
  },

  /**
   * Schedule non-destructive account deletion with a 30-day grace period.
   * Calls POST /api/v1/account/deletion-request
   */
  async requestDeletion(payload: AccountDeletionPayload): Promise<AccountDeletionResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<AccountDeletionResponse>("/account/deletion-request", payload);
      if (res.success && res.data) {
        return res.data;
      }
      throw new Error(res.error || "Failed to submit deletion request.");
    }

    const profile = getStoredMockProfile();
    profile.has_pending_deletion = true;
    saveStoredMockProfile(profile);

    const now = new Date();
    const scheduled = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    return {
      id: "del-req-mock",
      status: "PENDING",
      requested_at: now.toISOString(),
      scheduled_at: scheduled.toISOString(),
      grace_period_days: 30,
    };
  },

  /**
   * Cancel pending account deletion request during the 30-day grace period.
   * Calls POST /api/v1/account/deletion-request/cancel
   */
  async cancelDeletion(): Promise<AccountDeletionCancelResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<AccountDeletionCancelResponse>("/account/deletion-request/cancel");
      if (res.success && res.data) {
        return res.data;
      }
      throw new Error(res.error || "Failed to cancel deletion request.");
    }

    const profile = getStoredMockProfile();
    profile.has_pending_deletion = false;
    saveStoredMockProfile(profile);
    return { message: "Account deletion request cancelled successfully. Your account is active." };
  },
};
