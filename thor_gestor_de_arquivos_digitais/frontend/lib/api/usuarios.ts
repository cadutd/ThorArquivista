import { apiRequest } from "@/lib/api/client";
import type { PapelUsuario, Usuario } from "@/types/domain";

export type UsuarioPayload = {
  keycloak_sub?: string | null;
  username: string;
  nome: string;
  email: string;
  papel: PapelUsuario;
  ativo: boolean;
  observacoes?: string | null;
};

export type UsuarioFilters = Partial<{
  q: string;
  username: string;
  nome: string;
  email: string;
  papel: PapelUsuario;
  ativo: string;
}>;

export type UsuarioPage = {
  items: Usuario[];
  total: number;
  limit: number;
  offset: number;
};

export type IdentityProviderName = "KEYCLOAK";

export type IdentityAccount = {
  provider: IdentityProviderName;
  provider_user_id: string;
  temporary_password: string;
  username: string;
  email: string;
};

function queryString(params: Record<string, string | number | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function listUsuariosPage({
  limit = 20,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: UsuarioFilters;
} = {}) {
  return apiRequest<UsuarioPage>(`/usuarios${queryString({ limit, offset, ...filters })}`);
}

export function getUsuario(id: string) {
  return apiRequest<Usuario>(`/usuarios/${id}`);
}

export function createUsuario(payload: UsuarioPayload) {
  return apiRequest<Usuario>("/usuarios", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUsuario(id: string, payload: Partial<UsuarioPayload>) {
  return apiRequest<Usuario>(`/usuarios/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteUsuario(id: string) {
  return apiRequest<void>(`/usuarios/${id}`, {
    method: "DELETE",
  });
}

export function createIdentityAccount(id: string, provider: IdentityProviderName = "KEYCLOAK") {
  return apiRequest<IdentityAccount>(`/usuarios/${id}/identity-accounts`, {
    method: "POST",
    body: JSON.stringify({ provider }),
  });
}
