"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { request } from "@/lib/api";
import { RegistroImagens } from "@/components/registro-imagens";
import { PortalShell } from "@/components/portal-shell";
type RecordView = { titulo: string; dados: Record<string, unknown>; versao: number };
export default function PublicRecord() {
  const {id, registroId} = useParams<{ id: string; registroId: string }>();
  const path = "/publico/instrumentos/" + id + "/registros/" + encodeURIComponent(registroId);
  const [record, setRecord] = useState<RecordView>();
  const [tab, setTab] = useState("dados");
  const [error, setError] = useState("");
  function selectTab(next:string){
    setTab(next);requestAnimationFrame(()=>document.getElementById("public-tab-"+next)?.focus());
  }
  useEffect(() => {
    let current = true; setRecord(undefined);
    request<RecordView>(path).then(r => { if(current) setRecord(r); }).catch(e => { if(current) setError(e.message); });
    return () => { current = false; };
  }, [path]);
  return <PortalShell><div className="portal-width portal-section stack"><header className="row"><div className="page-heading"><h1>{record?.titulo||"Registro publicado"}</h1></div>
    <Link className="button secondary" href={"/consulta/"+id}><ArrowLeft size={16}/>Consulta</Link></header>
    {error && <p className="error" role="alert">{error}</p>}
    {!record&&!error&&<p role="status">Carregando...</p>}
    {record && <><p className="muted">Versao publicada: {record.versao}</p><div className="tabs" role="tablist" aria-label="Dados do registro"
      onKeyDown={e=>{if(["ArrowRight","ArrowLeft","Home","End"].includes(e.key)){e.preventDefault();selectTab(e.key==="Home"?"dados":e.key==="End"?"imagens":tab==="dados"?"imagens":"dados");}}}>
      <button role="tab" id="public-tab-dados" aria-controls="public-panel-dados" tabIndex={tab==="dados"?0:-1} aria-selected={tab === "dados"} onClick={() => selectTab("dados")}>Metadados</button>
      <button role="tab" id="public-tab-imagens" aria-controls="public-panel-imagens" tabIndex={tab==="imagens"?0:-1} aria-selected={tab === "imagens"} onClick={() => selectTab("imagens")}>Imagens</button></div>
      <div role="tabpanel" id={"public-panel-"+tab} aria-labelledby={"public-tab-"+tab}>
      {tab === "dados" ? <dl className="detail-grid">{Object.entries(record.dados).map(([key, value]) =>
        <div className="detail-item" key={key}><dt>{key}</dt><dd className="break-text">{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl> :
        <RegistroImagens instrumentoId={id} registroId={registroId} publico/>}</div></>}
  </div></PortalShell>;
}
