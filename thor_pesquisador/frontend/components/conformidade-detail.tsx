"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { ArrowLeft,RefreshCw } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { ConformidadeActions } from "./conformidade-actions";
import { request } from "@/lib/api";
import { Kind,Row,config,display } from "@/lib/conformidade-view";

const titles={auditoria:"Evento de auditoria",exportacoes:"Exportacao",politicas:"Politica de retencao",execucoes:"Execucao de retencao"};
const labels:Record<string,string>={id:"Identificador",entidade_id:"Entidade (id)",instrumento_id:"Instrumento (id)",
  instrumento_nome:"Instrumento",registro_id:"Registro",usuario_id:"Usuario (id)",request_id:"Request ID",operacao_id:"Operacao",
  detalhe:"Detalhes",erro:"Erro",checksum:"SHA-256",tamanho_bytes:"Tamanho (bytes)",tentativa:"Tentativa",expira_em:"Validade",
  atualizado_em:"Atualizacao",politica_id:"Politica (id)",permitir_expurgo:"Expurgo autorizado",corte_em:"Limite temporal",agente:"Responsavel"};
const fields:Record<Kind,string[]>={
  auditoria:["id","criado_em","acao","entidade","entidade_id","agente","usuario_id","fonte","instrumento_id","registro_id","request_id","operacao_id","detalhe"],
  exportacoes:["id","criado_em","atualizado_em","formato","escopo","status","instrumento_id","agente","processados","tentativa","expira_em","tamanho_bytes","checksum","erro"],
  politicas:["id","nome","categoria","dias","instrumento_nome","instrumento_id","ativo","permitir_expurgo","bloqueada"],
  execucoes:["id","criado_em","politica_id","instrumento_id","simulacao","status","agente","processados","elegiveis","bloqueados","removidos","corte_em","erro"]
};

export function ConformidadeDetail({tipo,id,fonte}:{tipo:Kind;id:string;fonte?:string}) {
  const cfg=config[tipo];
  const [data,setData]=useState<Row>(),[loading,setLoading]=useState(true),[error,setError]=useState(""),[refresh,setRefresh]=useState(0);
  useEffect(()=>{
    let live=true;setLoading(true);setError("");setData(undefined);
    const suffix=tipo==="auditoria"?encodeURIComponent(fonte||"")+"/"+encodeURIComponent(id):encodeURIComponent(id);
    request<Row>(cfg.path+"/"+suffix).then(r=>{if(live)setData(r);}).catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[cfg.path,tipo,id,fonte,refresh]);
  const values=data as unknown as Record<string,unknown>|undefined;
  return <AppShell><Permission acao={cfg.permission} anyScope><div className="stack conformidade-detail">
    <div className="row"><div className="page-heading"><h1>{data&&"nome" in data?data.nome:titles[tipo]}</h1></div>
      <div className="actions">
        <Link className="button secondary" href={cfg.path}><ArrowLeft size={16}/>Voltar</Link>
        <button className="icon-button" title="Atualizar" aria-label="Atualizar" disabled={loading} onClick={()=>setRefresh(v=>v+1)}><RefreshCw size={16}/></button>
        {data&&<ConformidadeActions tipo={tipo} row={data} onChanged={()=>setRefresh(v=>v+1)}/>}
      </div>
    </div>
    <section className="panel stack">
      {loading&&<p role="status">Carregando...</p>}
      {error&&<p className="error" role="alert">{error}</p>}
      {values&&<dl className="detail-grid">{fields[tipo].filter(key=>key in values).map(key=><div className="detail-item" key={key}>
        <dt>{labels[key]||cfg.columns.find(c=>c[0]===key)?.[1]||key}</dt>
        <dd>{key==="detalhe"?<pre>{display(key,values[key])}</pre>:<strong>{display(key,values[key])}</strong>}</dd>
      </div>)}</dl>}
    </section>
  </div></Permission></AppShell>;
}
