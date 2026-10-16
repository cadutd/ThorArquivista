"use client";
import { useEffect,useState } from "react";
import { Save } from "lucide-react";
import { Permission } from "./permission";
import { request } from "@/lib/api";
type Hold={bloqueado:boolean;reter_ate:string|null;expurgo_iniciado_em:string|null;expurgado_em:string|null};

export function RetencaoRegistro({instrumentoId,registroId}:{instrumentoId:string;registroId:string}){
  return <Permission acao="retencao_editar" instrumentoId={instrumentoId}><HoldForm instrumentoId={instrumentoId} registroId={registroId}/></Permission>;
}

function HoldForm({instrumentoId,registroId}:{instrumentoId:string;registroId:string}){
  const path="/instrumentos/"+instrumentoId+"/registros/"+encodeURIComponent(registroId)+"/retencao";
  const [data,setData]=useState<Hold>(),[date,setDate]=useState(""),[error,setError]=useState(""),[saving,setSaving]=useState(false);
  const [message,setMessage]=useState("");
  useEffect(()=>{let live=true;request<Hold>(path).then(r=>{if(live){setData(r);setDate(r.reter_ate?new Date(new Date(r.reter_ate).getTime()-new Date(r.reter_ate).getTimezoneOffset()*60000).toISOString().slice(0,16):"");}}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[path]);
  async function save(){
    if(saving||!data)return;
    setSaving(true);setMessage("");setError("");
    try{await request(path,{method:"PUT",body:JSON.stringify({bloqueado:data.bloqueado,reter_ate:date?new Date(date).toISOString():null})});setMessage("Retencao atualizada.");}
    catch(e){setError(e instanceof Error?e.message:"Falha ao salvar.");}finally{setSaving(false);}
  }
  return <section className="stack"><h2>Retencao do registro</h2>{error&&<p className="error" role="alert">{error}</p>}
    {!data&&!error&&<p role="status">Carregando...</p>}
    {data&&<form className="stack" onSubmit={e=>{e.preventDefault();save();}}><fieldset className="administracao-form-fields" disabled={saving||!!data.expurgo_iniciado_em}>
      <div className="grid"><label className="administracao-active"><input type="checkbox" checked={data.bloqueado} onChange={e=>setData({...data,bloqueado:e.target.checked})}/>Bloquear expurgo</label>
      <label className="field"><span>Reter ate</span><input className="input" type="datetime-local" value={date} onChange={e=>setDate(e.target.value)}/></label></div>
      <div className="actions"><button className="button"><Save size={16}/>{saving?"Salvando...":"Salvar retencao"}</button></div>
    </fieldset>{message&&<p role="status">{message}</p>}{data.expurgo_iniciado_em&&<p role="status">Expurgo iniciado.</p>}</form>}
  </section>;
}
