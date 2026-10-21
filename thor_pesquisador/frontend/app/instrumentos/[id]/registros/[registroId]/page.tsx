"use client";

import Link from "next/link";
import { ArrowLeft, Edit, Trash2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { RegistroImagens } from "@/components/registro-imagens";
import { EditorialPanel } from "@/components/editorial-panel";
import { RetencaoRegistro } from "@/components/retencao-registro";
import { Permission } from "@/components/permission";
import { deleteRegistro, getSchema } from "@/lib/api";
import { getRegistro } from "@/lib/imagens";
import type { Registro, InstrumentoCampo } from "@/types/domain";

export default function RegistroDetail() {
  const { id, registroId } = useParams<{ id: string; registroId: string }>();
  const router = useRouter();
  const [registro, setRegistro] = useState<Registro>();
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [nome, setNome] = useState("");
  const [error, setError] = useState("");
  const [tab, setTab] = useState("metadados");
  const [removing, setRemoving] = useState(false);
  const base = "/instrumentos/" + id + "/registros";
  const path = base + "/" + encodeURIComponent(registroId);

  useEffect(() => {
    let current = true;
    setRegistro(undefined); setError("");
    Promise.all([getRegistro(id, registroId), getSchema(id)]).then(([record, schema]) => {
      if (current) { setRegistro(record); setCampos(schema.campos); setNome(schema.nome); }
    }).catch(err => { if (current) setError(err instanceof Error ? err.message : "Falha ao carregar registro."); });
    setTab(new URLSearchParams(window.location.search).get("aba") === "imagens" ? "imagens" : "metadados");
    return () => { current = false; };
  }, [id, registroId]);

  function refresh() {
    getRegistro(id, registroId).then(setRegistro).catch(err => setError(err.message));
  }

  async function remove() {
    if (removing || !window.confirm("Excluir este registro? Seu historico sera preservado e ele deixara de aparecer na consulta.")) return;
    setRemoving(true); setError("");
    try { await deleteRegistro(id, registroId); router.push(base); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao excluir registro."); }
    finally { setRemoving(false); }
  }

  return <AppShell><div className="stack">
    <div className="row">
      <div className="page-heading"><h1>Registro</h1><p className="muted">{nome}</p></div>
      <div className="actions">
        <Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link>
        {registro && registro.status !== "EXCLUIDO" && <>
          {registro.status_editorial !== "ARQUIVADO" && <Permission acao="registros_editar" instrumentoId={id}>
            <Link className="button secondary" title="Editar registro" href={path + "/editar"}><Edit size={16}/>Editar</Link>
          </Permission>}
          <Permission acao="registros_excluir" instrumentoId={id}>
            <button className="button danger" type="button" title="Excluir registro" disabled={removing} onClick={remove}>
              <Trash2 size={16}/>{removing ? "Excluindo..." : "Excluir"}
            </button>
          </Permission>
        </>}
      </div>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {!registro && !error && <section className="panel"><p className="muted">Carregando...</p></section>}
    {registro && <>
      <section className="panel"><div className="detail-grid">
        <Detail label="Status" value={registro.status}/>
        <Detail label="Status editorial" value={registro.status_editorial}/>
        <Detail label="Versao" value={String(registro.versao)}/>
        <Detail label="Criado em" value={new Date(registro.criado_em).toLocaleString("pt-BR")}/>
        <Detail label="Atualizado em" value={new Date(registro.atualizado_em).toLocaleString("pt-BR")}/>
      </div></section>
      <div className="tabs" role="tablist" aria-label="Dados do registro">
        <button id="registro-tab-metadados" role="tab" aria-controls="registro-panel" aria-selected={tab === "metadados"} onClick={() => setTab("metadados")}>Metadados</button>
        <button id="registro-tab-imagens" role="tab" aria-controls="registro-panel" aria-selected={tab === "imagens"} onClick={() => setTab("imagens")}>Imagens</button>
      </div>
      <section id="registro-panel" className="panel" role="tabpanel" aria-labelledby={"registro-tab-" + tab}>
        {tab === "imagens" ? <RegistroImagens instrumentoId={id} registroId={registroId}
          readonly={registro.status === "EXCLUIDO" || registro.status_editorial !== "RASCUNHO"} onChange={refresh}/> :
          <div className="detail-grid">{campos.map(campo => <Detail key={campo.id} label={campo.nome} value={format(registro.dados[campo.chave])}/>)}</div>}
      </section>
      <EditorialPanel instrumentoId={id} registroId={registroId} status={registro.status_editorial}
        versao={registro.versao} onChange={refresh}/>
      <RetencaoRegistro instrumentoId={id} registroId={registroId}/>
    </>}
  </div></AppShell>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail-item"><span>{label}</span><strong className="break-text">{value}</strong></div>;
}

function format(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (Array.isArray(value)) return value.map(format).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
