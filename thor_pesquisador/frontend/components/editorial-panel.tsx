"use client";
import { useEffect, useState } from "react";
import { Archive, Check, RotateCcw, Send, Upload } from "lucide-react";
import { request } from "@/lib/api";

type Event = { id: string; data: string; agente: string; acao: string; estado_novo: string; justificativa?: string };
const actions = [
  { id: "enviar-revisao", label: "Enviar para revisao", states: ["RASCUNHO"], permission: "enviar_revisao", icon: Send },
  { id: "aprovar", label: "Aprovar", states: ["EM_REVISAO"], permission: "revisar", icon: Check },
  { id: "devolver", label: "Devolver", states: ["EM_REVISAO", "APROVADO"], permission: "revisar", icon: RotateCcw },
  { id: "publicar", label: "Publicar", states: ["APROVADO"], permission: "publicar", icon: Upload },
  { id: "arquivar", label: "Arquivar", states: ["RASCUNHO", "EM_REVISAO", "APROVADO", "PUBLICADO"], permission: "arquivar", icon: Archive },
  { id: "reabrir", label: "Reabrir", states: ["ARQUIVADO"], permission: "registros_editar", icon: RotateCcw },
];

export function EditorialPanel({ instrumentoId, registroId, status, versao, onChange }: {
  instrumentoId: string; registroId?: string; status: string; versao: number; onChange: () => void;
}) {
  const path = "/instrumentos/" + instrumentoId + (registroId ? "/registros/" + encodeURIComponent(registroId) : "");
  const [permissions, setPermissions] = useState<string[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [offset, setOffset] = useState(0);
  const [more, setMore] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [versions, setVersions] = useState<{ id: string; versao: number; data: string; schema?: unknown; snapshot?: unknown }[]>([]);
  const [versionOffset, setVersionOffset] = useState(0);
  const [versionMore, setVersionMore] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  useEffect(() => {
    if(!showVersions) return;
    let current = true;
    request<{items: typeof versions; has_more: boolean}>(path + "/versoes?limit=20&offset=" + versionOffset)
      .then(r => { if(current) { setVersions(r.items); setVersionMore(r.has_more); } }).catch(e => { if(current) setError(e.message); });
    return () => { current = false; };
  }, [path, versionOffset, showVersions, refresh]);
  useEffect(() => {
    let current = true;
    request<{ permissoes: string[] }>("/auth/permissoes?instrumento_id=" + instrumentoId)
      .then(r => { if (current) setPermissions(r.permissoes); }).catch(e => { if (current) setError(e.message); });
    return () => { current = false; };
  }, [instrumentoId]);
  useEffect(() => {
    let current = true;
    request<{ items: Event[]; has_more: boolean }>(path + "/historico?limit=20&offset=" + offset)
      .then(r => { if (current) { setEvents(r.items); setMore(r.has_more); } })
      .catch(e => { if (current) setError(e.message); });
    return () => { current = false; };
  }, [path, offset, refresh]);
  async function act(action: string) {
    setBusy(true); setError("");
    try {
      await request(path + "/editorial/" + action, { method: "POST", body: JSON.stringify({
        operacao_id: crypto.randomUUID(), versao, justificativa: comment.trim() || null,
      }) });
      setComment(""); setOffset(0); setRefresh(v => v + 1); onChange();
    } catch (e) { setError(e instanceof Error ? e.message : "Falha na operacao."); }
    finally { setBusy(false); }
  }
  return <section className="stack">
    <div className="row"><h2>Revisao e publicacao</h2><span>{status} · Versao {versao}</span></div>
    <label className="field"><span>Justificativa</span><textarea className="textarea" maxLength={4000}
      value={comment} onChange={e => setComment(e.target.value)} /></label>
    <div className="actions">{actions.filter(a => a.states.includes(status) &&
      (permissions.includes("*") || permissions.includes(a.id === "reabrir" && !registroId ? "instrumentos_editar" : a.permission))).map(a => {
        const Icon = a.icon;
        return <button key={a.id} className="button secondary" title={a.label} disabled={busy}
          onClick={() => act(a.id)}><Icon size={16} />{a.label}</button>;
      })}</div>
    {error && <p role="alert" className="error">{error}</p>}
    <h3>Historico editorial</h3>
    <button className="button secondary" onClick={() => setShowVersions(v => !v)}>Versoes publicadas</button>
    {showVersions && <div className="stack">{versions.map(v => <details key={v.id}><summary>Versao {v.versao} · {new Date(v.data).toLocaleString("pt-BR")}</summary>
      <pre className="break-text">{JSON.stringify(v.snapshot || v.schema, null, 2)}</pre></details>)}
      {!versions.length && <p className="muted">Nenhuma versao publicada.</p>}
      <div className="actions"><button className="button secondary" disabled={!versionOffset} onClick={() => setVersionOffset(v => v - 20)}>Anterior</button>
        <button className="button secondary" disabled={!versionMore} onClick={() => setVersionOffset(v => v + 20)}>Proxima</button></div></div>}
    <div className="table-wrap"><table className="table"><thead><tr><th>Data</th><th>Acao</th><th>Usuario</th><th>Estado</th><th>Justificativa</th></tr></thead>
      <tbody>{events.map(e => <tr key={e.id}><td>{new Date(e.data).toLocaleString("pt-BR")}</td>
        <td>{e.acao}</td><td>{e.agente}</td><td>{e.estado_novo}</td><td>{e.justificativa || "-"}</td></tr>)}</tbody></table></div>
    {!events.length && <p className="muted">Nenhum evento registrado.</p>}
    <div className="actions"><button className="button secondary" disabled={offset === 0}
      onClick={() => setOffset(v => Math.max(0, v - 20))}>Anterior</button><button className="button secondary"
      disabled={!more} onClick={() => setOffset(v => v + 20)}>Proxima</button></div>
  </section>;
}
