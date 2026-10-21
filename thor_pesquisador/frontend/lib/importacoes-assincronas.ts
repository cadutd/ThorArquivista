import { downloadFile, request } from "./api";
import type { AnaliseImportacao, ConfiguracaoImportacao, RelatorioImportacao } from "./importacoes";

export const statusImportacao = ["RECEBENDO", "ANALISANDO", "AGUARDANDO_MAPA", "VALIDANDO", "AGUARDANDO_CONFIRMACAO",
  "ERROS_VALIDACAO", "PENDENTE", "IMPORTANDO", "CONCLUIDA", "FALHOU", "PAUSADA", "CANCELADA", "EXPIRADA"] as const;
export type StatusImportacao = typeof statusImportacao[number];
export type JobImportacao = {
  id: string; status: StatusImportacao; phase: string | null;
  total: number; processados: number; fase_processados: number; validos: number; invalidos: number;
  bytes_recebidos: number; tamanho_bytes: number; nome_arquivo: string; erro: string | null;
  analise: (Pick<AnaliseImportacao, "nome" | "schema_version" | "campos" | "colunas"> & Partial<AnaliseImportacao>) | null;
  configuracao: ConfiguracaoImportacao | null;
  relatorio: Omit<RelatorioImportacao, "novos_campos"> | null;
  criado_em: string; atualizado_em: string; expira_em: string | null;
  velocidade: number | null; estimativa_segundos: number | null;
};
export type LimitesImportacao = { max_bytes: number; max_registros: number; chunk_bytes: number };
export type PaginaImportacoes = { items: JobImportacao[]; total: number; limit: number; offset: number };
export const CHUNK_BYTES = 8 * 1024 * 1024;
export const MAX_CHUNK_BYTES = 16 * 1024 * 1024;
const path = (iid: string) => "/instrumentos/" + encodeURIComponent(iid) + "/registros/importacoes/assincronas";
const jobPath = (iid: string, jid: string) => path(iid) + "/" + encodeURIComponent(jid);
export const listarImportacoesAssincronas = (iid: string, params: { limit: number; offset: number; q: string; status: string }, signal?: AbortSignal) =>
  request<PaginaImportacoes>(path(iid) + "?" + new URLSearchParams({ ...params, limit: String(params.limit), offset: String(params.offset) }), { signal });
export const obterLimitesImportacao = (iid: string, signal?: AbortSignal) => request<LimitesImportacao>(path(iid) + "/limites", { signal });
export const obterImportacao = (iid: string, jid: string, signal?: AbortSignal) => request<JobImportacao>(jobPath(iid, jid), { signal });
export const criarImportacao = (iid: string, payload: { operacao_id: string; nome_arquivo: string; tamanho_bytes: number }, signal?: AbortSignal) =>
  request<JobImportacao>(path(iid), { method: "POST", body: JSON.stringify(payload), signal });
export function enviarParteImportacao(iid: string, jid: string, numero: number, arquivo: Blob, signal?: AbortSignal) {
  const data = new FormData();
  data.append("arquivo", arquivo, "parte");
  return request<JobImportacao>(jobPath(iid, jid) + "/partes?numero=" + numero, { method: "POST", body: data, signal });
}
export type AcaoImportacao = "finalizar" | "validar" | "confirmar" | "cancelar" | "retomar";
export const acionarImportacao = (iid: string, jid: string, acao: AcaoImportacao, configuracao?: ConfiguracaoImportacao, signal?: AbortSignal) =>
  request<JobImportacao>(jobPath(iid, jid) + "/" + acao, { method: "POST", ...(configuracao ? { body: JSON.stringify(configuracao) } : {}), signal });
export const baixarErrosImportacao = (iid: string, jid: string) => downloadFile(jobPath(iid, jid) + "/erros", "importacao-" + jid + "-erros.csv");
export const importacaoAtiva = (status: StatusImportacao) => ["RECEBENDO", "ANALISANDO", "VALIDANDO", "PENDENTE", "IMPORTANDO"].includes(status);
export const podeRetomarImportacao = (status: StatusImportacao) => status === "FALHOU" || status === "PAUSADA";
export const podeCancelarImportacao = (status: StatusImportacao) => !["CONCLUIDA", "CANCELADA", "EXPIRADA"].includes(status);
export function progressoImportacao(job: JobImportacao) {
  const envio = job.status === "RECEBENDO";
  const fase = job.status === "ANALISANDO" || job.status === "VALIDANDO";
  const atual = envio ? job.bytes_recebidos : fase ? job.fase_processados : job.processados;
  const total = envio ? job.tamanho_bytes : job.total;
  return { atual, total, percentual: total > 0 ? Math.min(100, Math.max(0, atual / total * 100)) : 0 };
}
