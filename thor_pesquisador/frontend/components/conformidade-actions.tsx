"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Download,Edit,Pause,Play,RefreshCw,Trash2 } from "lucide-react";
import { Permission } from "./permission";
import { AdministracaoDetails } from "./administracao-details";
import { downloadFile,request } from "@/lib/api";
import { ExportJob,Policy,RetentionJob } from "@/lib/conformidade";
import { Kind,Row,config } from "@/lib/conformidade-view";

export function ConformidadeActions({tipo,row,onChanged}:{tipo:Kind;row:Row;onChanged?:()=>void}) {
  const router=useRouter();
  const cfg=config[tipo];
  const [busy,setBusy]=useState(false),[error,setError]=useState("");
  const [confirmation,setConfirmation]=useState<{row:Row;action:string;label:string}>();
  async function command(row:Row,action:string) {
    setBusy(true);setError("");
    try {
      if(action==="download") await downloadFile("/exportacoes/"+row.id+"/download","exportacao-"+row.id+((row as ExportJob).formato==="CSV"?".csv":".json"));
      else if(action==="simular"||action==="executar") {
        const job=await request<RetentionJob>("/retencao/politicas/"+row.id+"/execucoes",{
          method:"POST",body:JSON.stringify({operacao_id:crypto.randomUUID(),simulacao:action==="simular"})});
        setConfirmation(undefined);router.push("/retencao/execucoes/"+job.id);
        return;
      }
      else await request(cfg.path+"/"+row.id+(action==="repetir"?"/repetir":""),{method:action==="repetir"?"POST":"DELETE"});
      setConfirmation(undefined);onChanged?.();
    } catch(e){setError(e instanceof Error?e.message:"Falha na operacao.");}
    finally{setBusy(false);}
  }
  function actions(row:Row) {
    if(tipo==="exportacoes") {
      const j=row as ExportJob;
      return <>
        {j.status==="CONCLUIDA"&&Date.parse(j.expira_em)>Date.now()&&<button className="icon-button" disabled={busy} title="Baixar arquivo" aria-label="Baixar arquivo" onClick={()=>command(row,"download")}><Download size={16}/></button>}
        {j.status==="FALHOU"&&<Permission acao="exportacoes_repetir" instrumentoId={j.instrumento_id}><button className="icon-button" disabled={busy} title="Repetir" aria-label="Repetir" onClick={()=>command(row,"repetir")}><RefreshCw size={16}/></button></Permission>}
        {["PENDENTE","PROCESSANDO","FALHOU","CONCLUIDA"].includes(j.status)&&<Permission acao="exportacoes_excluir" instrumentoId={j.instrumento_id}>
          <button className="icon-button danger" disabled={busy} title={["PENDENTE","PROCESSANDO"].includes(j.status)?"Cancelar":"Descartar arquivo"}
            aria-label={["PENDENTE","PROCESSANDO"].includes(j.status)?"Cancelar":"Descartar arquivo"}
            onClick={()=>setConfirmation({row,action:"cancelar",label:["PENDENTE","PROCESSANDO"].includes(j.status)?"Cancelar exportacao":"Descartar arquivo"})}><Trash2 size={16}/></button></Permission>}
      </>;
    }
    if(tipo==="politicas"){
      const p=row as Policy;
      return <>
        <Permission acao="retencao_editar" instrumentoId={p.instrumento_id||undefined}><Link className="icon-button" title="Editar" aria-label="Editar" href={"/retencao/politicas/"+p.id+"/editar"}><Edit size={16}/></Link></Permission>
        {p.ativo&&!p.bloqueada&&<Permission acao="retencao_simular" instrumentoId={p.instrumento_id||undefined}><button className="icon-button" disabled={busy} title="Simular" aria-label="Simular" onClick={()=>command(row,"simular")}><Play size={16}/></button></Permission>}
        {p.ativo&&!p.bloqueada&&p.permitir_expurgo&&<Permission acao="retencao_executar" instrumentoId={p.instrumento_id||undefined}><button className="icon-button danger" disabled={busy} title="Executar retencao" aria-label="Executar retencao" onClick={()=>setConfirmation({row,action:"executar",label:"Executar retencao definitiva"})}><Trash2 size={16}/></button></Permission>}
        {p.ativo&&<Permission acao="retencao_excluir" instrumentoId={p.instrumento_id||undefined}><button className="icon-button" disabled={busy} title="Desativar" aria-label="Desativar" onClick={()=>setConfirmation({row,action:"desativar",label:"Desativar politica"})}><Pause size={16}/></button></Permission>}
      </>;
    }
    if(tipo==="execucoes") {
      const j=row as RetentionJob;
      return <>
        {j.status==="FALHOU"&&<Permission acao={j.simulacao?"retencao_simular":"retencao_executar"} instrumentoId={j.instrumento_id||undefined}><button className="icon-button" title="Repetir" aria-label="Repetir" disabled={busy} onClick={()=>command(row,"repetir")}><RefreshCw size={16}/></button></Permission>}
        {["PENDENTE","PROCESSANDO"].includes(j.status)&&<Permission acao="retencao_cancelar" instrumentoId={j.instrumento_id||undefined}><button className="icon-button" title="Cancelar" aria-label="Cancelar" disabled={busy} onClick={()=>setConfirmation({row,action:"cancelar",label:"Cancelar execucao"})}><Pause size={16}/></button></Permission>}
      </>;
    }
  }

  return <>{actions(row)}
    {error&&!confirmation&&<span className="error" role="alert">{error}</span>}
    {confirmation&&<AdministracaoDetails title={confirmation.label} onClose={()=>!busy&&setConfirmation(undefined)}
      fields={[["Confirmacao",confirmation.label+"?"]]} error={error} actions={<><button className="button secondary" disabled={busy} onClick={()=>setConfirmation(undefined)}>Voltar</button><button className="button administracao-delete" disabled={busy} onClick={()=>command(confirmation.row,confirmation.action)}><Trash2 size={16}/>{busy?"Processando...":"Confirmar"}</button></>}/>}

  </>;
}
