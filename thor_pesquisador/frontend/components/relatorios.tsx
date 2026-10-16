"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { Search,SlidersHorizontal } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission,usePermission } from "./permission";
import { InstrumentoLookup } from "./instrumento-lookup";
import { request } from "@/lib/api";
import { date,states } from "@/lib/conformidade";
import { CrudPagination } from "./crud-pagination";

type Summary={instrumentos:Group[];registros:Group[];publicacoes:Group[];indexacao:Group[];exportacoes:Group[];imagens_orfas:number|null};
type Group={nome:string;total:number};

function queryFor(filters:Record<string,string>) {
  const query=new URLSearchParams();
  Object.entries(filters).forEach(([key,value])=>{if(value)query.set(key,["inicio","fim"].includes(key)?new Date(value).toISOString():value);});
  return query;
}

export function Relatorios() {
  const [draft,setDraft]=useState({inicio:"",fim:"",instrumento_id:""}),[filters,setFilters]=useState(draft),[name,setName]=useState("");
  const [data,setData]=useState<Summary>(),[loading,setLoading]=useState(true),[error,setError]=useState("");
  useEffect(()=>{
    let live=true;setLoading(true);setError("");
    request<Summary>("/relatorios?"+queryFor(filters)).then(r=>{if(live)setData(r);})
      .catch(e=>{if(live){setData(undefined);setError(e.message);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[filters]);
  const sections:[keyof Summary,string][]=[["instrumentos","Instrumentos por estado"],["registros","Registros por situacao"],["publicacoes","Publicacoes por periodo"],["indexacao","Jobs de indexacao"],["exportacoes","Jobs de exportacao"]];
  return <AppShell><Permission acao="relatorios_consultar" anyScope><div className="stack">
    <div className="row"><div className="page-heading"><h1>Relatorios</h1></div></div>
    <section className="panel stack">
      <form className="stack" onSubmit={e=>{e.preventDefault();setFilters({...draft});}}>
        <div className="grid">{(["inicio","fim"] as const).map(key=><label className="field" key={key}><span>{key==="inicio"?"Inicio":"Fim"}</span><input className="input" type="datetime-local" value={draft[key]} onChange={e=>setDraft({...draft,[key]:e.target.value})}/></label>)}</div>
        <InstrumentoLookup value={draft.instrumento_id} label={name} acao="relatorios_consultar" onChange={(value,label)=>{setDraft({...draft,instrumento_id:value});setName(label);}}/>
        <div className="actions">
          <button className="button" type="submit" disabled={loading}><Search size={18}/>Buscar</button>
          <button className="button secondary" type="button" disabled={loading} onClick={()=>{const value={inicio:"",fim:"",instrumento_id:""};setDraft(value);setFilters(value);setName("");}}><SlidersHorizontal size={18}/>Limpar filtros</button>
        </div>
      </form>
      {error&&<p role="alert" className="error">{error}</p>}
      {loading&&<p role="status">Carregando...</p>}
      {data&&<>
        {sections.map(([key,title])=><section className="stack" key={key}><div className="row"><h2>{title}</h2></div>
          <div className="table-wrap"><table className="table"><thead><tr><th>Situacao / periodo</th><th>Total</th></tr></thead><tbody>
            {(data[key] as Group[]).map(g=><tr key={g.nome}><td>{key==="publicacoes"?date(g.nome):states[g.nome]||g.nome}</td><td>{g.total}</td></tr>)}
            {!(data[key] as Group[]).length&&<tr><td colSpan={2}>Nenhum resultado encontrado.</td></tr>}
          </tbody></table></div>
        </section>)}
        {data.imagens_orfas!=null&&<section><h2>Imagens sem vinculos atuais ou historicos</h2><p>{data.imagens_orfas}</p></section>}
        <PagedReport title="Registros por instrumento" endpoint="registros" filters={filters} columns={[["nome","Instrumento"],["total","Registros"]]}/>
        <Permission acao="relatorios_consultar"><Permission acao="usuarios_consultar"><Permission acao="auditoria_consultar">
          <PagedReport title="Alteracoes de usuarios" endpoint="usuarios" filters={filters} columns={[["criado_em","Data"],["acao","Acao"],["entidade_id","Usuario (id)"],["agente","Responsavel"]]}/>
        </Permission></Permission></Permission>
      </>}
    </section>
  </div></Permission></AppShell>;
}

function PagedReport({title,endpoint,filters,columns}:{title:string;endpoint:string;filters:Record<string,string>;columns:[string,string][]}){
  const [rows,setRows]=useState<Record<string,unknown>[]>([]),[total,setTotal]=useState(0);
  const [paginationState,setPagination]=useState({page:0,size:20,filters});
  const {size}=paginationState,page=filters===paginationState.filters?paginationState.page:0;
  const [loading,setLoading]=useState(true),[error,setError]=useState("");
  useEffect(()=>{
    let live=true;setLoading(true);
    const query=queryFor(filters);query.set("limit",String(size));query.set("offset",String(page*size));
    request<{items:typeof rows;total:number}>("/relatorios/"+endpoint+"?"+query).then(r=>{if(live){setRows(r.items);setTotal(r.total);setError("");}})
      .catch(e=>{if(live){setError(e.message);setRows([]);setTotal(0);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[endpoint,filters,page,size]);
  const pagination={total,pageIndex:page,pageSize:size,loading,onPageChange:(page:number)=>setPagination({page,size,filters}),onPageSizeChange:(size:number)=>setPagination({page:0,size,filters})};
  return <section className="stack"><div className="row"><div className="page-heading"><h2>{title}</h2><p className="muted">{loading?"Carregando...":total+" registros encontrados"}</p></div></div>
    {error&&<p role="alert" className="error">{error}</p>}<CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr>{columns.map(([key,label])=><th key={key}>{label}</th>)}</tr></thead><tbody>
      {rows.map(row=><tr key={String(row.id)}>{columns.map(([key],index)=><td key={key}>{index===0?<ReportLink row={row} endpoint={endpoint} value={key==="criado_em"?date(String(row[key])):String(row[key]??"-")}/>:String(row[key]??"-")}</td>)}</tr>)}
      {!rows.length&&<tr><td colSpan={columns.length}>{loading?"Carregando...":error?"Listagem indisponivel.":"Nenhum resultado encontrado."}</td></tr>}
    </tbody></table></div><CrudPagination {...pagination}/>
  </section>;
}

function ReportLink({row,endpoint,value}:{row:Record<string,unknown>;endpoint:string;value:string}) {
  const canRead=usePermission("instrumentos_consultar",String(row.id));
  if(endpoint==="registros"&&!canRead)return <>{value}</>;
  return <Link className="crud-record-link" href={endpoint==="registros"?"/instrumentos/"+row.id:"/auditoria/geral/"+row.id}>{value}</Link>;
}
