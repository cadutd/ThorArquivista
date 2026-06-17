export type TipoSuporte = "FISICO" | "DIGITAL" | "HIBRIDO";
export type TipoUnidade = "CAIXA" | "PASTA" | "VOLUME" | "AIP" | "SIP" | "DIP";
export type NivelAcesso = "PUBLICO" | "RESTRITO" | "CONFIDENCIAL";
export type StatusUnidade = "ATIVA" | "INATIVA" | "TRANSFERIDA" | "ELIMINADA";
export type FuncaoCopia = "PRESERVACAO" | "BACKUP" | "ACESSO" | "QUARENTENA";
export type StatusCopia = "ATIVA" | "INDISPONIVEL" | "CORROMPIDA" | "EM_VERIFICACAO";
export type TipoEventoPreservacao = "INGESTAO" | "VALIDACAO" | "FIXIDEZ" | "REPLICACAO" | "MIGRACAO" | "ACESSO" | "MOVIMENTACAO" | "OUTRO";
export type TipoEventoMidiaArmazenamento = "CRIACAO_MIDIA" | "ATUALIZACAO_MIDIA" | "REATIVACAO_MIDIA" | "CHECAGEM_MIDIA" | "MIGRACAO_MIDIA" | "DESATIVACAO_MIDIA" | "VALIDADE_EXPIRADA" | "FALHA_INTEGRIDADE" | "ALERTA_INTEGRIDADE";
export type ResultadoEventoPreservacao = "SUCESSO" | "FALHA" | "ALERTA" | "INDETERMINADO";
export type StatusMidiaArmazenamento = "ATIVA" | "EM_VERIFICACAO" | "COM_ALERTA" | "FALHA_INTEGRIDADE" | "EXPIRADA" | "EM_MIGRACAO" | "MIGRADA" | "DESATIVADA" | "PERDIDA";
export type StatusMigracaoMidia = "PLANEJADA" | "EM_EXECUCAO" | "AGUARDANDO_VALIDACAO" | "CONCLUIDA" | "CANCELADA";
export type ResultadoVerificacaoIntegridade = "SUCESSO" | "FALHA" | "ALERTA" | "INCONCLUSIVO";
export type TipoInstrumentoPesquisa = "GUIA" | "INVENTARIO" | "CATALOGO" | "INDICE" | "BASE_TEMATICA" | "EXPOSICAO" | "OUTRO";
export type StatusInstrumentoPesquisa = "RASCUNHO" | "PUBLICADO" | "ARQUIVADO";
export type VisibilidadeInstrumentoPesquisa = "INTERNO" | "PUBLICO" | "RESTRITO";
export type TipoCampoInstrumento = "TEXTO_CURTO" | "TEXTO_LONGO" | "NUMERO" | "DATA" | "PERIODO" | "BOOLEANO" | "LISTA_SIMPLES" | "LISTA_MULTIPLA" | "VOCABULARIO" | "UNIDADE_ACONDICIONAMENTO" | "MIDIA_ARMAZENAMENTO" | "REGISTRO_DESCRITIVO" | "URL" | "ARQUIVO" | "IMAGEM" | "CAMPO_CALCULADO";
export type TipoEntidadeProdutora = "ORGAO_PUBLICO" | "UNIDADE_ADMINISTRATIVA" | "EMPRESA_PUBLICA" | "EMPRESA_PRIVADA" | "PESSOA_FISICA" | "FAMILIA" | "COMISSAO" | "GRUPO_TRABALHO" | "FUNDO" | "COLECAO" | "OUTRO";
export type PapelUsuario = "ADMIN" | "ARQUIVISTA" | "ADMISSAO" | "GESTOR_ARMAZENAMENTO" | "CONSULTA";
export type AcaoPermissao = "CRIAR" | "EDITAR" | "CONSULTAR" | "EXCLUIR";

