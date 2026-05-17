import { apiRequest } from "@/lib/api/client";
import type { TipoSuporte } from "@/types/domain";

export type TipoProcessoAdmissao = "FECHADO" | "CONTINUO";
export type TipoIngressoAdmissao = "TRANSFERENCIA" | "RECOLHIMENTO" | "DOACAO" | "AQUISICAO" | "INCORPORACAO" | "REGULARIZACAO_LEGADO" | "OUTRO";
export type StatusProcessoAdmissao = "ABERTO" | "EM_NEGOCIACAO" | "EM_RECEBIMENTO" | "EM_QUARENTENA" | "EM_VALIDACAO" | "PENDENTE_COMPLEMENTACAO" | "EM_GERACAO_AIP" | "CONCLUIDO" | "CANCELADO" | "REJEITADO";
export type ResultadoFinalAdmissao = "ADMITIDO" | "ADMITIDO_COM_RESSALVA" | "REJEITADO" | "CANCELADO";
export type TipoReuniaoAdmissao = "NEGOCIACAO_INICIAL" | "ALINHAMENTO_TECNICO" | "VALIDACAO_SIP" | "REVISAO_ACORDO" | "TRATAMENTO_DIVERGENCIA" | "HOMOLOGACAO" | "ENCERRAMENTO" | "OUTRO";
export type StatusAcordoAdmissao = "RASCUNHO" | "EM_ANALISE" | "ATIVO" | "SUSPENSO" | "ENCERRADO";
export type CanalSubmissao = "UPLOAD" | "API" | "REDE_INTERNA" | "MIDIA_REMOVIVEL" | "ENTREGA_FISICA" | "IMPORTACAO_SISTEMA" | "OUTRO";
export type StatusSessaoSubmissao = "INICIADA" | "EM_TRANSFERENCIA" | "RECEBIDA" | "EM_QUARENTENA" | "EM_VALIDACAO" | "VALIDADA" | "REJEITADA" | "FINALIZADA" | "CANCELADA";
export type StatusSipAdmissao = "RECEBIDO" | "EM_QUARENTENA" | "EM_VALIDACAO" | "VALIDADO" | "VALIDADO_COM_RESSALVA" | "REJEITADO" | "TRANSFORMADO_EM_AIP";
export type TipoEventoAdmissao = "CRIACAO_PROCESSO" | "REUNIAO_ADMISSAO" | "CRIACAO_VERSAO_ACORDO" | "ATIVACAO_ACORDO" | "INICIO_SESSAO" | "RECEBIMENTO_SIP" | "APROVACAO" | "REJEICAO" | "GERACAO_AIP" | "ENCERRAMENTO_PROCESSO" | "CANCELAMENTO_PROCESSO";
export type ResultadoEventoAdmissao = "SUCESSO" | "FALHA" | "ALERTA" | "PENDENTE" | "INFORMATIVO";

export type ProcessoAdmissao = {
  id: string;
  numero_processo: string;
  titulo: string;
  descricao?: string | null;
  id_instituicao_arquivo: string;
  id_entidade_produtora: string;
  tipo_processo_admissao: TipoProcessoAdmissao;
  tipo_ingresso: TipoIngressoAdmissao;
  tipo_suporte: TipoSuporte;
  data_inicio: string;
  data_fim_prevista?: string | null;
  data_encerramento?: string | null;
  processo_ativo: boolean;
  admissoes_recorrentes: boolean;
  status: StatusProcessoAdmissao;
  resultado_final?: ResultadoFinalAdmissao | null;
  id_descricao_arquivistica?: string | null;
  codigo_classificacao?: string | null;
  codigo_classificacao_descricao?: string | null;
  restricao_acesso?: string | null;
  hipotese_legal_restricao?: string | null;
  volume_estimado?: string | null;
  volume_recebido?: string | null;
  quantidade_unidades_estimadas?: number | null;
  quantidade_unidades_recebidas?: number | null;
  observacoes?: string | null;
  parecer_final?: string | null;
  nome_instituicao_arquivo?: string | null;
  nome_entidade_produtora?: string | null;
  titulo_descricao_arquivistica?: string | null;
  criado_por?: string | null;
  atualizado_por?: string | null;
  criado_em: string;
  atualizado_em: string;
};

export type ProcessoAdmissaoPayload = Omit<ProcessoAdmissao, "id" | "criado_em" | "atualizado_em" | "nome_instituicao_arquivo" | "nome_entidade_produtora" | "titulo_descricao_arquivistica">;
export type ProcessoAdmissaoFilters = Partial<Pick<ProcessoAdmissao, "numero_processo" | "titulo" | "id_entidade_produtora" | "tipo_processo_admissao" | "tipo_ingresso" | "tipo_suporte" | "status"> & { q: string; processo_ativo: string; data_inicio_de: string; data_inicio_ate: string }>;
export type ProcessoAdmissaoPage = { items: ProcessoAdmissao[]; total: number; limit: number; offset: number };

