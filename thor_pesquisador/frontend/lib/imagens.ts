import { API_BASE_URL } from "./config";
import type { Page, Registro } from "@/types/domain";

export type Imagem = {
  id: string; titulo: string; descricao: string | null;
  tipo_referencia: "UPLOAD" | "URL" | "IIIF" | "REPOSITORIO_EXTERNO";
  uri: string; thumbnail_uri: string | null; manifest_iiif_uri: string | null;
  mime_type: string | null; tamanho_bytes: number | null; largura: number | null; altura: number | null;
  checksum_sha256: string | null; direitos_acesso: "PUBLICO" | "INTERNO" | "RESTRITO";
  metadados_json: Record<string, unknown>; criado_por: string | null;
  criado_em: string; atualizado_em: string;
};
export type ImagemPayload = Pick<Imagem, "titulo" | "descricao" | "tipo_referencia" | "uri" | "thumbnail_uri" | "manifest_iiif_uri" | "direitos_acesso" | "metadados_json">;
export type VinculoImagem = { instrumento_id: string; registro_id: string; imagem_id: string; ordem: number; principal: boolean; legenda: string | null; imagem: Imagem };

export async function imageRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    ...init, credentials: "include",
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((e: {msg: string}) => e.msg).join("; ") : body.detail;
    throw new Error(detail || "Falha na requisicao.");
  }
  if(response.status === 204) return undefined as T;
  return response.json();
}

export function mediaUrl(uri: string | null) {
  if(!uri) return "";
  return uri.startsWith("/api/v1/") ? new URL(API_BASE_URL).origin + uri : uri;
}
export const listImagens = (params: Record<string, string>) => imageRequest<Page<Imagem>>("/imagens?" + new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([,v])=>v!==""))));
export const getImagem = (id: string) => imageRequest<Imagem>("/imagens/" + id);
export const createImagem = (payload: ImagemPayload) => imageRequest<Imagem>("/imagens", {method:"POST",body:JSON.stringify(payload)});
export const updateImagem = (id: string, payload: Omit<ImagemPayload, "tipo_referencia">) => imageRequest<Imagem>("/imagens/"+id, {method:"PUT",body:JSON.stringify(payload)});
export const deleteImagem = (id: string) => imageRequest<void>("/imagens/"+id, {method:"DELETE"});
export const uploadImagem = (data: FormData) => imageRequest<Imagem>("/imagens/upload", {method:"POST",body:data});
const prefix = (i: string, r: string) => "/instrumentos/"+i+"/registros/"+encodeURIComponent(r)+"/imagens";
export const listVinculos = (i: string, r: string, offset=0, limit=20) => imageRequest<Page<VinculoImagem>>(prefix(i,r)+"?limit="+limit+"&offset="+offset);
export const vincularImagem = (i: string, r: string, imagem_id: string) => imageRequest<VinculoImagem>(prefix(i,r), {method:"POST",body:JSON.stringify({imagem_id})});
export const editarVinculo = (i: string, r: string, id: string, payload: {legenda?:string|null;principal?:boolean}) => imageRequest<VinculoImagem>(prefix(i,r)+"/"+id, {method:"PATCH",body:JSON.stringify(payload)});
export const reordenarImagens = (i: string, r: string, items: {imagem_id:string;ordem:number}[]) => imageRequest<void>(prefix(i,r)+"/reordenar", {method:"PATCH",body:JSON.stringify({items})});
export const desvincularImagem = (i: string, r: string, id: string) => imageRequest<void>(prefix(i,r)+"/"+id, {method:"DELETE"});
export const getRegistro = (i: string, r: string) => imageRequest<Registro>("/instrumentos/"+i+"/registros/"+encodeURIComponent(r));
