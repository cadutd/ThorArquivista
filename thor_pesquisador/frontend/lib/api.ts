import { API_BASE_URL } from "@/lib/config";
import type { CursorPage, DashboardStats, Instrumento, InstrumentoCampo, Page, Registro } from "@/types/domain";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? "Falha na requisicao.");
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export function devLogin() {
  return request("/auth/dev-login", { method: "POST" });
}

export function getGovbrStart() {
  return request<{ authorization_url: string }>("/auth/govbr/start");
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

export function listInstrumentos(params: { q?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  search.set("limit", String(params.limit ?? 20));
  search.set("offset", String(params.offset ?? 0));
  if (params.q) search.set("q", params.q);
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

export function searchRegistros(id: string, q: string) {
  return request<CursorPage<Registro>>(`/instrumentos/${id}/buscar`, {
    method: "POST",
    body: JSON.stringify({ q, page_size: 50 })
  });
}

export function createRegistro(id: string, payload: { dados: Record<string, unknown>; status: string }) {
  return request<Registro>(`/instrumentos/${id}/registros`, { method: "POST", body: JSON.stringify(payload) });
}
