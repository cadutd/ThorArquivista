export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type CursorPage<T> = {
  items: T[];
  page_size: number;
  next_cursor?: string | null;
  has_more: boolean;
};

export type Instrumento = {
  id: string;
  nome: string;
  tipo: "GUIA" | "INVENTARIO" | "CATALOGO" | "INDICE" | "BASE_TEMATICA" | "OUTRO";
  descricao?: string | null;
  status: "RASCUNHO" | "PUBLICADO" | "ARQUIVADO";
  visibilidade: "INTERNO" | "PUBLICO" | "RESTRITO";
  schema_version: number;
  criado_em: string;
  atualizado_em: string;
};

export type TipoCampo =
  | "TEXTO_CURTO"
  | "TEXTO_LONGO"
  | "NUMERO"
  | "DATA"
  | "BOOLEANO"
  | "LISTA_SIMPLES"
  | "LISTA_MULTIPLA"
  | "URL";

export type InstrumentoCampo = {
  id: string;
  instrumento_id: string;
  nome: string;
  chave: string;
  tipo: TipoCampo;
  ordem: number;
  obrigatorio: boolean;
  multiplo: boolean;
  opcoes?: unknown;
  validacoes?: unknown;
  aparece_cadastro: boolean;
  aparece_listagem: boolean;
  aparece_busca: boolean;
};

export type Registro = {
  id: string;
  instrumento_id: string;
  schema_version: number;
  dados: Record<string, unknown>;
  status: "ATIVO" | "INATIVO" | "EXCLUIDO";
  criado_em: string;
  atualizado_em: string;
};

export type DashboardStats = {
  total_instrumentos: number;
  instrumentos_publicados: number;
  instrumentos_rascunho: number;
  total_campos: number;
  total_registros: number;
  registros_ativos: number;
  registros_inativos: number;
  instrumentos_por_tipo: Array<{ tipo: string; total: number }>;
};
