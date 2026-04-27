import { config, keycloakRealmUrl } from "@/lib/config";
import { decodeJwtClaims, storeSession } from "@/lib/auth/session";

const AUTH_STATE_KEY = "thor.auth.state";
const AUTH_VERIFIER_KEY = "thor.auth.verifier";
const AUTH_NEXT_KEY = "thor.auth.next";

function base64UrlEncode(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";

  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });

  return window
    .btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function sha256(value: string) {
  return window.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
}

function randomString() {
  const bytes = new Uint8Array(32);
  window.crypto.getRandomValues(bytes);
  return base64UrlEncode(bytes.buffer);
}

export async function startLogin(nextPath?: string | null) {
  const state = randomString();
  const verifier = randomString();
  const challenge = base64UrlEncode(await sha256(verifier));

  window.sessionStorage.setItem(AUTH_STATE_KEY, state);
  window.sessionStorage.setItem(AUTH_VERIFIER_KEY, verifier);
  if (nextPath) {
    window.sessionStorage.setItem(AUTH_NEXT_KEY, nextPath);
  } else {
    window.sessionStorage.removeItem(AUTH_NEXT_KEY);
  }

  const params = new URLSearchParams({
    client_id: config.keycloakClientId,
    redirect_uri: `${config.appUrl}/auth/callback`,
    response_type: "code",
    scope: "openid profile email",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });

  window.location.assign(
    `${keycloakRealmUrl()}/protocol/openid-connect/auth?${params.toString()}`,
  );
}

export async function completeLogin(code: string, state: string) {
  const expectedState = window.sessionStorage.getItem(AUTH_STATE_KEY);
  const verifier = window.sessionStorage.getItem(AUTH_VERIFIER_KEY);

  if (!expectedState || !verifier || expectedState !== state) {
    throw new Error("Estado de autenticação inválido.");
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: config.keycloakClientId,
    redirect_uri: `${config.appUrl}/auth/callback`,
    code,
    code_verifier: verifier,
  });

  const response = await fetch(
    `${keycloakRealmUrl()}/protocol/openid-connect/token`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    },
  );

  if (!response.ok) {
    throw new Error("Não foi possível concluir a autenticação.");
  }

  const token = (await response.json()) as {
    access_token: string;
    refresh_token?: string;
    id_token?: string;
    expires_in: number;
  };

  const session = {
    accessToken: token.access_token,
    refreshToken: token.refresh_token,
    idToken: token.id_token,
    expiresAt: Date.now() + token.expires_in * 1000,
    claims: decodeJwtClaims(token.access_token),
  };

  storeSession(session);
  window.sessionStorage.removeItem(AUTH_STATE_KEY);
  window.sessionStorage.removeItem(AUTH_VERIFIER_KEY);

  return session;
}

export function consumeLoginRedirectPath() {
  const nextPath = window.sessionStorage.getItem(AUTH_NEXT_KEY);
  window.sessionStorage.removeItem(AUTH_NEXT_KEY);
  return nextPath && nextPath.startsWith("/") && !nextPath.startsWith("//")
    ? nextPath
    : "/dashboard";
}

export function keycloakLogoutUrl(idToken?: string) {
  const params = new URLSearchParams({
    client_id: config.keycloakClientId,
    post_logout_redirect_uri: `${config.appUrl}/login`,
  });

  if (idToken) {
    params.set("id_token_hint", idToken);
  }

  return `${keycloakRealmUrl()}/protocol/openid-connect/logout?${params.toString()}`;
}
