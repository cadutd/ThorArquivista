import { request } from "./api";
import type { InstrumentoCampo, TipoCampo } from "@/types/domain";

export type NovoCampo = { nome: string; chave: string; tipo: TipoCampo; obrigatorio: boolean };
export type Mapeamento = { origem: string; destino?: string | null; novo?: NovoCampo | null };
export type ConfiguracaoImportacao = { operacao_id: string; schema_version: number; mapeamentos: Mapeamento[] };
export type AnaliseImportacao = {
  nome: string; schema_version: number; total: number; formato: string; codificacao: string; separador?: string;
  colunas: { origem: string; chave_sugerida: string; tipo_sugerido: TipoCampo; amostras: unknown[] }[];
  campos: InstrumentoCampo[];
};
export type RelatorioImportacao = {
  total: number; validos: number; invalidos: number;
  erros: { linha: number; campo: string; mensagem: string }[];
  previa: { linha: number; dados: Record<string, unknown> }[];
  novos_campos: NovoCampo[];
};
export type Importacao = {
  id: string; status: "EM_ANDAMENTO" | "CONCLUIDA" | "INTERROMPIDA";
  total: number; processados: number; criado_em: string; configuracao: ConfiguracaoImportacao;
};
const path = (id: string) => "/instrumentos/" + id + "/registros/importacoes";
export const listarImportacoes = (id: string) => request<Importacao[]>(path(id));

export function enviarImportacao<T>(id: string, acao: "analisar" | "validar" | "", arquivo: File, configuracao?: ConfiguracaoImportacao) {
  const data = new FormData();
  data.append("arquivo", arquivo);
  if (configuracao) data.append("configuracao", JSON.stringify(configuracao));
  return request<T>(path(id) + (acao ? "/" + acao : ""), { method: "POST", body: data });
}
