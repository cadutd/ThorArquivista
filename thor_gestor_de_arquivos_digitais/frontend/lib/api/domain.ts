import { apiRequest } from "@/lib/api/client";
import type {
  EventoPreservacao,
  MidiaArmazenamento,
  UnidadeAcondicionamento,
} from "@/types/domain";

export type UnidadePayload = {
  identificador: string;
  titulo: string;
  descricao?: string | null;
  tipo_suporte: string;
  tipo_unidade: string;
  nivel_acesso: string;
  status: string;
  id_unidade_pai?: number | null;
  id_representa?: number | null;
};

export type UnidadeFilters = Partial<{
  q: string;
  identificador: string;
  titulo: string;
  descricao: string;
  tipo_suporte: string;
  tipo_unidade: string;
  nivel_acesso: string;
  status: string;
  criado_em_de: string;
  criado_em_ate: string;
  atualizado_em_de: string;
  atualizado_em_ate: string;
}>;

export type MidiaPayload = {
  nome: string;
  tipo: string;
  descricao?: string | null;
  ativo: boolean;
};

export type CopiaDigitalPayload = {
  id_midia_armazenamento: number;
  uri_copia: string;
  funcao_copia: string;
  status_copia: string;
  algoritmo_fixidez?: string | null;
  hash_fixidez?: string | null;
  ultima_verificacao_em?: string | null;
};

export type UnidadePage = {
  items: UnidadeAcondicionamento[];
  total: number;
  limit: number;
  offset: number;
};

export type DashboardStats = {
  total_unidades: number;
  aips_digitais: number;
  midias_ativas: number;
  alertas: number;
  unidades_por_suporte: Array<{
    tipo_suporte: string;
    total: number;
  }>;
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

export function listUnidadesPage({
  limit = 20,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: UnidadeFilters;
} = {}) {
  return apiRequest<UnidadePage>(
    `/unidades-acondicionamento${queryString({ limit, offset, ...filters })}`,
  );
}

export async function listUnidades(options: {
  limit?: number;
  offset?: number;
  filters?: UnidadeFilters;
} = {}) {
  const page = await listUnidadesPage(options);
  return page.items;
}

export function createUnidade(payload: UnidadePayload) {
  return apiRequest<UnidadeAcondicionamento>("/unidades-acondicionamento", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUnidade(id: number, payload: Partial<UnidadePayload>) {
  return apiRequest<UnidadeAcondicionamento>(`/unidades-acondicionamento/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteUnidade(id: number) {
  return apiRequest<void>(`/unidades-acondicionamento/${id}`, {
    method: "DELETE",
  });
}

export function listMidias() {
  return apiRequest<MidiaArmazenamento[]>("/midias-armazenamento");
}

export function getDashboardStats() {
  return apiRequest<DashboardStats>("/dashboard");
}

export function createMidia(payload: MidiaPayload) {
  return apiRequest<MidiaArmazenamento>("/midias-armazenamento", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createCopiaDigital(
  unidadeId: number,
  payload: CopiaDigitalPayload,
) {
  return apiRequest(`/unidades-acondicionamento/${unidadeId}/copias`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEventos(unidadeId: number) {
  return apiRequest<EventoPreservacao[]>(
    `/unidades-acondicionamento/${unidadeId}/eventos-preservacao`,
  );
}
