import { config } from "@/lib/config";
import { refreshLogin } from "@/lib/auth/oidc";
import {
  getStoredSession,
  isSessionActive,
  redirectToLoginAfterSessionLoss,
  type AuthSession,
} from "@/lib/auth/session";

type ApiRequestOptions = RequestInit & {
  authenticated?: boolean;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const session = await getActiveSession();
  const headers = new Headers(options.headers);

  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.authenticated !== false && session && isSessionActive(session)) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  } else if (options.authenticated !== false) {
    redirectToLoginAfterSessionLoss();
    throw new Error("Sua sessão expirou. Entre novamente para continuar.");
  }

  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      redirectToLoginAfterSessionLoss();
      throw new Error("Sua sessão expirou. Entre novamente para continuar.");
    }

    const detail = await response.text();
    throw new Error(detail || `Erro ${response.status} na API.`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function getActiveSession(): Promise<AuthSession | null> {
  const session = getStoredSession();

  if (!session || isSessionActive(session)) {
    return session;
  }

  if (!session.refreshToken) {
    return session;
  }

  try {
    return await refreshLogin(session.refreshToken);
  } catch {
    return session;
  }
}
