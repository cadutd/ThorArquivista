export type AuthSession = {
  accessToken: string;
  refreshToken?: string;
  idToken?: string;
  expiresAt: number;
  claims?: Record<string, unknown>;
};

const SESSION_KEY = "thor.auth.session";
export const SESSION_EXPIRED_REASON = "sessao-expirada";

export function getStoredSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function storeSession(session: AuthSession) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  window.dispatchEvent(new CustomEvent("thor.auth.session-changed", { detail: session }));
}

export function clearStoredSession() {
  window.localStorage.removeItem(SESSION_KEY);
  window.dispatchEvent(new CustomEvent("thor.auth.session-changed", { detail: null }));
}

export function redirectToLoginAfterSessionLoss() {
  if (typeof window === "undefined") {
    return;
  }

  clearStoredSession();

  if (window.location.pathname === "/login") {
    return;
  }

  const params = new URLSearchParams({
    motivo: SESSION_EXPIRED_REASON,
  });
  const currentPath = `${window.location.pathname}${window.location.search}`;

  if (currentPath && currentPath !== "/") {
    params.set("next", currentPath);
  }

  window.location.replace(`/login?${params.toString()}`);
}

export function isSessionActive(session: AuthSession | null) {
  if (!session) {
    return false;
  }

  return session.expiresAt > Date.now() + 30_000;
}

export function decodeJwtClaims(token: string): Record<string, unknown> | undefined {
  const [, payload] = token.split(".");
  if (!payload) {
    return undefined;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = window.atob(normalized);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return undefined;
  }
}
