import { apiRequest } from "@/lib/api/client";

export type DigitosCodigoEstrutura = {
  corredor: number;
  modulo: number;
  estante: number;
};

export type ConfiguracaoEnderecamento = {
  digitos_codigo_estrutura: DigitosCodigoEstrutura;
};

export type ConfiguracaoInstituicao = {
  nome?: string | null;
  logotipo_data_url?: string | null;
};

export type EsferaAdministrativa =
  | "FEDERAL"
  | "ESTADUAL"
  | "DISTRITAL"
  | "MUNICIPAL"
  | "PRIVADA"
  | "COMUNITARIA"
  | "UNIVERSITARIA"
  | "OUTRA";

export type InstituicaoArquivo = {
  id: string;
  nome: string;
  sigla?: string | null;
  codigo_referencia?: string | null;
  natureza_juridica?: string | null;
  esfera_administrativa?: EsferaAdministrativa | null;
  cnpj?: string | null;
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
  responsavel_nome?: string | null;
  responsavel_cargo?: string | null;
  responsavel_email?: string | null;
  responsavel_telefone?: string | null;
  historico?: string | null;
  missao?: string | null;
  observacoes?: string | null;
  criada_em: string;
  atualizada_em: string;
};

export type InstituicaoArquivoPayload = Omit<
  InstituicaoArquivo,
  "id" | "criada_em" | "atualizada_em"
>;

export function obterConfiguracaoEnderecamento() {
  return apiRequest<ConfiguracaoEnderecamento>("/admin/configuracoes/enderecamento");
}

export function salvarConfiguracaoEnderecamento(payload: ConfiguracaoEnderecamento) {
  return apiRequest<ConfiguracaoEnderecamento>("/admin/configuracoes/enderecamento", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function obterConfiguracaoInstituicao() {
  return apiRequest<ConfiguracaoInstituicao>("/admin/configuracoes/instituicao");
}

export function salvarConfiguracaoInstituicao(payload: ConfiguracaoInstituicao) {
  return apiRequest<ConfiguracaoInstituicao>("/admin/configuracoes/instituicao", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function obterInstituicaoArquivo() {
  return apiRequest<InstituicaoArquivo | null>("/admin/instituicao-arquivo");
}

export function criarInstituicaoArquivo(payload: InstituicaoArquivoPayload) {
  return apiRequest<InstituicaoArquivo>("/admin/instituicao-arquivo", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function atualizarInstituicaoArquivo(payload: Partial<InstituicaoArquivoPayload>) {
  return apiRequest<InstituicaoArquivo>("/admin/instituicao-arquivo", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function excluirInstituicaoArquivo() {
  return apiRequest<void>("/admin/instituicao-arquivo", {
    method: "DELETE",
  });
}
