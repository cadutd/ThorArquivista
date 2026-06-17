import { apiRequest } from "@/lib/api/client";
import type {
  CopiaDigital,
  CategoriaIntegridadeMidia,
  EventoMidiaArmazenamento,
  EventoPreservacao,
  InstrumentoCampo,
  InstrumentoPesquisaSchema,
  InstrumentoPesquisa,
  InstrumentoRegistro,
  InstrumentoRegistroPage,
  IntegridadePainel,
  IntegridadeResumo,
  MigracaoMidia,
  ResultadoVerificacaoIntegridade,
  StatusInstrumentoRegistro,
  MidiaArmazenamento,
  StatusMigracaoMidia,
  StatusMidiaArmazenamento,
  StatusInstrumentoPesquisa,
  TipoCampoInstrumento,
  TipoInstrumentoPesquisa,
  TipoMidiaArmazenamento,
  UnidadeAcondicionamento,
  VerificacaoIntegridadeMidia,
  VisibilidadeInstrumentoPesquisa,
} from "@/types/domain";

export type UnidadePayload = {
  identificador: string;
  titulo: string;
  descricao?: string | null;
  produtor?: string | null;
  unidade?: string | null;
  data_limite?: string | null;
  codigo_classificacao?: string | null;
  assunto?: string | null;
  codigo_barra?: string | null;
  informacoes_pacote?: string | null;
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
  produtor: string;
  unidade: string;
  data_limite: string;
  codigo_classificacao: string;
  assunto: string;
  codigo_barra: string;
  informacoes_pacote: string;
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
  tipo_midia_id: string;
  descricao?: string | null;
  ativo?: boolean;
  status?: StatusMidiaArmazenamento;
  data_aquisicao?: string | null;
  data_inicio_uso?: string | null;
  data_validade?: string | null;
  ultima_checagem_integridade?: string | null;
  proxima_checagem_integridade?: string | null;
  capacidade_total_bytes?: number | null;
  capacidade_utilizada_bytes?: number | null;
  identificador_fisico?: string | null;
  midia_origem_id?: number | null;
  data_desativacao?: string | null;
  motivo_desativacao?: string | null;
};

export type MidiaFilters = Partial<{
  q: string;
  tipo_midia_id: string;
  ativo: boolean;
}>;

export type TipoMidiaPayload = {
  nome: string;
  descricao?: string | null;
  tempo_duracao_anos: number;
  periodicidade_checagem_meses: number;
  ativo?: boolean;
};

export type TipoMidiaFilters = Partial<{
  q: string;
  ativo: boolean;
}>;

export type InstrumentoPesquisaPayload = {
  nome: string;
  tipo: TipoInstrumentoPesquisa;
  descricao?: string | null;
  status: StatusInstrumentoPesquisa;
  visibilidade: VisibilidadeInstrumentoPesquisa;
  responsavel?: string | null;
};

