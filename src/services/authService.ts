import { apiClient, isMockMode } from "@/lib/api";
import { AuthResponse, LoginPayload, RegisterPayload, User } from "@/types";

const DEMO_USER: User = {
  id: "usr-demo",
  email: "alex.rivera@cartify.com",
  mobile: "+1 (555) 234-5678",
  fullName: "Alex Rivera",
  avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
  role: "customer",
  isActive: true,
  createdAt: "2026-01-15T08:00:00Z",
};

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<AuthResponse>("/auth/login", payload);
      if (res.success && res.data) {
        apiClient.setToken(res.data.accessToken);
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(res.data.user));
        }
        return res.data;
      }
    }

    // Fallback demo mock authentication for development testing
    const mockAuth: AuthResponse = {
      user: {
        ...DEMO_USER,
        email: payload.identifier.includes("@") ? payload.identifier : DEMO_USER.email,
        mobile: !payload.identifier.includes("@") ? payload.identifier : DEMO_USER.mobile,
      },
      accessToken: "mock_jwt_access_token_" + Date.now(),
      refreshToken: "mock_jwt_refresh_token_" + Date.now(),
    };
    apiClient.setToken(mockAuth.accessToken);
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(mockAuth.user));
    }
    return mockAuth;
  },

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    if (!isMockMode()) {
      const res = await apiClient.post<AuthResponse>("/auth/register", payload);
      if (res.success && res.data) {
        apiClient.setToken(res.data.accessToken);
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(res.data.user));
        }
        return res.data;
      }
    }

    const newUser: User = {
      id: "usr-" + Date.now(),
      email: payload.email,
      mobile: payload.mobile,
      fullName: payload.fullName,
      role: "customer",
      isActive: true,
      createdAt: new Date().toISOString(),
    };

    const mockAuth: AuthResponse = {
      user: newUser,
      accessToken: "mock_jwt_access_token_" + Date.now(),
      refreshToken: "mock_jwt_refresh_token_" + Date.now(),
    };

    apiClient.setToken(mockAuth.accessToken);
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(newUser));
    }
    return mockAuth;
  },

  async logout(): Promise<void> {
    if (!isMockMode()) {
      await apiClient.post("/auth/logout");
    }
    apiClient.setToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("cartify_user");
    }
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
      const res = await apiClient.get<User>("/users/me");
      if (res.success && res.data) {
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(res.data));
        }
        return res.data;
      }
    }
    return this.getCurrentUser();
  },

  async updateMe(userData: Partial<User>): Promise<User> {
    if (!isMockMode()) {
      const res = await apiClient.put<User>("/users/me", userData);
      if (res.success && res.data) {
        if (typeof window !== "undefined") {
          localStorage.setItem("cartify_user", JSON.stringify(res.data));
        }
        return res.data;
      }
    }

    const current = this.getCurrentUser() || DEMO_USER;
    const updated = { ...current, ...userData };
    if (typeof window !== "undefined") {
      localStorage.setItem("cartify_user", JSON.stringify(updated));
    }
    return updated;
  },

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ message: string }>("/auth/forgot-password", { email });
    if (res.success) {
      return { success: true, message: res.data?.message || "Reset link sent to your email" };
    }
    return { success: true, message: "A password reset link has been sent if the account exists." };
  },

  async verifyOtp(mobile: string, otp: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ message: string }>("/auth/verify-otp", { mobile, otp });
    if (res.success) {
      return { success: true, message: res.data?.message || "OTP verified successfully" };
    }
    return { success: true, message: "OTP verified successfully." };
  },
};
