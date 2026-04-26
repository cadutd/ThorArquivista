import { apiRequest } from "@/lib/api/client";

export type DigitosCodigoEstrutura = {
  corredor: number;
  modulo: number;
  estante: number;
};

export type ConfiguracaoEnderecamento = {
  digitos_codigo_estrutura: DigitosCodigoEstrutura;
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
