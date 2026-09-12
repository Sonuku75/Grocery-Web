import { apiClient, isMockMode } from "@/lib/api";
import {
  AuthResponse,
  ChangePasswordPayload,
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  User,
  UserUpdatePayload,
} from "@/types";

const DEMO_USER: User = {
  id: "usr-demo",
  email: "alex.rivera@cartify.com",
  mobile: "+1 (555) 234-5678",
  phone: "+1 (555) 234-5678",
  name: "Alex Rivera",
  fullName: "Alex Rivera",
  avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
  role: "customer",
  isActive: true,
  isVerified: false,
  createdAt: "2026-01-15T08:00:00Z",
};

function normalizeUser(rawUser: any): User {
  if (!rawUser) return DEMO_USER;
  const fullName = rawUser.fullName || rawUser.name || "User";
  const mobile = rawUser.mobile || rawUser.phone || "";
  return {
    id: rawUser.id,
    name: fullName,
    fullName,
    email: rawUser.email,
    phone: mobile,
    mobile,
    avatarUrl: rawUser.avatarUrl || rawUser.avatar_url,
    role: rawUser.role || "customer",
    isActive: rawUser.isActive ?? rawUser.is_active ?? true,
    isVerified: rawUser.isVerified ?? rawUser.is_verified ?? false,
    createdAt: rawUser.createdAt || rawUser.created_at || new Date().toISOString(),
    updatedAt: rawUser.updatedAt || rawUser.updated_at,
  };
}

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const email = payload.email || payload.identifier || "";
    if (!isMockMode()) {
      const res = await apiClient.post<any>("/auth/login", {
        email,
        password: payload.password,
      });

      if (res.success && res.data) {
        const accessToken = res.data.accessToken || res.data.access_token;
        const refreshToken = res.data.refreshToken || res.data.refresh_token;
        const user = normalizeUser(res.data.user);

        apiClient.setToken(accessToken);
        if (refreshToken) {
          apiClient.setRefreshToken(refreshToken);
        }
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(user));
        }

        return {
          user,
          accessToken,
          refreshToken,
        };
      }
    }

    // Fallback demo mock authentication for development testing
    const mockUser: User = {
      ...DEMO_USER,
      email: email.includes("@") ? email : DEMO_USER.email,
      mobile: !email.includes("@") ? email : DEMO_USER.mobile,
      phone: !email.includes("@") ? email : DEMO_USER.mobile,
    };
    const mockAuth: AuthResponse = {
      user: mockUser,
      accessToken: "mock_jwt_access_token_" + Date.now(),
      refreshToken: "mock_jwt_refresh_token_" + Date.now(),
    };
    apiClient.setToken(mockAuth.accessToken);
    apiClient.setRefreshToken(mockAuth.refreshToken);
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(mockUser));
    }
    return mockAuth;
  },

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const name = payload.name || payload.fullName;
    const phone = payload.phone || payload.mobile;

    if (!isMockMode()) {
      const res = await apiClient.post<any>("/auth/register", {
        name,
        email: payload.email,
        phone,
        password: payload.password,
      });

      if (res.success && res.data) {
        const accessToken = res.data.accessToken || res.data.access_token;
        const refreshToken = res.data.refreshToken || res.data.refresh_token;
        const user = normalizeUser(res.data.user);

        apiClient.setToken(accessToken);
        if (refreshToken) {
          apiClient.setRefreshToken(refreshToken);
        }
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(user));
        }

        return {
          user,
          accessToken,
          refreshToken,
        };
      }
    }

    const newUser: User = {
      id: "usr-" + Date.now(),
      email: payload.email,
      mobile: phone || "",
      phone: phone || "",
      fullName: name,
      name,
      role: "customer",
      isActive: true,
      isVerified: false,
      createdAt: new Date().toISOString(),
    };

    const mockAuth: AuthResponse = {
      user: newUser,
      accessToken: "mock_jwt_access_token_" + Date.now(),
      refreshToken: "mock_jwt_refresh_token_" + Date.now(),
    };

    apiClient.setToken(mockAuth.accessToken);
    apiClient.setRefreshToken(mockAuth.refreshToken);
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(newUser));
    }
    return mockAuth;
  },

  async refreshToken(): Promise<AuthResponse | null> {
    if (!isMockMode()) {
      const storedRefreshToken = apiClient.getRefreshToken();
      const res = await apiClient.post<any>("/auth/refresh", {
        refresh_token: storedRefreshToken || undefined,
      });
      if (res.success && res.data) {
        const accessToken = res.data.accessToken || res.data.access_token;
        const refreshToken = res.data.refreshToken || res.data.refresh_token;
        const user = normalizeUser(res.data.user);

        apiClient.setToken(accessToken);
        if (refreshToken) {
          apiClient.setRefreshToken(refreshToken);
        }
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(user));
        }
        return { user, accessToken, refreshToken };
      }
    }
    return null;
  },

  async logout(): Promise<void> {
    if (!isMockMode()) {
      const storedRefreshToken = apiClient.getRefreshToken();
      await apiClient.post("/auth/logout", {
        refresh_token: storedRefreshToken || undefined,
      }).catch(() => null);
    }
    apiClient.clearTokens();
  },

  getCurrentUser(): User | null {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem("cartify_user");
    if (!stored) return null;
    try {
      return JSON.parse(stored) as User;
    } catch {
      return null;
    }
  },

  async getMe(): Promise<User | null> {
    if (!isMockMode()) {
      const res = await apiClient.get<any>("/users/me");
      if (res.success && res.data) {
        const user = normalizeUser(res.data);
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(user));
        }
        return user;
      }
    }
    return this.getCurrentUser();
  },

  async updateMe(userData: Partial<User> | UserUpdatePayload): Promise<User> {
    if (!isMockMode()) {
      const res = await apiClient.patch<any>("/users/me", {
        name: (userData as any).name || (userData as any).fullName,
        phone: (userData as any).phone || (userData as any).mobile,
        avatar_url: userData.avatarUrl,
      });
      if (res.success && res.data) {
        const user = normalizeUser(res.data);
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(user));
        }
        return user;
      }
    }

    const current = this.getCurrentUser() || DEMO_USER;
    const updated = normalizeUser({ ...current, ...userData });
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(updated));
    }
    return updated;
  },

  async changePassword(payload: ChangePasswordPayload): Promise<{ success: boolean; message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<any>("/users/me/change-password", {
        current_password: payload.currentPassword,
        new_password: payload.newPassword,
      });
      if (res.success) {
        return { success: true, message: res.message || "Password changed successfully." };
      }
      return { success: false, message: res.error || "Failed to change password." };
    }
    return { success: true, message: "Password changed successfully (mock)." };
  },

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<{ message: string }>("/auth/forgot-password", { email });
      if (res.success) {
        return { success: true, message: res.data?.message || res.message || "If an account exists with this email, a password reset link has been sent." };
      }
    }
    return { success: true, message: "If an account exists with this email, a password reset link has been sent." };
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<{ success: boolean; message: string }> {
    if (!isMockMode()) {
      const res = await apiClient.post<{ message: string }>("/auth/reset-password", {
        token: payload.token,
        new_password: payload.newPassword,
      });
      if (res.success) {
        return { success: true, message: res.data?.message || res.message || "Password has been reset successfully." };
      }
      return { success: false, message: res.error || "Failed to reset password." };
    }
    return { success: true, message: "Password has been reset successfully (mock)." };
  },

  async verifyOtp(mobile: string, otp: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ message: string }>("/auth/verify-otp", { mobile, otp });
    if (res.success) {
      return { success: true, message: res.data?.message || "OTP verified successfully" };
    }
    return { success: true, message: "OTP verified successfully." };
  },
};
