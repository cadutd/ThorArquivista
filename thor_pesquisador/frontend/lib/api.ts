import { notifySessionExpired } from "./auth-navigation.mjs";
import { API_BASE_URL } from "@/lib/config";
import type {
  BuscaAvancadaResultado,
  CursorPage,
  DashboardStats,
  FacetasResultado,
  Instrumento,
  InstrumentoCampo,
  Page,
  Registro,
  ReindexacaoJob
} from "@/types/domain";

export class ApiError extends Error {
  constructor(message:string, public status:number, public detail:unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function requestResponse(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    if(response.status === 401) notifySessionExpired();
    const detail = await response.json().catch(() => ({}));
    const message = Array.isArray(detail.detail)
      ? detail.detail.map((item: {loc?:string[];msg?:string}) => [item.loc?.slice(1).join("."),item.msg].filter(Boolean).join(": ")).join("; ")
      : detail.detail;
    throw new ApiError(message ?? "Falha na requisicao.",response.status,detail.detail);
  }
  return response;
}

export async function downloadFile(path:string, filename:string) {
  const response = await requestResponse(path);
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await requestResponse(path, init);
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export function devLogin() {
  return request("/auth/dev-login", { method: "POST" });
}

export function getGovbrStart(next="/dashboard") {
  return request<{ authorization_url: string }>("/auth/govbr/start?next=" + encodeURIComponent(next));
}

export function me() {
  return request<{ id: string; nome: string; email?: string | null; cpf?: string | null }>("/auth/me");
}

export function logout() {
  return request<void>("/auth/logout", { method: "POST" });
}

export function getDashboardStats() {
  return request<DashboardStats>("/dashboard");
}

export function listInstrumentos(params: { q?: string; nome?: string; tipo?: string; status?: string; visibilidade?: string; descricao?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  search.set("limit", String(params.limit ?? 20));
  search.set("offset", String(params.offset ?? 0));
  if (params.q) search.set("q", params.q);
  for(const key of ["nome","tipo","status","visibilidade","descricao"] as const) {
    if(params[key]) search.set(key,params[key]);
  }
  return request<Page<Instrumento>>(`/instrumentos?${search}`);
}

export function getInstrumento(id: string) {
  return request<Instrumento>(`/instrumentos/${id}`);
}

export function getSchema(id: string) {
  return request<Instrumento & { campos: InstrumentoCampo[] }>(`/instrumentos/${id}/schema`);
}

export function createInstrumento(payload: Partial<Instrumento>) {
  return request<Instrumento>("/instrumentos", { method: "POST", body: JSON.stringify(payload) });
}

export function updateInstrumento(id: string, payload: Partial<Instrumento>) {
  return request<Instrumento>(`/instrumentos/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteInstrumento(id: string) {
  return request<void>(`/instrumentos/${id}`, { method: "DELETE" });
}

export function listCampos(id: string) {
  return request<InstrumentoCampo[]>(`/instrumentos/${id}/campos`);
}

export function createCampo(id: string, payload: Partial<InstrumentoCampo>) {
  return request<InstrumentoCampo>(`/instrumentos/${id}/campos`, { method: "POST", body: JSON.stringify(payload) });
}

export function listRegistros(id: string, cursor?: string | null) {
  const search = new URLSearchParams({ page_size: "50" });
  if (cursor) search.set("cursor", cursor);
  return request<CursorPage<Registro>>(`/instrumentos/${id}/registros?${search}`);
}

export function searchRegistros(id: string, q: string, cursor?: string | null) {
  return request<CursorPage<Registro>>(`/instrumentos/${id}/buscar`, {
    method: "POST",
    body: JSON.stringify({ q, page_size: 50, cursor: cursor ?? null })
  });
}

export function createRegistro(id: string, payload: { dados: Record<string, unknown>; status: string }) {
  return request<Registro>(`/instrumentos/${id}/registros`, { method: "POST", body: JSON.stringify(payload) });
}

export function buscarAvancado(
  id: string,
  payload: { q?: string; filters?: Record<string, unknown>; sort?: string[]; limit?: number; offset?: number }
) {
  return request<BuscaAvancadaResultado>(`/instrumentos/${id}/buscar-avancado`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getFacetas(id: string) {
  return request<FacetasResultado>(`/instrumentos/${id}/facetas`);
}

export function reindexarInstrumento(id: string) {
  return request<ReindexacaoJob>(`/instrumentos/${id}/reindexar`, { method: "POST" });
}
