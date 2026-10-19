"use client";
import Link from "next/link";
import { useEffect,useRef,useState } from "react";
import { ArrowLeft,Search,SlidersHorizontal } from "lucide-react";
import { request } from "@/lib/api";
import { CrudPagination } from "./crud-pagination";
import { PortalShell } from "./portal-shell";

type RecordRow={id:string;titulo:string;dados:Record<string,unknown>};
type Field={chave:string;nome:string;tipo:string;filtro_avancado?:boolean};
export function PortalRecords({id}:{id:string}){return <PortalShell><Records id={id}/></PortalShell>;}
function Records({id}:{id:string}) {
  const [name,setName]=useState("Instrumento"),[fields,setFields]=useState<Field[]>([]);
  const [facets,setFacets]=useState<Record<string,Record<string,number>>>({});
  const [q,setQ]=useState(""),[filters,setFilters]=useState<Record<string,unknown>>({}),[draft,setDraft]=useState<Record<string,unknown>>({});
  const [applied,setApplied]=useState(""),[page,setPage]=useState(0),[size,setSize]=useState(20),[refresh,setRefresh]=useState(0);
  const [items,setItems]=useState<RecordRow[]>([]),[total,setTotal]=useState(0),[loading,setLoading]=useState(true),[error,setError]=useState("");
  const [advanced,setAdvanced]=useState(false),[fieldError,setFieldError]=useState("");
  const counted=useRef("");
  const path="/publico/instrumentos/"+id;
  useEffect(()=>{
    let live=true;setFieldError("");setFields([]);setFacets({});
    request<{nome:string;campos:Field[]}>(path).then(s=>{if(live){setName(s.nome);setFields(s.campos);}})
      .catch(e=>{if(live)setFieldError(e.message);});
    return()=>{live=false;};
  },[path]);
  useEffect(()=>{
    if(!advanced)return;
    let live=true;
    request<typeof facets>(path+"/facetas").then(f=>{if(live)setFacets(f);}).catch(e=>{if(live)setFieldError(e.message);});
    return()=>{live=false;};
  },[path,advanced]);
  useEffect(()=>{
    let live=true;setLoading(true);setError("");
    request<{items:RecordRow[];total:number}>(path+"/buscar?"+new URLSearchParams({
      q:applied,limit:String(size),offset:String(page*size),filtros:JSON.stringify(filters)}))
      .then(r=>{if(live){setItems(r.items);setTotal(r.total);
        if(counted.current!==id){counted.current=id;void request(path+"/acessos",{method:"POST"}).catch(()=>{counted.current="";});}
      }}).catch(e=>{if(live){setError(e.message);setItems([]);setTotal(0);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[path,id,applied,filters,page,size,refresh]);
  const pagination={total,pageIndex:page,pageSize:size,loading,onPageChange:setPage,onPageSizeChange:(size:number)=>{setSize(size);setPage(0);}};
  return <div className="portal-width portal-section stack">
    <div className="row"><div className="page-heading"><h1>{name}</h1><p className="muted">{loading?"Carregando...":total+" registros publicados"}</p></div>
      <Link className="button secondary" href="/consulta"><ArrowLeft size={16}/>Instrumentos</Link></div>
    <form className="stack" onSubmit={e=>{e.preventDefault();setApplied(q.trim());setFilters({...draft});setPage(0);setRefresh(v=>v+1);}}>
      <div className="row"><label className="field search-field"><span>Buscar registros publicados</span><input className="input" maxLength={1000} value={q} onChange={e=>setQ(e.target.value)}/></label>
        <div className="actions"><button className="button" type="submit" disabled={loading}><Search size={18}/>Buscar</button>
          <button className="icon-button" type="button" title="Filtros" aria-label="Filtros" aria-expanded={advanced} onClick={()=>setAdvanced(v=>!v)}><SlidersHorizontal size={18}/></button>
          <button className="button secondary" type="button" disabled={loading} onClick={()=>{setQ("");setApplied("");setDraft({});setFilters({});setPage(0);}}><SlidersHorizontal size={18}/>Limpar filtros</button></div></div>
      {advanced&&<div className="grid">{fields.filter(f=>facets["dados."+f.chave]||f.filtro_avancado).map(f=><label className="field" key={f.chave}><span>{f.nome}</span>
        {facets["dados."+f.chave]?<select className="select" value={draft[f.chave]===undefined?"":String(draft[f.chave])} onChange={e=>{
          const next={...draft};if(!e.target.value)delete next[f.chave];else next[f.chave]=f.tipo==="NUMERO"?Number(e.target.value):f.tipo==="BOOLEANO"?e.target.value==="true":e.target.value;
          setDraft(next);}}><option value="">Todos</option>{Object.entries(facets["dados."+f.chave]).map(([value,count])=><option key={value} value={value}>{value} ({count})</option>)}</select>:
        <input className="input" value={String(draft[f.chave]||"")} onChange={e=>{const next={...draft};if(e.target.value)next[f.chave]=e.target.value;else delete next[f.chave];setDraft(next);}}/>}
      </label>)}</div>}
    </form>
    {(error||fieldError)&&<p className="error" role="alert">{error||fieldError}</p>}
    <CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr><th>Registro</th><th>Metadados publicados</th></tr></thead><tbody>
      {items.map(row=><tr key={row.id}><td><Link className="crud-record-link" prefetch={false} href={"/consulta/"+id+"/"+encodeURIComponent(row.id)}>{row.titulo}</Link></td>
        <td className="break-text">{Object.values(row.dados).map(v=>typeof v==="object"?JSON.stringify(v):String(v)).join(" | ")}</td></tr>)}
      {!items.length&&<tr><td colSpan={2}>{loading?"Carregando...":error?"Consulta indisponivel.":"Nenhum registro publicado."}</td></tr>}
    </tbody></table></div>
    <CrudPagination {...pagination}/>
  </div>;
}