export type UnidadeAcondicionamento = {
  id: number;
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

export type TipoMidiaArmazenamento = {
  id: string;
  nome: string;
  descricao?: string | null;
  tempo_duracao_anos: number;
  periodicidade_checagem_meses: number;
  ativo: boolean;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type MidiaArmazenamento = {
  id: number;
  nome: string;
  tipo_midia_id: string;
  tipo_midia?: TipoMidiaArmazenamento | null;
  descricao?: string | null;
  ativo: boolean;
  status: StatusMidiaArmazenamento;
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
  id_posicao_armazenamento?: number | null;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type MigracaoMidia = {
  id: string;
  midia_origem_id: number;
  midia_destino_id: number;
  data_inicio: string;
  data_conclusao?: string | null;
  usuario_responsavel_id?: string | null;
  status: StatusMigracaoMidia;
  motivo_migracao: string;
  procedimento_utilizado: string;
  software_utilizado?: string | null;
  versao_software?: string | null;
  observacoes?: string | null;
  relatorio_integridade_origem?: string | null;
  relatorio_integridade_destino?: string | null;
  evento_id?: number | null;
  etapas: Array<Record<string, unknown>>;
  relatorios: Array<Record<string, unknown>>;
  criado_em?: string | null;
  atualizado_em?: string | null;
  midia_origem?: MidiaArmazenamento | null;
  midia_destino?: MidiaArmazenamento | null;
};

export type VerificacaoIntegridadeMidia = {
  id: string;
  midia_id: number;
  data_inicio: string;
  data_fim?: string | null;
  usuario_id?: string | null;
  resultado: ResultadoVerificacaoIntegridade;
  software_utilizado?: string | null;
  versao_software?: string | null;
  arquivo_relatorio_id?: string | null;
  total_aips_verificados: number;
  total_sucesso: number;
  total_falha: number;
  total_alerta: number;
  relatorio_json: Record<string, unknown>;
  observacoes?: string | null;
  evento_id?: number | null;
  criado_em?: string | null;
  eventos_unidades?: EventoPreservacao[];
};

export type IntegridadePainel = {
  validade_vencida: MidiaArmazenamento[];
  checagem_vencida: MidiaArmazenamento[];
  proximas_vencimento: MidiaArmazenamento[];
  falha_ultima_checagem: MidiaArmazenamento[];
  sem_checagem: MidiaArmazenamento[];
  com_alerta: MidiaArmazenamento[];
};

export type CategoriaIntegridadeMidia = keyof IntegridadePainel;

export type IntegridadeResumo = Record<CategoriaIntegridadeMidia, number>;

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

export type EventoMidiaArmazenamento = {
  id: number;
  id_midia_armazenamento: number;
  tipo_evento: TipoEventoMidiaArmazenamento;
  resultado: ResultadoEventoPreservacao;
  data_evento?: string | null;
  detalhe?: string | null;
  agente?: string | null;
  correlacao?: string | null;
  premis_json?: Record<string, unknown> | null;
  evento_relacionado_id?: number | null;
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
  total?: number | null;
};

export type EntidadeProdutora = {
  id: string;
  nome: string;
  nome_normalizado?: string | null;
  sigla?: string | null;
  codigo_referencia?: string | null;
  tipo_entidade: TipoEntidadeProdutora;
  natureza_juridica?: string | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  entidade_ativa: boolean;
  historico?: string | null;
  competencias_funcoes?: string | null;
  observacoes?: string | null;
  email?: string | null;
  telefone?: string | null;
  site?: string | null;
  endereco_logradouro?: string | null;
  endereco_numero?: string | null;
  endereco_complemento?: string | null;
  endereco_bairro?: string | null;
  endereco_municipio?: string | null;
  endereco_uf?: string | null;
  endereco_cep?: string | null;
  endereco_pais?: string | null;
  id_entidade_superior?: string | null;
  nome_entidade_superior?: string | null;
  criado_em: string;
  atualizado_em: string;
  avisos_duplicidade?: string[];
};

export type EntidadeProdutoraTree = Pick<
  EntidadeProdutora,
  "id" | "nome" | "sigla" | "codigo_referencia" | "tipo_entidade" | "entidade_ativa" | "id_entidade_superior"
> & {
  has_children: boolean;
  filhos: EntidadeProdutoraTree[];
};

export type Usuario = {
  id: string;
  keycloak_sub?: string | null;
  username: string;
  nome: string;
  email: string;
  papel: PapelUsuario;
  id_perfil?: string | null;
  perfil?: Perfil | null;
  ativo: boolean;
  observacoes?: string | null;
  criado_em: string;
  atualizado_em: string;
};

export type Permissao = {
  id: string;
  codigo: string;
  nome: string;
  descricao?: string | null;
  modulo: string;
  funcao: string;
  acao: AcaoPermissao;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
};

export type Perfil = {
  id: string;
  codigo: string;
  nome: string;
  descricao?: string | null;
  ativo: boolean;
  sistema: boolean;
  permissoes: Permissao[];
  criado_em: string;
  atualizado_em: string;
};
