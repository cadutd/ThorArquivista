"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { ArrowLeft,Eye,List,Plus,RefreshCw,Search,SlidersHorizontal } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { CrudPagination } from "./crud-pagination";
import { ConformidadeActions } from "./conformidade-actions";
import { request } from "@/lib/api";
import { categories,states } from "@/lib/conformidade";
import { Kind,Row,config,detailPath,display } from "@/lib/conformidade-view";

export function ConformidadeList({tipo}:{tipo:Kind}) {
  const cfg=config[tipo];
  const [rows,setRows]=useState<Row[]>([]),[total,setTotal]=useState(0),[page,setPage]=useState(0),[size,setSize]=useState(20);
  const [draft,setDraft]=useState<Record<string,string>>({q:""}),[filters,setFilters]=useState(draft);
  const [advanced,setAdvanced]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(""),[refresh,setRefresh]=useState(0);
  useEffect(()=>{
    let live=true;setLoading(true);
    const params=new URLSearchParams({limit:String(size),offset:String(page*size)});
    Object.entries(filters).forEach(([key,value])=>{if(value)params.set(key,["inicio","fim"].includes(key)?new Date(value).toISOString():value);});
    request<{items:Row[];total:number}>(cfg.path+"?"+params).then(r=>{
      if(live){setRows(r.items);setTotal(r.total);setError("");
        if(page>0&&page*size>=r.total)setPage(Math.max(0,Math.ceil(r.total/size)-1));
      }
    }).catch(e=>{if(live){setError(e.message);setRows([]);setTotal(0);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[cfg.path,filters,page,size,refresh]);
  const pagination={total,pageIndex:page,pageSize:size,loading,onPageChange:setPage,onPageSizeChange:(n:number)=>{setSize(n);setPage(0);}};
  return <AppShell><Permission acao={cfg.permission} anyScope><div className="stack">
    <div className="row">
      <div className="page-heading"><h1>{cfg.title}</h1><p className="muted">{loading?"Carregando...":total+" registros encontrados"}</p></div>
      <div className="actions">
        {tipo==="exportacoes"&&<Permission acao="exportacoes_incluir" anyScope><Link className="button" href="/exportacoes/nova"><Plus size={18}/>Nova exportacao</Link></Permission>}
        {tipo==="politicas"&&<><Link className="button secondary" href="/retencao/execucoes"><List size={16}/>Execucoes</Link><Permission acao="retencao_incluir" anyScope><Link className="button" href="/retencao/politicas/nova"><Plus size={18}/>Nova politica</Link></Permission></>}
        {tipo==="execucoes"&&<Link className="button secondary" href="/retencao/politicas"><ArrowLeft size={16}/>Voltar</Link>}
        <button className="icon-button" title="Atualizar" aria-label="Atualizar" disabled={loading} onClick={()=>setRefresh(v=>v+1)}><RefreshCw size={16}/></button>
      </div>
    </div>
    <section className="panel stack">
      <form className="stack crud-search-form" onSubmit={e=>{e.preventDefault();setFilters({...draft});setPage(0);setRefresh(v=>v+1);}}>
        <div className="row">
          <label className="field search-field"><span>Busca simples</span><input className="input" placeholder="Buscar registros" value={draft.q||""} onChange={e=>setDraft({...draft,q:e.target.value})}/></label>
          <div className="actions">
            <button className="button" type="submit" disabled={loading}><Search size={18}/>Buscar</button>
            <button className="icon-button" type="button" title="Filtros avancados" aria-label="Filtros avancados" aria-expanded={advanced} aria-controls="conformidade-filtros" onClick={()=>setAdvanced(v=>!v)}><SlidersHorizontal size={18}/></button>
            <button className="button secondary" type="button" disabled={loading} onClick={()=>{setDraft({q:""});setFilters({q:""});setPage(0);}}><SlidersHorizontal size={18}/>Limpar filtros</button>
          </div>
        </div>
      {advanced&&<div className="grid" id="conformidade-filtros">
        {tipo==="auditoria"&&[["acao","Acao"],["usuario_id","Usuario (UUID)"],["entidade","Entidade"],["instrumento_id","Instrumento (UUID)"],["inicio","Inicio"],["fim","Fim"]].map(([key,label])=><label className="field" key={key}><span>{label}</span><input className="input" type={["inicio","fim"].includes(key)?"datetime-local":"text"} value={draft[key]||""} onChange={e=>setDraft({...draft,[key]:e.target.value})}/></label>)}
        {(tipo==="exportacoes"||tipo==="execucoes")&&<label className="field"><span>Situacao</span><select className="select" value={draft.status||""} onChange={e=>setDraft({...draft,status:e.target.value})}><option value="">Todas</option>{Object.entries(states).filter(([key])=>tipo==="exportacoes"||!["EXPIRADA","DESCARTADA"].includes(key)).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>}
        {tipo==="politicas"&&<><label className="field"><span>Categoria</span><select className="select" value={draft.categoria||""} onChange={e=>setDraft({...draft,categoria:e.target.value})}><option value="">Todas</option>{Object.entries(categories).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
          <label className="field"><span>Situacao</span><select className="select" value={draft.ativo||""} onChange={e=>setDraft({...draft,ativo:e.target.value})}><option value="">Todas</option><option value="true">Ativo</option><option value="false">Inativo</option></select></label></>}
      </div>}

      </form>
      {error&&<p className="error" role="alert">{error}</p>}
      <CrudPagination {...pagination}/>
      <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr>{cfg.columns.map(([key,label])=><th key={key}>{label}</th>)}<th className="crud-actions-heading">Acoes</th></tr></thead><tbody>
        {rows.map(row=><tr key={("fonte" in row?row.fonte:"")+row.id}>{cfg.columns.map(([key],index)=><td key={key}>{index===0?
          <Link className="crud-record-link" href={detailPath(tipo,row)}>{display(key,(row as unknown as Record<string,unknown>)[key])}</Link>:display(key,(row as unknown as Record<string,unknown>)[key])}</td>)}
          <td><div className="actions"><Link className="icon-button" title="Visualizar" aria-label="Visualizar" href={detailPath(tipo,row)}><Eye size={16}/></Link><ConformidadeActions tipo={tipo} row={row} onChanged={()=>setRefresh(v=>v+1)}/></div></td></tr>)}
        {!rows.length&&<tr><td colSpan={cfg.columns.length+1}>{loading?"Carregando...":error?"Listagem indisponivel.":"Nenhum registro encontrado."}</td></tr>}
      </tbody></table></div>
      <CrudPagination {...pagination}/>
    </section>
  </div></Permission></AppShell>;
}