export type ReuniaoAdmissao = { id: string; id_processo_admissao: string; numero_reuniao: number; titulo: string; descricao?: string | null; tipo_reuniao: TipoReuniaoAdmissao; data_reuniao: string; participantes?: string | null; deliberacoes?: string | null; pendencias?: string | null; proximos_passos?: string | null; ata_documento?: string | null; criado_em: string; atualizado_em: string };
export type AcordoAdmissao = { id: string; id_processo_admissao: string; numero_versao: number; titulo: string; descricao?: string | null; status: StatusAcordoAdmissao; data_inicio_vigencia?: string | null; data_fim_vigencia?: string | null; motivo_revisao?: string | null; regras_empacotamento?: string | null; regras_nomenclatura?: string | null; formatos_aceitos?: string | null; metadados_obrigatorios?: string | null; requisitos_fixidez?: string | null; politica_validacao?: string | null; politica_rejeicao?: string | null; observacoes?: string | null; documento_acordo?: string | null; criado_em: string; atualizado_em: string };
export type SessaoSubmissao = { id: string; id_processo_admissao: string; id_acordo_utilizado: string; numero_sessao: number; titulo: string; descricao?: string | null; data_inicio: string; data_fim?: string | null; canal_submissao: CanalSubmissao; tipo_suporte: TipoSuporte; status: StatusSessaoSubmissao; responsavel_envio?: string | null; responsavel_recebimento?: string | null; volume_informado?: string | null; volume_recebido?: string | null; observacoes?: string | null; criado_em: string; atualizado_em: string };
export type SipAdmissao = { id: string; id_processo_admissao: string; id_sessao_submissao: string; codigo_sip: string; titulo: string; descricao?: string | null; tipo_sip: TipoSuporte; status: StatusSipAdmissao; data_recebimento: string; caminho_armazenamento_temporario?: string | null; algoritmo_hash?: string | null; hash_global?: string | null; tamanho_bytes?: number | null; quantidade_arquivos?: number | null; quantidade_unidades_fisicas?: number | null; resultado_validacao?: string | null; observacoes?: string | null; criado_em: string; atualizado_em: string };
export type EventoAdmissao = { id: string; id_processo_admissao: string; id_sessao_submissao?: string | null; id_sip?: string | null; id_unidade_acondicionamento?: number | null; tipo_evento: TipoEventoAdmissao; descricao: string; resultado: ResultadoEventoAdmissao; agente?: string | null; data_evento: string; detalhe_tecnico?: string | null; evidencia?: string | null; criado_em: string };

function queryString(params: Record<string, string | number | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") searchParams.set(key, String(value));
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function listProcessosAdmissao({ limit = 20, offset = 0, filters = {} }: { limit?: number; offset?: number; filters?: ProcessoAdmissaoFilters } = {}) {
  return apiRequest<ProcessoAdmissaoPage>(`/admissao/processos${queryString({ limit, offset, ...filters })}`);
}
export function getProcessoAdmissao(id: string) { return apiRequest<ProcessoAdmissao>(`/admissao/processos/${id}`); }
export function createProcessoAdmissao(payload: ProcessoAdmissaoPayload) { return apiRequest<ProcessoAdmissao>("/admissao/processos", { method: "POST", body: JSON.stringify(payload) }); }
export function updateProcessoAdmissao(id: string, payload: Partial<ProcessoAdmissaoPayload>) { return apiRequest<ProcessoAdmissao>(`/admissao/processos/${id}`, { method: "PUT", body: JSON.stringify(payload) }); }
export function deleteProcessoAdmissao(id: string) { return apiRequest<void>(`/admissao/processos/${id}`, { method: "DELETE" }); }

export function listReunioesAdmissao(processoId: string) { return apiRequest<ReuniaoAdmissao[]>(`/admissao/processos/${processoId}/reunioes`); }
export function createReuniaoAdmissao(processoId: string, payload: Partial<ReuniaoAdmissao>) { return apiRequest<ReuniaoAdmissao>(`/admissao/processos/${processoId}/reunioes`, { method: "POST", body: JSON.stringify(payload) }); }
export function listAcordosAdmissao(processoId: string) { return apiRequest<AcordoAdmissao[]>(`/admissao/processos/${processoId}/acordos`); }
export function createAcordoAdmissao(processoId: string, payload: Partial<AcordoAdmissao>) { return apiRequest<AcordoAdmissao>(`/admissao/processos/${processoId}/acordos`, { method: "POST", body: JSON.stringify(payload) }); }
export function ativarAcordoAdmissao(id: string) { return apiRequest<AcordoAdmissao>(`/admissao/acordos/${id}/ativar`, { method: "POST" }); }
export function novaVersaoAcordoAdmissao(id: string) { return apiRequest<AcordoAdmissao>(`/admissao/acordos/${id}/nova-versao`, { method: "POST" }); }
export function listSessoesSubmissao(processoId: string) { return apiRequest<SessaoSubmissao[]>(`/admissao/processos/${processoId}/sessoes`); }
export function createSessaoSubmissao(processoId: string, payload: Partial<SessaoSubmissao>) { return apiRequest<SessaoSubmissao>(`/admissao/processos/${processoId}/sessoes`, { method: "POST", body: JSON.stringify(payload) }); }
export function finalizarSessaoSubmissao(id: string) { return apiRequest<SessaoSubmissao>(`/admissao/sessoes/${id}/finalizar`, { method: "POST" }); }
export function listSipsProcesso(processoId: string) { return apiRequest<SipAdmissao[]>(`/admissao/processos/${processoId}/sips`); }
export function createSipAdmissao(sessaoId: string, payload: Partial<SipAdmissao>) { return apiRequest<SipAdmissao>(`/admissao/sessoes/${sessaoId}/sips`, { method: "POST", body: JSON.stringify(payload) }); }
export function validarSipAdmissao(id: string) { return apiRequest<SipAdmissao>(`/admissao/sips/${id}/validar`, { method: "POST" }); }
export function rejeitarSipAdmissao(id: string) { return apiRequest<SipAdmissao>(`/admissao/sips/${id}/rejeitar`, { method: "POST" }); }
export function listEventosAdmissao(processoId: string) { return apiRequest<EventoAdmissao[]>(`/admissao/processos/${processoId}/eventos`); }
export function createEventoAdmissao(processoId: string, payload: Partial<EventoAdmissao>) { return apiRequest<EventoAdmissao>(`/admissao/processos/${processoId}/eventos`, { method: "POST", body: JSON.stringify(payload) }); }
