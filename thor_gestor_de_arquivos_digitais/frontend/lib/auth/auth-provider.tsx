"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  clearStoredSession,
  getStoredSession,
  isSessionActive,
  redirectToLoginAfterSessionLoss,
  type AuthSession,
} from "@/lib/auth/session";
import { keycloakLogoutUrl, startLogin } from "@/lib/auth/oidc";

type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (nextPath?: string | null) => Promise<void>;
  logout: () => void;
  setAuthenticatedSession: (session: AuthSession) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    queueMicrotask(() => {
      if (!isMounted) {
        return;
      }

      const stored = getStoredSession();
      if (stored && !isSessionActive(stored)) {
        redirectToLoginAfterSessionLoss();
        setSession(null);
      } else {
        setSession(stored);
      }
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!session) {
      return;
    }

    const timeoutMs = Math.max(session.expiresAt - Date.now() - 30_000, 0);
    const timeoutId = window.setTimeout(() => {
      setSession(null);
      redirectToLoginAfterSessionLoss();
    }, timeoutMs);

    return () => window.clearTimeout(timeoutId);
  }, [session]);

  const login = useCallback(async (nextPath?: string | null) => {
    await startLogin(nextPath);
  }, []);

  const setAuthenticatedSession = useCallback((nextSession: AuthSession) => {
    setSession(nextSession);
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    const idToken = session?.idToken;
    clearStoredSession();
    setSession(null);
    window.location.assign(keycloakLogoutUrl(idToken));
  }, [session?.idToken]);

  const value = useMemo(
    () => ({
      session,
      isAuthenticated: isSessionActive(session),
      isLoading,
      login,
      logout,
      setAuthenticatedSession,
    }),
    [isLoading, login, logout, session, setAuthenticatedSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  }

  return context;
}
