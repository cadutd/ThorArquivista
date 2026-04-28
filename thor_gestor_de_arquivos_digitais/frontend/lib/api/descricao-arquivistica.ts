import { apiRequest } from "@/lib/api/client";
import { getStoredSession, isSessionActive, redirectToLoginAfterSessionLoss } from "@/lib/auth/session";
import { config } from "@/lib/config";
import { queryString } from "@/lib/api/storage-query";
import type {
  EAD2002ImportResult,
  RegistroDescritivo,
  RegistroDescritivoPayload,
  RegistroDescritivoTreeNode,
} from "@/types/descricao-arquivistica";
import type { UnidadeAcondicionamento } from "@/types/domain";

export function listarArvoreDescricao(params: Record<string, string | undefined | null> = {}) {
  return apiRequest<RegistroDescritivoTreeNode[]>(
    `/descricao-arquivistica/registros/arvore${queryString(params)}`,
  );
}

export function listarRegistrosDescricao(params: Record<string, string | undefined | null> = {}) {
  return apiRequest<RegistroDescritivo[]>(
    `/descricao-arquivistica/registros${queryString(params)}`,
  );
}

export function obterRegistroDescricao(id: string) {
  return apiRequest<RegistroDescritivo>(`/descricao-arquivistica/registros/${id}`);
}

export function listarUnidadesAssociadasDescricao(id: string) {
  return apiRequest<{
    id_registro_descritivo: string;
    unidades: UnidadeAcondicionamento[];
  }>(`/descricao-arquivistica/registros/${id}/unidades`);
}

export function atualizarUnidadesAssociadasDescricao(id: string, unidadesIds: number[]) {
  return apiRequest<{
    id_registro_descritivo: string;
    unidades: UnidadeAcondicionamento[];
  }>(`/descricao-arquivistica/registros/${id}/unidades`, {
    method: "PUT",
    body: JSON.stringify({ unidades_ids: unidadesIds }),
  });
}

export function criarRegistroDescricao(payload: RegistroDescritivoPayload) {
  return apiRequest<RegistroDescritivo>("/descricao-arquivistica/registros", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function atualizarRegistroDescricao(id: string, payload: Partial<RegistroDescritivoPayload>) {
  return apiRequest<RegistroDescritivo>(`/descricao-arquivistica/registros/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function excluirRegistroDescricao(id: string, cascade = false) {
  return apiRequest<void>(`/descricao-arquivistica/registros/${id}${queryString({ cascade })}`, {
    method: "DELETE",
  });
}

export function duplicarRegistroDescricao(id: string, payload: Partial<RegistroDescritivoPayload> = {}) {
  return apiRequest<RegistroDescritivo>(`/descricao-arquivistica/registros/${id}/duplicar`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function moverRegistroDescricao(id: string, parentId: string) {
  return apiRequest<RegistroDescritivo>(`/descricao-arquivistica/registros/${id}/mover`, {
    method: "POST",
    body: JSON.stringify({ parent_id: parentId }),
  });
}

export function criarRegistrosDescricaoLote(parentId: string, registros: RegistroDescritivoPayload[]) {
  return apiRequest<RegistroDescritivo[]>("/descricao-arquivistica/registros/lote", {
    method: "POST",
    body: JSON.stringify({ parent_id: parentId, registros }),
  });
}

export async function exportarRegistroEAD2002(id: string) {
  const response = await authenticatedFetch(`/descricao-arquivistica/registros/${id}/exportar/ead2002`, {
    headers: { Accept: "application/xml" },
  });
  if (!response.ok) {
    if (response.status === 401) {
      redirectToLoginAfterSessionLoss();
      throw new Error("Sua sessão expirou. Entre novamente para continuar.");
    }

    throw new Error(await response.text() || `Erro ${response.status} na API.`);
  }
  return response.blob();
}

export async function importarEAD2002(content: string) {
  const response = await authenticatedFetch("/descricao-arquivistica/importar/ead2002", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/xml",
    },
    body: content,
  });
  if (!response.ok) {
    if (response.status === 401) {
      redirectToLoginAfterSessionLoss();
      throw new Error("Sua sessão expirou. Entre novamente para continuar.");
    }

    throw new Error(await response.text() || `Erro ${response.status} na API.`);
  }
  return (await response.json()) as EAD2002ImportResult;
}

function authenticatedFetch(path: string, init: RequestInit) {
  const headers = new Headers(init.headers);
  const session = getStoredSession();
  if (session && isSessionActive(session)) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  } else {
    redirectToLoginAfterSessionLoss();
    throw new Error("Sua sessão expirou. Entre novamente para continuar.");
  }
  return fetch(`${config.apiBaseUrl}${path}`, { ...init, headers });
}
