import { apiRequest } from "@/lib/api/client";
import type {
  EventoPreservacao,
  MidiaArmazenamento,
  UnidadeAcondicionamento,
} from "@/types/domain";

export type UnidadePayload = {
  identificador: string;
  titulo: string;
  descricao?: string | null;
  tipo_suporte: string;
  tipo_unidade: string;
  nivel_acesso: string;
  status: string;
};

export type MidiaPayload = {
  nome: string;
  tipo: string;
  descricao?: string | null;
  ativo: boolean;
};

export function listUnidades() {
  return apiRequest<UnidadeAcondicionamento[]>("/unidades-acondicionamento");
}

export function createUnidade(payload: UnidadePayload) {
  return apiRequest<UnidadeAcondicionamento>("/unidades-acondicionamento", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listMidias() {
  return apiRequest<MidiaArmazenamento[]>("/midias-armazenamento");
}

export function createMidia(payload: MidiaPayload) {
  return apiRequest<MidiaArmazenamento>("/midias-armazenamento", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEventos(unidadeId: number) {
  return apiRequest<EventoPreservacao[]>(
    `/unidades-acondicionamento/${unidadeId}/eventos-preservacao`,
  );
}
