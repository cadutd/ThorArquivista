import { apiRequest } from "@/lib/api/client";
import type { AcaoPermissao, Perfil, Permissao } from "@/types/domain";

export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type PerfilPayload = {
  codigo: string;
  nome: string;
  descricao?: string | null;
  ativo: boolean;
  sistema: boolean;
  permissao_ids: string[];
};

export type PermissaoFilters = Partial<{
  q: string;
  codigo: string;
  nome: string;
  modulo: string;
  funcao: string;
  acao: AcaoPermissao;
  ativo: string;
}>;

export type PerfilFilters = Partial<{
  q: string;
  codigo: string;
  nome: string;
  ativo: string;
  sistema: string;
}>;

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

export function listPermissoesPage({
  limit = 20,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: PermissaoFilters;
} = {}) {
  return apiRequest<Page<Permissao>>(`/permissoes${queryString({ limit, offset, ...filters })}`);
}

export function getPermissao(id: string) {
  return apiRequest<Permissao>(`/permissoes/${id}`);
}

export function listPerfisPage({
  limit = 20,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: PerfilFilters;
} = {}) {
  return apiRequest<Page<Perfil>>(`/perfis${queryString({ limit, offset, ...filters })}`);
}

export function getPerfil(id: string) {
  return apiRequest<Perfil>(`/perfis/${id}`);
}

export function createPerfil(payload: PerfilPayload) {
  return apiRequest<Perfil>("/perfis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePerfil(id: string, payload: Partial<PerfilPayload>) {
  return apiRequest<Perfil>(`/perfis/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deletePerfil(id: string) {
  return apiRequest<void>(`/perfis/${id}`, { method: "DELETE" });
}
