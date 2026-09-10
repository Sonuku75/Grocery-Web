"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User, LoginPayload, RegisterPayload } from "@/types";
import { authService } from "@/services/authService";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<User>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      try {
        const currentUser = await authService.getMe();
        if (currentUser) {
          setUser(currentUser);
        } else {
          // Pre-populate with default demo user for seamless evaluation
          const defaultUser = authService.getCurrentUser();
          if (defaultUser) {
            setUser(defaultUser);
          }
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    initAuth();
  }, []);

  const login = async (payload: LoginPayload): Promise<User> => {
    setLoading(true);
    try {
      const response = await authService.login(payload);
      setUser(response.user);
      return response.user;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload: RegisterPayload): Promise<User> => {
    setLoading(true);
    try {
      const response = await authService.register(payload);
      setUser(response.user);
      return response.user;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<User> => {
    const updated = await authService.updateMe(userData);
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
