"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { RegistroForm } from "@/components/registro-form";
import { getSchema, request } from "@/lib/api";
import { getRegistro } from "@/lib/imagens";
import type { Registro, InstrumentoCampo } from "@/types/domain";
export default function EditRecord() {
  const {id, registroId} = useParams<{id: string; registroId: string}>();
  const router = useRouter();
  const [record, setRecord] = useState<Registro>();
  const [fields, setFields] = useState<InstrumentoCampo[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [nome, setNome] = useState("");
  const base = "/instrumentos/" + id + "/registros";
  const path = "/instrumentos/" + id + "/registros/" + encodeURIComponent(registroId);
  useEffect(() => {
    let current = true;
    setRecord(undefined); setFields([]); setError("");
    Promise.all([getRegistro(id, registroId), getSchema(id)]).then(([r, s]) => {
      if(current) { setRecord(r); setFields(s.campos); setNome(s.nome); }
    }).catch(e => { if(current) setError(e.message); });
    return () => { current = false; };
  }, [id, registroId]);
  async function save(dados: Record<string, unknown>) {
    if(!record) return;
    setBusy(true); setError("");
    try {
      await request(path, {method: "PUT", body: JSON.stringify({
        dados,
        versao: record.versao, status: record.status,
      })});
      router.push(base);
    } catch(e) { setError(e instanceof Error ? e.message : "Falha ao salvar."); }
    finally { setBusy(false); }
  }
  return <AppShell><div className="stack"><div className="row"><div className="page-heading"><h1>Editar registro</h1><p className="muted">{nome}</p></div>
    <Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link></div>
    {!record && error && <p className="error">{error}</p>}
    {!record && !error && <section className="panel"><p className="muted">Carregando...</p></section>}
    {record && (record.status === "EXCLUIDO" || record.status_editorial === "ARQUIVADO") ?
      <section className="panel"><p className="error">Registro excluido ou arquivado nao pode ser editado diretamente.</p></section> :
    <Permission acao="registros_editar" instrumentoId={id}>{record && <RegistroForm key={registroId} campos={fields}
      initial={record.dados} onSubmit={save} saving={busy} error={error}/>}</Permission>
    }
  </div></AppShell>;
}
