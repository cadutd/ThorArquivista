"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { request } from "@/lib/api";
import { RegistroImagens } from "@/components/registro-imagens";
type RecordView = { titulo: string; dados: Record<string, unknown>; versao: number };
export default function PublicRecord() {
  const {id, registroId} = useParams<{ id: string; registroId: string }>();
  const path = "/publico/instrumentos/" + id + "/registros/" + encodeURIComponent(registroId);
  const [record, setRecord] = useState<RecordView>();
  const [tab, setTab] = useState("dados");
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true; setRecord(undefined);
    request<RecordView>(path).then(r => { if(current) setRecord(r); }).catch(e => { if(current) setError(e.message); });
    return () => { current = false; };
  }, [path]);
  return <main className="container stack"><header className="row"><h1>Thor Pesquisador</h1>
    <Link className="button secondary" href="/consulta"><ArrowLeft size={16}/>Consulta</Link></header>
    {error && <p className="error" role="alert">{error}</p>}
    {record && <><h2 className="break-text">{record.titulo}</h2><div className="tabs" role="tablist">
      <button role="tab" aria-selected={tab === "dados"} onClick={() => setTab("dados")}>Metadados</button>
      <button role="tab" aria-selected={tab === "imagens"} onClick={() => setTab("imagens")}>Imagens</button></div>
      {tab === "dados" ? <dl className="detail-grid">{Object.entries(record.dados).map(([key, value]) =>
        <div className="detail-item" key={key}><dt>{key}</dt><dd className="break-text">{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl> :
        <RegistroImagens instrumentoId={id} registroId={registroId} publico/>}</>}
  </main>;
}
