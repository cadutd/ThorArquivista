import { apiRequest } from "@/lib/api/client";
import { queryString } from "@/lib/api/storage-query";
import type {
  CompartimentoArmazenamento,
  EstruturaArmazenamento,
  LocalGuarda,
  MovimentacaoArmazenamento,
  Ocupacao,
  PosicaoArmazenamento,
  TipoCompartimentoArmazenamento,
  TipoEstruturaArmazenamento,
  TipoLocalGuarda,
  TipoPosicaoArmazenamento,
  TipoZonaGuarda,
  TopografiaGerada,
  ZonaGuarda,
} from "@/types/storage";
import type {
  CopiaDigital,
  MidiaArmazenamento,
  UnidadeAcondicionamento,
} from "@/types/domain";

export type LocalGuardaPayload = Partial<LocalGuarda> & {
  codigo: string;
  nome: string;
  tipo_local: TipoLocalGuarda;
};

export type ZonaGuardaPayload = Partial<ZonaGuarda> & {
  id_local_guarda: number;
  codigo: string;
  nome: string;
  tipo_zona: TipoZonaGuarda;
};

export type EstruturaPayload = Partial<EstruturaArmazenamento> & {
  id_zona_guarda: number;
  codigo: string;
  nome: string;
  tipo_estrutura: TipoEstruturaArmazenamento;
};

export type CompartimentoPayload = Partial<CompartimentoArmazenamento> & {
  id_estrutura_armazenamento: number;
  codigo: string;
  nome: string;
  tipo_compartimento: TipoCompartimentoArmazenamento;
};

export type PosicaoPayload = Partial<PosicaoArmazenamento> & {
  id_compartimento_armazenamento: number;
  codigo: string;
  codigo_completo: string;
  tipo_posicao: TipoPosicaoArmazenamento;
};

export type AtribuirPosicaoPayload = {
  id_posicao: number;
  responsavel?: string | null;
  motivo?: string | null;
  observacoes?: string | null;
};

export function listarLocaisGuarda(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<LocalGuarda[]>(`/locais-guarda${queryString({ limit: 1000, ...params })}`);
}

export function criarLocalGuarda(payload: LocalGuardaPayload) {
  return apiRequest<LocalGuarda>("/locais-guarda", { method: "POST", body: JSON.stringify(payload) });
}

export function obterLocalGuarda(id: number) {
  return apiRequest<LocalGuarda>(`/locais-guarda/${id}`);
}

