"use client";
import Link from "next/link";
import { ArrowLeft, Edit } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect,useState } from "react";
import { AppShell } from "@/components/app-shell";
import { RegistroImagens } from "@/components/registro-imagens";
import { EditorialPanel } from "@/components/editorial-panel";
import { RetencaoRegistro } from "@/components/retencao-registro";
import { Permission } from "@/components/permission";
import { getSchema } from "@/lib/api";
import { getRegistro } from "@/lib/imagens";
import type { Registro,InstrumentoCampo } from "@/types/domain";
export default function RegistroDetail(){
 const {id,registroId}=useParams<{id:string;registroId:string}>();const [registro,setRegistro]=useState<Registro>();const [campos,setCampos]=useState<InstrumentoCampo[]>([]);const [error,setError]=useState("");const [tab,setTab]=useState("metadados");
 useEffect(()=>{Promise.all([getRegistro(id,registroId),getSchema(id)]).then(([r,s])=>{setRegistro(r);setCampos(s.campos);}).catch(e=>setError(e.message));if(new URLSearchParams(window.location.search).get("aba")==="imagens")setTab("imagens");},[id,registroId]);
 return <AppShell><div className="stack"><div className="row"><div className="page-heading"><h1>Registro</h1><p>{registro?.status||""}</p></div><Link className="button secondary" href={"/instrumentos/"+id+"/registros"}><ArrowLeft size={16}/>Voltar</Link></div>
 <Permission acao="registros_editar" instrumentoId={id}><Link className="button" href={"/instrumentos/"+id+"/registros/"+encodeURIComponent(registroId)+"/editar"}><Edit size={16}/>Editar</Link></Permission>
 {error?<p className="error">{error}</p>:!registro?<p className="muted">Carregando...</p>:<>
 <div className="tabs" role="tablist"><button role="tab" aria-selected={tab==="metadados"} onClick={()=>setTab("metadados")}>Metadados</button><button role="tab" aria-selected={tab==="imagens"} onClick={()=>setTab("imagens")}>Imagens</button></div>
 <section className="panel" role="tabpanel">{tab==="imagens"?<RegistroImagens instrumentoId={id} registroId={registroId} readonly={registro.status_editorial!=="RASCUNHO"} onChange={()=>getRegistro(id,registroId).then(setRegistro).catch(e=>setError(e.message))}/>:<div className="detail-grid">{campos.map(c=><div className="detail-item" key={c.id}><span>{c.nome}</span><strong className="break-text">{format(registro.dados[c.chave])}</strong></div>)}</div>}</section>
 <EditorialPanel instrumentoId={id} registroId={registroId} status={registro.status_editorial}
   versao={registro.versao} onChange={()=>getRegistro(id,registroId).then(setRegistro).catch(e=>setError(e.message))}/>
 <RetencaoRegistro instrumentoId={id} registroId={registroId}/>
 </>}
 </div></AppShell>;
}
function format(v:unknown):string {if(v===null||v===undefined||v==="")return "-";if(typeof v==="boolean")return v?"Sim":"Nao";if(Array.isArray(v))return v.map(format).join(", ");if(typeof v==="object")return JSON.stringify(v);return String(v);}