export type InstrumentoPesquisaFilters = Partial<{
  q: string;
  tipo: TipoInstrumentoPesquisa;
  status: StatusInstrumentoPesquisa;
  visibilidade: VisibilidadeInstrumentoPesquisa;
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

export type MidiaPage = {
  items: MidiaArmazenamento[];
  total: number;
  limit: number;
  offset: number;
};

export type MigracaoMidiaPage = {
  items: MigracaoMidia[];
  total: number;
  limit: number;
  offset: number;
};

export type MigracaoMidiaIniciarPayload = {
  nova_midia: MidiaPayload;
  motivo_migracao: string;
  procedimento_utilizado: string;
  software_utilizado?: string | null;
  versao_software?: string | null;
  observacoes?: string | null;
};

export type MigracaoMidiaEtapaPayload = {
  descricao: string;
  resultado?: string | null;
  data?: string | null;
  evidencias?: Record<string, unknown> | null;
};

export type MigracaoMidiaRelatorioPayload = {
  tipo: string;
  referencia: string;
  descricao?: string | null;
};

export type MigracaoMidiaConclusaoPayload = {
  resultado: StatusMigracaoMidia;
  observacoes?: string | null;
  relatorio_integridade_origem?: string | null;
  relatorio_integridade_destino?: string | null;
};

export type MigracaoMidiaUpdatePayload = {
  status?: StatusMigracaoMidia | null;
  motivo_migracao?: string | null;
  procedimento_utilizado?: string | null;
  software_utilizado?: string | null;
  versao_software?: string | null;
  observacoes?: string | null;
  relatorio_integridade_origem?: string | null;
  relatorio_integridade_destino?: string | null;
};

export type VerificacaoIntegridadePage = {
  items: VerificacaoIntegridadeMidia[];
  total: number;
  limit: number;
  offset: number;
};

export type VerificacaoIntegridadeManualPayload = {
  data_inicio?: string | null;
  data_fim?: string | null;
  resultado: ResultadoVerificacaoIntegridade;
  software_utilizado?: string | null;
  versao_software?: string | null;
  arquivo_relatorio_id?: string | null;
  total_aips_verificados?: number;
  total_sucesso?: number;
  total_falha?: number;
  total_alerta?: number;
  relatorio_json?: Record<string, unknown>;
  observacoes?: string | null;
};

export type VerificacaoIntegridadeImportPayload = {
  ferramenta?: string | null;
  versao?: string | null;
  arquivo_relatorio_id?: string | null;
  relatorio_json: Record<string, unknown>;
  observacoes?: string | null;
};

export type TipoMidiaPage = {
  items: TipoMidiaArmazenamento[];
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

export function getUnidade(id: number) {
  return apiRequest<UnidadeAcondicionamento>(`/unidades-acondicionamento/${id}`);
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

export type InstrumentoAdvancedSearchPayload = {
  q?: string;
  filters?: Record<string, unknown>;
  sort?: Array<Record<string, "asc" | "desc">>;
  page_size?: number;
  cursor?: string | null;
  offset?: number | null;
};

export function advancedSearchInstrumentoRegistros(
  instrumentoId: string,
  payload: InstrumentoAdvancedSearchPayload,
) {
  return apiRequest<InstrumentoRegistroPage>(`/instrumentos-pesquisa/${instrumentoId}/buscar-avancado`, {
    method: "POST",
    body: JSON.stringify({
      q: "",
      filters: {},
      sort: [],
      page_size: 25,
      cursor: null,
      offset: null,
      ...payload,
    }),
  });
}

export type InstrumentoFacetValue = {
  value: string;
  count: number;
};

export type InstrumentoFacetField = {
  campo: string;
  values: InstrumentoFacetValue[];
};

export type InstrumentoFacetsResponse = {
  facets: InstrumentoFacetField[];
};

export function getInstrumentoRegistroFacets(instrumentoId: string) {
  return apiRequest<InstrumentoFacetsResponse>(`/instrumentos-pesquisa/${instrumentoId}/facetas`);
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

export function listMidiasPage({
  limit = 50,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: MidiaFilters;
} = {}) {
  return apiRequest<MidiaPage>(
    `/midias-armazenamento${queryString({
      limit,
      offset,
      q: filters.q,
      tipo_midia_id: filters.tipo_midia_id,
      ativo: filters.ativo === undefined ? undefined : String(filters.ativo),
    })}`,
  );
}

export async function listMidias() {
  const page = await listMidiasPage({ limit: 100 });
  return page.items;
}

export function getMidia(id: number) {
  return apiRequest<MidiaArmazenamento>(`/midias-armazenamento/${id}`);
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

export function updateMidia(id: number, payload: Partial<MidiaPayload>) {
  return apiRequest<MidiaArmazenamento>(`/midias-armazenamento/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function listEventosMidia(id: number) {
  return apiRequest<EventoMidiaArmazenamento[]>(
    `/midias-armazenamento/${id}/eventos`,
  );
}

export function getPainelIntegridadeMidias() {
  return apiRequest<IntegridadePainel>("/midias-armazenamento/integridade/painel");
}

export function getResumoIntegridadeMidias() {
  return apiRequest<IntegridadeResumo>("/midias-armazenamento/integridade/resumo");
}

export function listItensIntegridadeMidias({
  categoria,
  limit = 20,
  offset = 0,
}: {
  categoria: CategoriaIntegridadeMidia;
  limit?: number;
  offset?: number;
}) {
  return apiRequest<MidiaPage>(
    `/midias-armazenamento/integridade/itens${queryString({ categoria, limit, offset })}`,
  );
}

export function listMidiasChecagemVencida(limit = 100) {
  return apiRequest<MidiaArmazenamento[]>(
    `/midias-armazenamento/integridade/pendentes${queryString({ limit })}`,
  );
}

export function listMidiasValidadeVencida(limit = 100) {
  return apiRequest<MidiaArmazenamento[]>(
    `/midias-armazenamento/integridade/vencidas${queryString({ limit })}`,
  );
}

export function listVerificacoesIntegridadeMidia(id: number, { limit = 50, offset = 0 } = {}) {
  return apiRequest<VerificacaoIntegridadePage>(
    `/midias-armazenamento/${id}/verificacoes-integridade${queryString({ limit, offset })}`,
  );
}

export function getVerificacaoIntegridadeMidia(id: number, verificacaoId: string) {
  return apiRequest<VerificacaoIntegridadeMidia>(
    `/midias-armazenamento/${id}/verificacoes-integridade/${verificacaoId}`,
  );
}

export function registrarVerificacaoIntegridadeManual(id: number, payload: VerificacaoIntegridadeManualPayload) {
  return apiRequest<VerificacaoIntegridadeMidia>(`/midias-armazenamento/${id}/verificacoes-integridade/manual`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function importarRelatorioVerificacaoIntegridade(id: number, payload: VerificacaoIntegridadeImportPayload) {
  return apiRequest<VerificacaoIntegridadeMidia>(`/midias-armazenamento/${id}/verificacoes-integridade/importar-relatorio`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function iniciarMigracaoMidia(id: number, payload: MigracaoMidiaIniciarPayload) {
  return apiRequest<MigracaoMidia>(`/midias-armazenamento/${id}/migrar`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listMigracoesMidias({
  limit = 50,
  offset = 0,
}: {
  limit?: number;
  offset?: number;
} = {}) {
  return apiRequest<MigracaoMidiaPage>(`/migracoes-midias${queryString({ limit, offset })}`);
}

export function getMigracaoMidia(id: string) {
  return apiRequest<MigracaoMidia>(`/migracoes-midias/${id}`);
}

export function updateMigracaoMidia(id: string, payload: MigracaoMidiaUpdatePayload) {
  return apiRequest<MigracaoMidia>(`/migracoes-midias/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function registrarEtapaMigracaoMidia(id: string, payload: MigracaoMidiaEtapaPayload) {
  return apiRequest<MigracaoMidia>(`/migracoes-midias/${id}/etapas`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function anexarRelatorioMigracaoMidia(id: string, payload: MigracaoMidiaRelatorioPayload) {
  return apiRequest<MigracaoMidia>(`/migracoes-midias/${id}/relatorios`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function concluirMigracaoMidia(id: string, payload: MigracaoMidiaConclusaoPayload) {
  return apiRequest<MigracaoMidia>(`/migracoes-midias/${id}/concluir`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTiposMidiaPage({
  limit = 50,
  offset = 0,
  filters = {},
}: {
  limit?: number;
  offset?: number;
  filters?: TipoMidiaFilters;
} = {}) {
  return apiRequest<TipoMidiaPage>(
    `/tipos-midia-armazenamento${queryString({
      limit,
      offset,
      q: filters.q,
      ativo: filters.ativo === undefined ? undefined : String(filters.ativo),
    })}`,
  );
}

export async function listTiposMidiaAtivos() {
  const page = await listTiposMidiaPage({ limit: 100, filters: { ativo: true } });
  return page.items;
}

export function getTipoMidia(id: string) {
  return apiRequest<TipoMidiaArmazenamento>(`/tipos-midia-armazenamento/${id}`);
}

export function createTipoMidia(payload: TipoMidiaPayload) {
  return apiRequest<TipoMidiaArmazenamento>("/tipos-midia-armazenamento", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTipoMidia(id: string, payload: Partial<TipoMidiaPayload>) {
  return apiRequest<TipoMidiaArmazenamento>(`/tipos-midia-armazenamento/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteTipoMidia(id: string) {
  return apiRequest<void>(`/tipos-midia-armazenamento/${id}`, {
    method: "DELETE",
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
