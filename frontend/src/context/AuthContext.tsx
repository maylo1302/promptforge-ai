import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, session } from "../lib/api";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (firstName: string, lastName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | null>(null);

type TokenResponse = { access_token: string; csrf_token: string };

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);
  const establish = async (result: TokenResponse) => { session.set(result.access_token, result.csrf_token); setUser(await api<User>("/users/me")); };
  const refreshUser = async () => { setUser(await api<User>("/users/me")); };

  useEffect(() => { void (async () => { try { await establish(await api<TokenResponse>("/auth/refresh", { method: "POST" })); } catch { session.clear(); } finally { setLoading(false); } })(); }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user, isLoading, refreshUser,
    login: async (email, password) => establish(await api<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })),
    register: async (first_name, last_name, email, password) => { await api("/auth/register", { method: "POST", body: JSON.stringify({ first_name, last_name, email, password }) }); await establish(await api<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })); },
    logout: async () => { try { await api("/auth/logout", { method: "POST" }); } finally { session.clear(); setUser(null); } },
  }), [user, isLoading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth musi działać wewnątrz AuthProvider.");
  return context;
};

