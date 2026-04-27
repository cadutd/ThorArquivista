export type NormaDescricao = "NOBRADE" | "ISAD_G" | "EAD2002";
export type NivelDescricao = "1" | "2" | "2.5" | "3" | "3.5" | "4" | "5";

export type RegistroDescritivo = {
  id: string;
  parent_id?: string | null;
  nivel: NivelDescricao;
  norma: NormaDescricao;
  codigo_referencia: string;
  titulo: string;
  data_inicial?: string | null;
  data_final?: string | null;
  dimensao?: string | null;
  suporte?: string | null;
  produtor?: string | null;
  historia_administrativa?: string | null;
  historia_arquivistica?: string | null;
  procedencia?: string | null;
  ambito_conteudo?: string | null;
  avaliacao_eliminacao?: string | null;
  incorporacoes?: string | null;
  sistema_arranjo?: string | null;
  condicoes_acesso?: string | null;
  condicoes_reproducao?: string | null;
  idioma?: string | null;
  caracteristicas_tecnicas?: string | null;
  originais?: string | null;
  copias?: string | null;
  unidades_relacionadas?: string | null;
  publicacoes?: string | null;
  notas?: string | null;
  arquivista_responsavel?: string | null;
  regras_convencoes?: string | null;
  data_descricao?: string | null;
  assuntos?: string | null;
  pessoas?: string | null;
  locais?: string | null;
  entidades?: string | null;
  eventos?: string | null;
  has_children?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type RegistroDescritivoPayload = Omit<
  RegistroDescritivo,
  "id" | "has_children" | "created_at" | "updated_at"
>;

export type RegistroDescritivoTreeNode = {
  id: string;
  parent_id?: string | null;
  nivel: NivelDescricao;
  norma: NormaDescricao;
  codigo_referencia: string;
  titulo: string;
  children: RegistroDescritivoTreeNode[];
};

export type EAD2002ImportResult = {
  imported: number;
  root_ids: string[];
  warnings: string[];
};
