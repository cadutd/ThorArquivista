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
