"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Edit, Save, Search } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { request } from "@/lib/api";
export type Acesso = {id: string; usuario_id: string; nome: string; papel: string; instrumento_id: string | null; instrumento_nome?: string};
export function AcessoEditor({id, readonly = false, usuarioId}: {id?: string; readonly?: boolean; usuarioId?:string}) {
  const router = useRouter();
  const [initial, setInitial] = useState<Acesso>();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [preselected, setPreselected] = useState<{id:string;nome:string}>();
  useEffect(() => {
    if(!usuarioId || id) return;
    let current = true;
    request<{id:string;nome:string}>("/usuarios/" + usuarioId).then(u => {if(current) setPreselected(u);})
      .catch(e => {if(current) setError(e.message);});
    return () => {current = false;};
  }, [usuarioId, id]);
  const back = initial?.usuario_id || usuarioId;
  const backPath = back ? "/usuarios/" + back + "/acessos" : "/usuarios";
  useEffect(() => {
    if(!id) return;
    let current = true;
    request<Acesso>("/acessos/" + id).then(a => { if(current) setInitial(a); }).catch(e => { if(current) setError(e.message); });
    return () => { current = false; };
  }, [id]);
  async function save(data: {usuario_id: string; papel: string; instrumento_id: string | null}) {
    setSaving(true); setError("");
    try { await request(id ? "/acessos/" + id : "/acessos", {method: id ? "PUT" : "POST", body: JSON.stringify(data)}); router.push("/usuarios/" + data.usuario_id + "/acessos"); }
    catch(e) { setError(e instanceof Error ? e.message : "Falha ao salvar."); }
    finally { setSaving(false); }
  }
  return <AppShell><Permission acao={readonly ? "acessos_consultar" : id ? "acessos_editar" : "acessos_incluir"}><div className="stack"><div className="row"><h1>{readonly ? "Visualizar acesso" : id ? "Editar acesso" : "Novo acesso"}</h1>
    <div className="actions"><Link className="button secondary" href={backPath}><ArrowLeft size={16}/>Voltar</Link>
      {readonly && id && <Link className="button" href={"/acessos/" + id + "/editar"}><Edit size={16}/>Editar</Link>}</div></div>
    {readonly ? <dl className="detail-grid"><div><dt>Usuario</dt><dd>{initial?.nome}</dd></div><div><dt>Papel</dt><dd>{initial?.papel}</dd></div>
      <div><dt>Escopo</dt><dd>{initial?.instrumento_nome}</dd></div></dl> :
      (!id || initial) && (!usuarioId || preselected || initial) &&
      <AcessoForm key={id || preselected?.id || "novo"} initial={initial} preselected={preselected} onSubmit={save} saving={saving}/>}
    {error && <p className="error" role="alert">{error}</p>}
  </div></Permission></AppShell>;
}
function AcessoForm({initial, preselected, onSubmit, saving}: {initial?: Acesso; preselected?:{id:string;nome:string}; saving: boolean;
  onSubmit: (data: {usuario_id: string; papel: string; instrumento_id: string | null}) => Promise<void>}) {
  const [user, setUser] = useState(initial?.usuario_id || preselected?.id || "");
  const [role, setRole] = useState(initial?.papel || "");
  const [global, setGlobal] = useState(!!initial && !initial.instrumento_id);
  const [instrument, setInstrument] = useState(initial?.instrumento_id || "");
  return <form className="stack" onSubmit={e => { e.preventDefault(); onSubmit({usuario_id: user, papel: role, instrumento_id: global ? null : instrument}); }}>
    <EntitySelect label="Usuario" path="/usuarios" value={user} initial={initial ? {id: initial.usuario_id, nome: initial.nome} : preselected} onChange={setUser}/>
    <EntitySelect label="Perfil" path="/perfis?ativo=true" value={role}
      initial={initial ? {id:initial.papel,nome:initial.papel} : undefined} onChange={setRole}/>
    <label><input type="checkbox" checked={global} onChange={e => setGlobal(e.target.checked)}/>Escopo global</label>
    {!global && <EntitySelect label="Instrumento" path="/instrumentos" value={instrument}
      initial={initial?.instrumento_id ? {id: initial.instrumento_id, nome: initial.instrumento_nome || initial.instrumento_id} : undefined} onChange={setInstrument}/>}
    <button className="button" disabled={saving || !user || !role || (!global && !instrument) || (role === "ADMIN" && !global)}>
      <Save size={16}/>{saving ? "Salvando..." : "Salvar"}</button>
  </form>;
}
export function EntitySelect({label, path, value, initial, onChange, autoLoad=false}: {label: string; path: string; value: string; autoLoad?:boolean;
  initial?: {id: string; nome: string}; onChange: (id: string) => void}) {
  const [items, setItems] = useState(initial ? [initial] : []);
  const [q, setQ] = useState("");
  const [applied, setApplied] = useState<string | undefined>(autoLoad ? "" : undefined);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    if(applied === undefined) return;
    let current = true; setLoading(true);
    request<{items: {id: string; nome: string}[]; total: number}>(path + (path.includes("?") ? "&" : "?") + "limit=20&offset=" + offset + "&q=" + encodeURIComponent(applied))
      .then(r => { if(current) { setItems(r.items); setTotal(r.total); setError(""); } }).catch(e => { if(current) setError(e.message); })
      .finally(() => { if(current) setLoading(false); });
    return () => { current = false; };
  }, [path, applied, offset, refresh]);
  return <div className="stack"><label className="field"><span>{label} *</span><select className="select" required value={value} onChange={e => onChange(e.target.value)}>
    <option value="">Selecione</option>{items.map(i => <option key={i.id} value={i.id}>{i.nome}</option>)}</select></label>
    <div className="row"><input className="input" aria-label={"Buscar " + label.toLowerCase()} value={q} onChange={e => setQ(e.target.value)}/>
      <button className="icon-button" type="button" title={"Buscar " + label.toLowerCase()} aria-label={"Buscar " + label.toLowerCase()} disabled={loading}
        onClick={() => { onChange(""); setApplied(q.trim()); setOffset(0); setRefresh(v => v + 1); }}><Search size={16}/></button></div>
    {applied !== undefined && <div className="actions"><span>{total} resultados</span><button className="button secondary" type="button"
      disabled={loading || !offset} onClick={() => { onChange(""); setOffset(v => v - 20); }}>Anterior</button>
      <button className="button secondary" type="button" disabled={loading || offset + 20 >= total}
        onClick={() => { onChange(""); setOffset(v => v + 20); }}>Proxima</button></div>}
    {error && <p className="error">{error}</p>}
  </div>;
}
