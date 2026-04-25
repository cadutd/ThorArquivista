export type TipoLocalGuarda =
  | "DEPOSITO"
  | "SALA_COFRE"
  | "DATA_CENTER"
  | "MAPOTECA"
  | "LABORATORIO"
  | "NUVEM"
  | "OUTRO";

export type TipoZonaGuarda =
  | "ACERVO_TEXTUAL"
  | "CARTOGRAFICO"
  | "ICONOGRAFICO"
  | "MIDIAS_REMOVIVEIS"
  | "FITAS_LTO"
  | "STORAGE_ONLINE"
  | "QUARENTENA"
  | "BACKUP"
  | "ACESSO"
  | "OUTRO";

export type TipoEstruturaArmazenamento =
  | "ESTANTE"
  | "ARQUIVO_DESLIZANTE"
  | "MAPOTECA"
  | "GAVETEIRO"
  | "ARMARIO"
  | "RACK"
  | "COFRE"
  | "SERVIDOR"
  | "NAS"
  | "BUCKET_S3"
  | "VOLUME_REDE"
  | "UNIDADE_LTO"
  | "OUTRO";

export type TipoCompartimentoArmazenamento =
  | "PRATELEIRA"
  | "GAVETA"
  | "BANDEJA"
  | "SLOT"
  | "VOLUME"
  | "DIRETORIO"
  | "BUCKET"
  | "PARTICAO"
  | "CAIXA_INTERNA"
  | "OUTRO";

export type TipoPosicaoArmazenamento =
  | "POSICAO_CAIXA"
  | "POSICAO_PASTA"
  | "POSICAO_VOLUME"
  | "POSICAO_MAPA"
  | "SLOT_FITA"
  | "SLOT_MIDIA"
  | "DIRETORIO_AIP"
  | "DIRETORIO_SIP"
  | "DIRETORIO_DIP"
  | "BUCKET_OBJETO"
  | "VOLUME_LOGICO"
  | "OUTRO";

export type LocalGuarda = {
  id: number;
  codigo: string;
  nome: string;
  tipo_local: TipoLocalGuarda;
  descricao?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  municipio?: string | null;
  uf?: string | null;
  cep?: string | null;
  pais?: string | null;
  observacoes?: string | null;
  ativo: boolean;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type ZonaGuarda = {
  id: number;
  id_local_guarda: number;
  codigo: string;
  nome: string;
  tipo_zona: TipoZonaGuarda;
  descricao?: string | null;
  quantidade_corredores?: number | null;
  quantidade_modulos_por_corredor?: number | null;
  quantidade_estantes_por_modulo?: number | null;
  quantidade_prateleiras_por_estante?: number | null;
  capacidade_caixas_por_prateleira?: number | null;
  observacoes?: string | null;
  ativo: boolean;
  local_guarda_nome?: string | null;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type EstruturaArmazenamento = {
  id: number;
  id_zona_guarda: number;
  codigo: string;
  nome: string;
  tipo_estrutura: TipoEstruturaArmazenamento;
  descricao?: string | null;
  ordem?: number | null;
  capacidade_total?: number | null;
  observacoes?: string | null;
  ativo: boolean;
  zona_nome?: string | null;
};

export type CompartimentoArmazenamento = {
  id: number;
  id_estrutura_armazenamento: number;
  codigo: string;
  nome: string;
  tipo_compartimento: TipoCompartimentoArmazenamento;
  descricao?: string | null;
  ordem?: number | null;
  capacidade_posicoes?: number | null;
  observacoes?: string | null;
  ativo: boolean;
  estrutura_nome?: string | null;
};

export type PosicaoArmazenamento = {
  id: number;
  id_compartimento_armazenamento: number;
  codigo: string;
  codigo_completo: string;
  tipo_posicao: TipoPosicaoArmazenamento;
  ordem?: number | null;
  capacidade_unidades: number;
  ocupada: boolean;
  ativo: boolean;
  observacoes?: string | null;
  local_guarda?: string | null;
  zona?: string | null;
  localizacao_completa?: string | null;
};

export type MovimentacaoArmazenamento = {
  id: number;
  id_unidade_acondicionamento?: number | null;
  id_midia_armazenamento?: number | null;
  id_copia_unidade_acondicionamento_digital?: number | null;
  id_posicao_origem?: number | null;
  id_posicao_destino?: number | null;
  data_movimentacao?: string | null;
  responsavel?: string | null;
  motivo?: string | null;
  observacoes?: string | null;
};

export type TopografiaGerada = {
  id_zona_guarda: number;
  estruturas_criadas: number;
  compartimentos_criados: number;
  posicoes_criadas: number;
};

export type Ocupacao = {
  id: number;
  nome: string;
  total_posicoes: number;
  posicoes_ocupadas: number;
  capacidade_total: number;
  ocupacao_total: number;
  taxa_ocupacao: number;
};
