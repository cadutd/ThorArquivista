import { apiRequest } from "@/lib/api/client";
import type {
  CopiaDigital,
  EventoPreservacao,
  InstrumentoCampo,
  InstrumentoPesquisaSchema,
  InstrumentoPesquisa,
  InstrumentoRegistro,
  InstrumentoRegistroPage,
  StatusInstrumentoRegistro,
  MidiaArmazenamento,
  StatusInstrumentoPesquisa,
  TipoCampoInstrumento,
  TipoInstrumentoPesquisa,
  UnidadeAcondicionamento,
  VisibilidadeInstrumentoPesquisa,
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

export type InstrumentoPesquisaPayload = {
  nome: string;
  tipo: TipoInstrumentoPesquisa;
  descricao?: string | null;
  status: StatusInstrumentoPesquisa;
  visibilidade: VisibilidadeInstrumentoPesquisa;
  responsavel?: string | null;
};

export type InstrumentoPesquisaFilters = Partial<{
  tipo: TipoInstrumentoPesquisa;
  status: StatusInstrumentoPesquisa;
}>;

export type InstrumentoCampoPayload = {
  nome: string;
  chave: string;
  tipo: TipoCampoInstrumento;
  ordem: number;
  obrigatorio: boolean;
  multiplo: boolean;
  valor_padrao?: string | null;
  placeholder?: string | null;
  ajuda?: string | null;
  aparece_cadastro: boolean;
  aparece_listagem: boolean;
  aparece_busca: boolean;
  filtro_avancado: boolean;
  facetavel: boolean;
  ordenavel: boolean;
  opcoes?: unknown;
  validacoes?: unknown;
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

export type InstrumentoPesquisaPage = {
  items: InstrumentoPesquisa[];
  total: number;
  limit: number;
  offset: number;
};

export type DashboardStats = {
  total_unidades: number;
  aips_digitais: number;
  midias_ativas: number;
  alertas: number;
  enderecamento: {
    locais: number;
    zonas: number;
    estruturas: number;
    compartimentos: number;
    posicoes: number;
    posicoes_livres: number;
    posicoes_ocupadas: number;
    posicoes_inativas: number;
    taxa_ocupacao: number;
  };
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

export function listInstrumentosPesquisa({
  limit = 100,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: InstrumentoPesquisaFilters;
} = {}) {
  return apiRequest<InstrumentoPesquisaPage>(
    `/instrumentos-pesquisa${queryString({ limit, offset, ...filters })}`,
  );
}

export function createInstrumentoPesquisa(payload: InstrumentoPesquisaPayload) {
  return apiRequest<InstrumentoPesquisa>("/instrumentos-pesquisa", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateInstrumentoPesquisa(id: string, payload: Partial<InstrumentoPesquisaPayload>) {
  return apiRequest<InstrumentoPesquisa>(`/instrumentos-pesquisa/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteInstrumentoPesquisa(id: string) {
  return apiRequest<void>(`/instrumentos-pesquisa/${id}`, {
    method: "DELETE",
  });
}

export function listInstrumentoCampos(instrumentoId: string) {
  return apiRequest<InstrumentoCampo[]>(`/instrumentos-pesquisa/${instrumentoId}/campos`);
}

export function createInstrumentoCampo(instrumentoId: string, payload: InstrumentoCampoPayload) {
  return apiRequest<InstrumentoCampo>(`/instrumentos-pesquisa/${instrumentoId}/campos`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateInstrumentoCampo(instrumentoId: string, campoId: string, payload: Partial<InstrumentoCampoPayload>) {
  return apiRequest<InstrumentoCampo>(`/instrumentos-pesquisa/${instrumentoId}/campos/${campoId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteInstrumentoCampo(instrumentoId: string, campoId: string) {
  return apiRequest<void>(`/instrumentos-pesquisa/${instrumentoId}/campos/${campoId}`, {
    method: "DELETE",
  });
}

export function reorderInstrumentoCampos(instrumentoId: string, campos: Array<{ id: string; ordem: number }>) {
  return apiRequest<InstrumentoCampo[]>(`/instrumentos-pesquisa/${instrumentoId}/campos/reordenar`, {
    method: "PATCH",
    body: JSON.stringify({ campos }),
  });
}

export function getInstrumentoPesquisaSchema(instrumentoId: string) {
  return apiRequest<InstrumentoPesquisaSchema>(`/instrumentos-pesquisa/${instrumentoId}/schema`);
}

export type InstrumentoRegistroPayload = {
  dados: Record<string, unknown>;
  unidade_acondicionamento_ids?: number[];
  registro_descritivo_ids?: string[];
  status?: StatusInstrumentoRegistro;
};

export type InstrumentoRegistroFilters = Partial<{
  status: StatusInstrumentoRegistro;
}>;

export function createInstrumentoRegistro(instrumentoId: string, payload: InstrumentoRegistroPayload) {
  return apiRequest<InstrumentoRegistro>(`/instrumentos-pesquisa/${instrumentoId}/registros`, {
    method: "POST",
    body: JSON.stringify({
      unidade_acondicionamento_ids: [],
      registro_descritivo_ids: [],
      status: "ATIVO",
      ...payload,
    }),
  });
}

export function listInstrumentoRegistros(
  instrumentoId: string,
  {
    pageSize = 25,
    cursor,
    filters = {},
  }: {
    pageSize?: number;
    cursor?: string | null;
    filters?: InstrumentoRegistroFilters;
  } = {},
) {
  return apiRequest<InstrumentoRegistroPage>(
    `/instrumentos-pesquisa/${instrumentoId}/registros${queryString({
      page_size: pageSize,
      cursor,
      ...filters,
    })}`,
  );
}

export function searchInstrumentoRegistros(
  instrumentoId: string,
  {
    q,
    pageSize = 25,
    cursor,
  }: {
    q: string;
    pageSize?: number;
    cursor?: string | null;
  },
) {
  return apiRequest<InstrumentoRegistroPage>(`/instrumentos-pesquisa/${instrumentoId}/buscar`, {
    method: "POST",
    body: JSON.stringify({
      q,
      page_size: pageSize,
      cursor: cursor ?? null,
    }),
  });
}

export function getInstrumentoRegistro(instrumentoId: string, registroId: string) {
  return apiRequest<InstrumentoRegistro>(`/instrumentos-pesquisa/${instrumentoId}/registros/${registroId}`);
}

export function updateInstrumentoRegistro(instrumentoId: string, registroId: string, payload: InstrumentoRegistroPayload) {
  return apiRequest<InstrumentoRegistro>(`/instrumentos-pesquisa/${instrumentoId}/registros/${registroId}`, {
    method: "PUT",
    body: JSON.stringify({
      unidade_acondicionamento_ids: [],
      registro_descritivo_ids: [],
      status: "ATIVO",
      ...payload,
    }),
  });
}

export function deleteInstrumentoRegistro(instrumentoId: string, registroId: string) {
  return apiRequest<void>(`/instrumentos-pesquisa/${instrumentoId}/registros/${registroId}`, {
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
  return apiRequest<CopiaDigital>(`/unidades-acondicionamento/${unidadeId}/copias`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEventos(unidadeId: number) {
  return apiRequest<EventoPreservacao[]>(
    `/unidades-acondicionamento/${unidadeId}/eventos-preservacao`,
  );
}
