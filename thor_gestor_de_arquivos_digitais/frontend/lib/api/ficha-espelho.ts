import { apiRequest } from "@/lib/api/client";
import type {
  FichaEspelhoGerada,
  ModeloFichaEspelho,
  ModeloFichaEspelhoPage,
  ModeloFichaEspelhoPayload,
} from "@/types/ficha-espelho";

function queryString(params: Record<string, string | number | boolean | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function listarModelosFichaEspelho({
  limit = 100,
  offset = 0,
  q,
  ativo,
}: {
  limit?: number;
  offset?: number;
  q?: string;
  ativo?: boolean;
} = {}) {
  return apiRequest<ModeloFichaEspelhoPage>(
    `/fichas-espelho/modelos${queryString({ limit, offset, q, ativo })}`,
  );
}

export function obterModeloFichaEspelhoPadrao() {
  return apiRequest<ModeloFichaEspelho>("/fichas-espelho/modelos/padrao");
}

export function obterModeloFichaEspelho(id: number) {
  return apiRequest<ModeloFichaEspelho>(`/fichas-espelho/modelos/${id}`);
}

export function criarModeloFichaEspelho(payload: ModeloFichaEspelhoPayload) {
  return apiRequest<ModeloFichaEspelho>("/fichas-espelho/modelos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function atualizarModeloFichaEspelho(id: number, payload: Partial<ModeloFichaEspelhoPayload>) {
  return apiRequest<ModeloFichaEspelho>(`/fichas-espelho/modelos/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function excluirModeloFichaEspelho(id: number) {
  return apiRequest<void>(`/fichas-espelho/modelos/${id}`, {
    method: "DELETE",
  });
}

export function gerarFichasEspelho(payload: { modelo_id: number; unidade_ids: number[] }) {
  return apiRequest<FichaEspelhoGerada>("/fichas-espelho/gerar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
