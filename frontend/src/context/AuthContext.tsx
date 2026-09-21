import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, setAccessToken, setOnAuthExpired } from "../lib/api";
import type { TokenResponse, User } from "../lib/types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  useEffect(() => {
    setOnAuthExpired(clearSession);
    return () => setOnAuthExpired(null);
  }, [clearSession]);

  // Access tokens live only in memory, so a page reload has none. Silent
  // refresh exchanges the httponly refresh cookie for a new access token
  // without the user having to log in again. Refresh tokens are single-use
  // and rotate on every call, so this must run at most once per mount —
  // two concurrent calls (e.g. React StrictMode's double effect
  // invocation) would race for the same token and one would 401.
  const hasAttemptedRefresh = useRef(false);
  useEffect(() => {
    if (hasAttemptedRefresh.current) return;
    hasAttemptedRefresh.current = true;

    (async () => {
      try {
        const token = await api.post<TokenResponse>("/auth/refresh");
        setAccessToken(token.access_token);
        setUser(token.user);
        setStatus("authenticated");
      } catch {
        setStatus("unauthenticated");
      }
    })();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    const token = await api.postForm<TokenResponse>("/auth/login", form);
    setAccessToken(token.access_token);
    setUser(token.user);
    setStatus("authenticated");
  }, []);

  const signup = useCallback(
    async (email: string, password: string, fullName: string) => {
      await api.post<User>("/auth/signup", { email, password, full_name: fullName });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const updateUser = useCallback((next: User) => setUser(next), []);

  const value = useMemo(
    () => ({ status, user, login, signup, logout, updateUser }),
    [status, user, login, signup, logout, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
