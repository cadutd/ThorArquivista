import { apiRequest } from "@/lib/api/client";
import type { EntidadeProdutora, EntidadeProdutoraTree, TipoEntidadeProdutora } from "@/types/domain";

export type EntidadeProdutoraPayload = {
  nome: string;
  sigla?: string | null;
  codigo_referencia?: string | null;
  tipo_entidade: TipoEntidadeProdutora;
  natureza_juridica?: string | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  entidade_ativa: boolean;
  historico?: string | null;
  competencias_funcoes?: string | null;
  observacoes?: string | null;
  email?: string | null;
  telefone?: string | null;
  site?: string | null;
  endereco_logradouro?: string | null;
  endereco_numero?: string | null;
  endereco_complemento?: string | null;
  endereco_bairro?: string | null;
  endereco_municipio?: string | null;
  endereco_uf?: string | null;
  endereco_cep?: string | null;
  endereco_pais?: string | null;
  id_entidade_superior?: string | null;
};

export type EntidadeProdutoraFilters = Partial<{
  q: string;
  nome: string;
  sigla: string;
  tipo_entidade: TipoEntidadeProdutora;
  entidade_ativa: string;
  id_entidade_superior: string;
}>;

export type EntidadeProdutoraPage = {
  items: EntidadeProdutora[];
  total: number;
  limit: number;
  offset: number;
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

export function listEntidadesProdutorasPage({
  limit = 20,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: EntidadeProdutoraFilters;
} = {}) {
  return apiRequest<EntidadeProdutoraPage>(
    `/entidades-produtoras${queryString({ limit, offset, ...filters })}`,
  );
}

export async function listEntidadesProdutoras() {
  const page = await listEntidadesProdutorasPage({ limit: 100 });
  return page.items;
}

export function getEntidadeProdutora(id: string) {
  return apiRequest<EntidadeProdutora>(`/entidades-produtoras/${id}`);
}

export function createEntidadeProdutora(payload: EntidadeProdutoraPayload) {
  return apiRequest<EntidadeProdutora>("/entidades-produtoras", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEntidadeProdutora(id: string, payload: Partial<EntidadeProdutoraPayload>) {
  return apiRequest<EntidadeProdutora>(`/entidades-produtoras/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteEntidadeProdutora(id: string) {
  return apiRequest<void>(`/entidades-produtoras/${id}`, {
    method: "DELETE",
  });
}

export function getEntidadesProdutorasTree(params: Record<string, string | undefined | null> = {}) {
  return apiRequest<EntidadeProdutoraTree[]>(
    `/entidades-produtoras/arvore${queryString(params)}`,
  );
}
