"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { useSearchParams } from "next/navigation";
import { Eye,Search,SlidersHorizontal } from "lucide-react";
import { request } from "@/lib/api";
import { CatalogItem,types } from "@/lib/portal";
import { PortalShell } from "./portal-shell";
import { CrudPagination } from "./crud-pagination";

export function PortalCatalog(){return <PortalShell><Catalog/></PortalShell>;}
function Catalog(){
  const search=useSearchParams();
  const empty={q:"",nome:"",tipo:"",descricao:""};
  const [draft,setDraft]=useState({...empty,q:search.get("q")||""}),[filters,setFilters]=useState(draft);
  const [items,setItems]=useState<CatalogItem[]>([]),[total,setTotal]=useState(0),[page,setPage]=useState(0),[size,setSize]=useState(20);
  const [advanced,setAdvanced]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState("");
  useEffect(()=>{
    let live=true;setLoading(true);setError("");
    request<{items:CatalogItem[];total:number}>("/publico/instrumentos?"+new URLSearchParams({...filters,limit:String(size),offset:String(page*size)}))
      .then(r=>{if(live){setItems(r.items);setTotal(r.total);}})
      .catch(e=>{if(live){setError(e.message);setItems([]);setTotal(0);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[filters,page,size]);
  const pagination={total,pageIndex:page,pageSize:size,loading,onPageChange:setPage,onPageSizeChange:(size:number)=>{setSize(size);setPage(0);}};
  return <div className="portal-width portal-section stack">
    <div className="page-heading"><h1>Instrumentos de pesquisa</h1><p className="muted">{loading?"Carregando...":total+" instrumentos encontrados"}</p></div>
    <section className="panel stack">
    <form className="stack" onSubmit={e=>{e.preventDefault();setFilters({...draft,q:draft.q.trim(),nome:draft.nome.trim(),descricao:draft.descricao.trim()});setPage(0);}}>
      <div className="row">
        <label className="field search-field"><span>Busca simples</span><input className="input" placeholder="Nome ou descricao" maxLength={150} value={draft.q} onChange={e=>setDraft({...draft,q:e.target.value})}/></label>
        <div className="actions"><button className="button" type="submit" disabled={loading}><Search size={18}/>Buscar</button>
          <button className="icon-button" type="button" title="Filtros avancados" aria-label="Filtros avancados" aria-expanded={advanced} onClick={()=>setAdvanced(v=>!v)}><SlidersHorizontal size={18}/></button>
          <button className="button secondary" type="button" disabled={loading} onClick={()=>{setDraft(empty);setFilters(empty);setPage(0);}}><SlidersHorizontal size={18}/>Limpar filtros</button></div>
      </div>
      {advanced&&<div className="grid">
        <label className="field"><span>Nome</span><input className="input" value={draft.nome} maxLength={255} onChange={e=>setDraft({...draft,nome:e.target.value})}/></label>
        <label className="field"><span>Tipo</span><select className="select" value={draft.tipo} onChange={e=>setDraft({...draft,tipo:e.target.value})}><option value="">Todos</option>{Object.entries(types).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
        <label className="field"><span>Descricao</span><input className="input" value={draft.descricao} maxLength={1000} onChange={e=>setDraft({...draft,descricao:e.target.value})}/></label>
      </div>}
    </form>
    {error&&<p className="error" role="alert">{error}</p>}
    <CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr><th>Nome</th><th>Tipo</th><th>Descricao</th><th className="crud-actions-heading">Acoes</th></tr></thead>
      <tbody>{items.map(item=><tr key={item.id}><td><Link className="crud-record-link" prefetch={false} href={"/consulta/"+item.id}>{item.nome}</Link></td>
        <td>{types[item.tipo]||item.tipo}</td><td className="break-text">{item.descricao||"-"}</td>
        <td className="crud-actions-cell"><Link className="icon-button" title="Consultar registros" aria-label="Consultar registros" prefetch={false} href={"/consulta/"+item.id}><Eye size={16}/></Link></td></tr>)}
        {!items.length&&<tr><td colSpan={4}>{loading?"Carregando...":error?"Consulta indisponivel.":"Nenhum instrumento encontrado."}</td></tr>}
      </tbody></table></div>
    <CrudPagination {...pagination}/>
    </section>
  </div>;
}
