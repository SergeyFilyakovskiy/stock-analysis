import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { authApi } from "./api";
import { setTokens, clearTokens, getAccessToken } from "./queryClient";
import type { ProfileResponse } from "@shared/schema";

interface AuthState {
  user: ProfileResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; first_name?: string; last_name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  /** Called after OAuth redirect — tokens come as query params */
  handleOAuthCallback: (access: string, refresh: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    try {
      const profile = await authApi.me();
      setUser(profile);
    } catch {
      setUser(null);
      clearTokens();
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    await fetchProfile();
  }, [fetchProfile]);

  const register = useCallback(async (data: { email: string; password: string; first_name?: string; last_name?: string }) => {
    const tokens = await authApi.register(data);
    setTokens(tokens.access_token, tokens.refresh_token);
    await fetchProfile();
  }, [fetchProfile]);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    clearTokens();
    setUser(null);
  }, []);

  const handleOAuthCallback = useCallback(async (access: string, refresh: string) => {
    setTokens(access, refresh);
    await fetchProfile();
  }, [fetchProfile]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        handleOAuthCallback,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
