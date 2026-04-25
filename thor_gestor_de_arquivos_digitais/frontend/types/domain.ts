export type TipoSuporte = "FISICO" | "DIGITAL" | "HIBRIDO";
export type TipoUnidade = "CAIXA" | "PASTA" | "VOLUME" | "AIP" | "SIP" | "DIP";
export type NivelAcesso = "PUBLICO" | "RESTRITO" | "CONFIDENCIAL";
export type StatusUnidade = "ATIVA" | "INATIVA" | "TRANSFERIDA" | "ELIMINADA";
export type TipoMidiaArmazenamento = "FILESYSTEM" | "NAS" | "NFS" | "LTO" | "S3" | "CLOUD";
export type FuncaoCopia = "PRESERVACAO" | "BACKUP" | "ACESSO" | "QUARENTENA";
export type StatusCopia = "ATIVA" | "INDISPONIVEL" | "CORROMPIDA" | "EM_VERIFICACAO";
export type TipoEventoPreservacao = "INGESTAO" | "VALIDACAO" | "FIXIDEZ" | "REPLICACAO" | "MIGRACAO" | "ACESSO" | "MOVIMENTACAO" | "OUTRO";
export type ResultadoEventoPreservacao = "SUCESSO" | "FALHA" | "ALERTA" | "INDETERMINADO";

export type UnidadeAcondicionamento = {
  id: number;
  identificador: string;
  titulo: string;
  descricao?: string | null;
  tipo_suporte: TipoSuporte;
  tipo_unidade: TipoUnidade;
  nivel_acesso: NivelAcesso;
  status: StatusUnidade;
  id_unidade_pai?: number | null;
  id_representa?: number | null;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type MidiaArmazenamento = {
  id: number;
  nome: string;
  tipo: TipoMidiaArmazenamento;
  descricao?: string | null;
  ativo: boolean;
  criado_em?: string | null;
};

export type CopiaDigital = {
  id: number;
  id_unidade_acondicionamento: number;
  id_midia_armazenamento: number;
  uri_copia: string;
  funcao_copia: FuncaoCopia;
  status_copia: StatusCopia;
  algoritmo_fixidez?: string | null;
  hash_fixidez?: string | null;
  ultima_verificacao_em?: string | null;
  criada_em?: string | null;
};

export type EventoPreservacao = {
  id: number;
  id_unidade_acondicionamento: number;
  tipo_evento: TipoEventoPreservacao;
  resultado: ResultadoEventoPreservacao;
  detalhe?: string | null;
  agente?: string | null;
  correlacao?: string | null;
  criado_em?: string | null;
};