export function atualizarLocalGuarda(id: number, payload: Partial<LocalGuardaPayload>) {
  return apiRequest<LocalGuarda>(`/locais-guarda/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function excluirLocalGuarda(id: number) {
  return apiRequest<void>(`/locais-guarda/${id}`, { method: "DELETE" });
}

export function listarZonasGuarda(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<ZonaGuarda[]>(`/zonas-guarda${queryString({ limit: 1000, ...params })}`);
}

export function criarZonaGuarda(payload: ZonaGuardaPayload) {
  return apiRequest<ZonaGuarda>("/zonas-guarda", { method: "POST", body: JSON.stringify(payload) });
}

export function atualizarZonaGuarda(id: number, payload: Partial<ZonaGuardaPayload>) {
  return apiRequest<ZonaGuarda>(`/zonas-guarda/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function excluirZonaGuarda(id: number) {
  return apiRequest<void>(`/zonas-guarda/${id}`, { method: "DELETE" });
}

export function gerarTopografiaZona(id: number) {
  return apiRequest<TopografiaGerada>(`/zonas-guarda/${id}/gerar-topografia`, { method: "POST" });
}

export function listarEstruturas(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<EstruturaArmazenamento[]>(`/estruturas-armazenamento${queryString({ limit: 1000, ...params })}`);
}

export function criarEstrutura(payload: EstruturaPayload) {
  return apiRequest<EstruturaArmazenamento>("/estruturas-armazenamento", { method: "POST", body: JSON.stringify(payload) });
}

export function atualizarEstrutura(id: number, payload: Partial<EstruturaPayload>) {
  return apiRequest<EstruturaArmazenamento>(`/estruturas-armazenamento/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function excluirEstrutura(id: number) {
  return apiRequest<void>(`/estruturas-armazenamento/${id}`, { method: "DELETE" });
}

export function listarCompartimentos(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<CompartimentoArmazenamento[]>(`/compartimentos-armazenamento${queryString({ limit: 1000, ...params })}`);
}

export function criarCompartimento(payload: CompartimentoPayload) {
  return apiRequest<CompartimentoArmazenamento>("/compartimentos-armazenamento", { method: "POST", body: JSON.stringify(payload) });
}

export function atualizarCompartimento(id: number, payload: Partial<CompartimentoPayload>) {
  return apiRequest<CompartimentoArmazenamento>(`/compartimentos-armazenamento/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function excluirCompartimento(id: number) {
  return apiRequest<void>(`/compartimentos-armazenamento/${id}`, { method: "DELETE" });
}

export function listarPosicoes(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<PosicaoArmazenamento[]>(`/posicoes-armazenamento${queryString({ limit: 1000, ...params })}`);
}

export function listarPosicoesLivres(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<PosicaoArmazenamento[]>(`/posicoes-armazenamento/livres${queryString({ limit: 1000, ...params })}`);
}

export function listarPosicoesOcupadas(params: Record<string, string | number | boolean | undefined | null> = {}) {
  return apiRequest<PosicaoArmazenamento[]>(`/posicoes-armazenamento/ocupadas${queryString({ limit: 1000, ...params })}`);
}

export function obterPosicao(id: number) {
  return apiRequest<PosicaoArmazenamento>(`/posicoes-armazenamento/${id}`);
}

export function criarPosicao(payload: PosicaoPayload) {
  return apiRequest<PosicaoArmazenamento>("/posicoes-armazenamento", { method: "POST", body: JSON.stringify(payload) });
}

export function atualizarPosicao(id: number, payload: Partial<PosicaoPayload>) {
  return apiRequest<PosicaoArmazenamento>(`/posicoes-armazenamento/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function excluirPosicao(id: number) {
  return apiRequest<void>(`/posicoes-armazenamento/${id}`, { method: "DELETE" });
}

export function atribuirPosicaoUnidade(id: number, payload: AtribuirPosicaoPayload) {
  return apiRequest<UnidadeAcondicionamento>(`/unidades-acondicionamento/${id}/atribuir-posicao`, { method: "POST", body: JSON.stringify(payload) });
}

export function atribuirPosicaoMidia(id: number, payload: AtribuirPosicaoPayload) {
  return apiRequest<MidiaArmazenamento>(`/midias-armazenamento/${id}/atribuir-posicao`, { method: "POST", body: JSON.stringify(payload) });
}

export function atribuirPosicaoCopia(id: number, payload: AtribuirPosicaoPayload) {
  return apiRequest<CopiaDigital>(`/copias-unidades-acondicionamento-digitais/${id}/atribuir-posicao`, { method: "POST", body: JSON.stringify(payload) });
}

export function listarMovimentacoes(params: Record<string, string | number | undefined | null> = {}) {
  return apiRequest<MovimentacaoArmazenamento[]>(`/movimentacoes-armazenamento${queryString({ limit: 1000, ...params })}`);
}

export function listarMovimentacoesPorUnidade(id: number) {
  return apiRequest<MovimentacaoArmazenamento[]>(`/movimentacoes-armazenamento/unidade/${id}`);
}

export function listarMovimentacoesPorMidia(id: number) {
  return apiRequest<MovimentacaoArmazenamento[]>(`/movimentacoes-armazenamento/midia/${id}`);
}

export function listarMovimentacoesPorCopia(id: number) {
  return apiRequest<MovimentacaoArmazenamento[]>(`/movimentacoes-armazenamento/copia/${id}`);
}

export function obterOcupacaoLocal(id: number) {
  return apiRequest<Ocupacao>(`/locais-guarda/${id}/ocupacao`);
}

export function obterOcupacaoZona(id: number) {
  return apiRequest<Ocupacao>(`/zonas-guarda/${id}/ocupacao`);
}
