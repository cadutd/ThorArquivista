export type TipoSuporte = "FISICO" | "DIGITAL" | "HIBRIDO";
export type TipoUnidade = "CAIXA" | "PASTA" | "VOLUME" | "AIP" | "SIP" | "DIP";
export type NivelAcesso = "PUBLICO" | "RESTRITO" | "CONFIDENCIAL";
export type StatusUnidade = "ATIVA" | "INATIVA" | "TRANSFERIDA" | "ELIMINADA";
export type TipoMidiaArmazenamento = "FILESYSTEM" | "NAS" | "NFS" | "LTO" | "S3" | "CLOUD";
export type FuncaoCopia = "PRESERVACAO" | "BACKUP" | "ACESSO" | "QUARENTENA";
export type StatusCopia = "ATIVA" | "INDISPONIVEL" | "CORROMPIDA" | "EM_VERIFICACAO";
export type TipoEventoPreservacao = "INGESTAO" | "VALIDACAO" | "FIXIDEZ" | "REPLICACAO" | "MIGRACAO" | "ACESSO" | "MOVIMENTACAO" | "OUTRO";
export type ResultadoEventoPreservacao = "SUCESSO" | "FALHA" | "ALERTA" | "INDETERMINADO";
export type TipoInstrumentoPesquisa = "GUIA" | "INVENTARIO" | "CATALOGO" | "INDICE" | "BASE_TEMATICA" | "EXPOSICAO" | "OUTRO";
export type StatusInstrumentoPesquisa = "RASCUNHO" | "PUBLICADO" | "ARQUIVADO";
export type VisibilidadeInstrumentoPesquisa = "INTERNO" | "PUBLICO" | "RESTRITO";
export type TipoCampoInstrumento = "TEXTO_CURTO" | "TEXTO_LONGO" | "NUMERO" | "DATA" | "PERIODO" | "BOOLEANO" | "LISTA_SIMPLES" | "LISTA_MULTIPLA" | "VOCABULARIO" | "UNIDADE_ACONDICIONAMENTO" | "REGISTRO_DESCRITIVO" | "URL" | "ARQUIVO" | "IMAGEM" | "CAMPO_CALCULADO";

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
  id_posicao_armazenamento?: number | null;
  criado_em?: string | null;
  atualizado_em?: string | null;
  digital?: UnidadeAcondicionamentoDigital | null;
  copias_digitais?: CopiaDigital[];
};

export type UnidadeAcondicionamentoDigital = {
  id_unidade_acondicionamento: number;
  tamanho_bytes?: number | null;
  status_fixidez?: string | null;
};

export type MidiaArmazenamento = {
  id: number;
  nome: string;
  tipo: TipoMidiaArmazenamento;
  descricao?: string | null;
  ativo: boolean;
  id_posicao_armazenamento?: number | null;
  criado_em?: string | null;
};

export type CopiaDigital = {
  id: number;
  id_unidade_acondicionamento: number;
  id_midia_armazenamento: number;
  id_posicao_armazenamento?: number | null;
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

export type InstrumentoPesquisa = {
  id: string;
  nome: string;
  tipo: TipoInstrumentoPesquisa;
  descricao?: string | null;
  status: StatusInstrumentoPesquisa;
  visibilidade: VisibilidadeInstrumentoPesquisa;
  responsavel?: string | null;
  criado_em: string;
  atualizado_em: string;
};

export type InstrumentoCampo = {
  id: string;
  instrumento_id: string;
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
  criado_em: string;
  atualizado_em: string;
};

export type InstrumentoCampoSchema = Pick<
  InstrumentoCampo,
  | "id"
  | "nome"
  | "chave"
  | "tipo"
  | "ordem"
  | "obrigatorio"
  | "multiplo"
  | "placeholder"
  | "ajuda"
  | "opcoes"
  | "validacoes"
  | "aparece_cadastro"
  | "aparece_listagem"
  | "aparece_busca"
  | "filtro_avancado"
  | "facetavel"
  | "ordenavel"
>;

export type InstrumentoPesquisaSchema = {
  instrumento: {
    id: string;
    nome: string;
    tipo: TipoInstrumentoPesquisa;
    status: StatusInstrumentoPesquisa;
  };
  campos: InstrumentoCampoSchema[];
};

export type StatusInstrumentoRegistro = "ATIVO" | "INATIVO" | "EXCLUIDO";

export type InstrumentoRegistro = {
  id: string;
  instrumento_id: string;
  schema_version: number;
  dados: Record<string, unknown>;
  unidade_acondicionamento_ids: number[];
  registro_descritivo_ids: string[];
  status: StatusInstrumentoRegistro;
  criado_em: string;
  atualizado_em: string;
};

export type InstrumentoRegistroPage = {
  items: InstrumentoRegistro[];
  page_size: number;
  next_cursor?: string | null;
  has_more: boolean;
};
