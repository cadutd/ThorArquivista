export type CampoFichaEspelho =
  | "logo_instituicao"
  | "unidade_produtora"
  | "fundo"
  | "classe"
  | "subclasse"
  | "descricao_conteudo"
  | "data_limite"
  | "identificador_caixa"
  | "codigo_barras";

export const campoFichaEspelhoLabels: Record<CampoFichaEspelho, string> = {
  logo_instituicao: "Logotipo da instituição",
  unidade_produtora: "Unidade acumuladora/produtora",
  fundo: "Nome do fundo",
  classe: "Nome da classe",
  subclasse: "Nome da subclasse",
  descricao_conteudo: "Descrição do conteúdo",
  data_limite: "Data-limite",
  identificador_caixa: "Identificador da caixa",
  codigo_barras: "Código de barras",
};

export const camposFichaEspelhoPadrao = Object.keys(campoFichaEspelhoLabels) as CampoFichaEspelho[];

export type ModeloFichaEspelho = {
  id: number;
  nome: string;
  descricao?: string | null;
  campos: CampoFichaEspelho[];
  tamanho_papel: "A4" | "CARTA";
  orientacao: "RETRATO" | "PAISAGEM";
  colunas: number;
  largura_cm: number;
  altura_cm: number;
  ativo: boolean;
  criado_em?: string | null;
  atualizado_em?: string | null;
};

export type ModeloFichaEspelhoPayload = Omit<ModeloFichaEspelho, "id" | "criado_em" | "atualizado_em">;

export type ModeloFichaEspelhoPage = {
  items: ModeloFichaEspelho[];
  total: number;
  limit: number;
  offset: number;
};

export type FichaEspelhoDados = {
  unidade_id: number;
  unidade_produtora?: string | null;
  fundo?: string | null;
  classe?: string | null;
  subclasse?: string | null;
  descricao_conteudo?: string | null;
  data_limite?: string | null;
  identificador_caixa: string;
  codigo_barras?: string | null;
};

export type FichaEspelhoGerada = {
  modelo: ModeloFichaEspelho;
  instituicao: {
    nome?: string | null;
    logotipo_data_url?: string | null;
  };
  fichas: FichaEspelhoDados[];
};
