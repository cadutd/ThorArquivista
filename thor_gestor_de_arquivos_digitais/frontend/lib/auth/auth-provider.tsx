"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { clearStoredSession, getStoredSession, isSessionActive, type AuthSession } from "@/lib/auth/session";
import { keycloakLogoutUrl, startLogin } from "@/lib/auth/oidc";

type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
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
      setSession(isSessionActive(stored) ? stored : null);
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async () => {
    await startLogin();
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
