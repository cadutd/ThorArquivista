"use client";
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ExternalLink, X } from "lucide-react";
import { mediaUrl, type Imagem } from "@/lib/imagens";
import { ModalFrame } from "./modal-frame";

function safeHttp(value: unknown): string | null {
 if(typeof value!=="string") return null;
 try {const url=new URL(value);return ["http:","https:"].includes(url.protocol)?value:null;}catch{return null;}
}
export function MediaPreview({imagem,onClose}:{imagem:Imagem;onClose:()=>void}){
 const [pages,setPages]=useState<string[]>([]);const [page,setPage]=useState(0);const [error,setError]=useState("");const [loading,setLoading]=useState(false);
 useEffect(()=>{
  setPage(0);setError("");
  if(imagem.tipo_referencia!=="IIIF"){setPages([mediaUrl(imagem.uri)]);return;}
  setLoading(true);setPages([]);
  const controller=new AbortController();
  fetch(imagem.manifest_iiif_uri||imagem.uri,{signal:controller.signal})
   .then(r=>{if(!r.ok)throw new Error("Manifest IIIF indisponivel.");return r.json();})
   .then(manifest=>{
    const v2=manifest.sequences?.[0]?.canvases?.flatMap((c: {images?: {resource?:{"@id"?:string}}[]})=>c.images?.map(i=>i.resource?.["@id"])||[])||[];
    const v3=manifest.items?.flatMap((c: {items?:{items?:{body?:{id?:string}|{id?:string}[]}[]}[]})=>c.items?.flatMap(p=>p.items?.flatMap(i=>Array.isArray(i.body)?i.body.map(b=>b.id):[i.body?.id])||[])||[])||[];
    const urls=[...v2,...v3].map(safeHttp).filter((u):u is string=>!!u);
    if(!urls.length)throw new Error("Manifest sem imagens compativeis.");
    setPages(urls);
   }).catch(e=>{if(e.name!=="AbortError")setError(e.message);}).finally(()=>setLoading(false));
  return ()=>controller.abort();
 },[imagem]);
 return <ModalFrame title={imagem.titulo} onClose={onClose}>
  <div className="row"><strong>{imagem.titulo}</strong><div className="actions"><a className="icon-button" title="Abrir referencia" aria-label="Abrir referencia" href={mediaUrl(imagem.uri)} target="_blank" rel="noopener noreferrer"><ExternalLink size={16}/></a><button autoFocus className="icon-button" title="Fechar" aria-label="Fechar" onClick={onClose}><X size={16}/></button></div></div>
  {loading&&<p className="muted">Carregando...</p>}{error&&<p className="error">{error}</p>}
  {pages[page]&&<img className="media-large" src={pages[page]} alt={imagem.titulo} onError={()=>setError("Imagem indisponivel.")}/>}
  {pages.length>1&&<div className="row"><button className="icon-button" title="Imagem anterior" disabled={page===0} onClick={()=>setPage(page-1)}><ChevronLeft size={16}/></button><span>{page+1} de {pages.length}</span><button className="icon-button" title="Proxima imagem" disabled={page===pages.length-1} onClick={()=>setPage(page+1)}><ChevronRight size={16}/></button></div>}
 </ModalFrame>;
}
