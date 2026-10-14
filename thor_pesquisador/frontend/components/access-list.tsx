"use client";
import { Permission } from "./permission";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Edit, Eye, Plus, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import { CrudPagination } from "@/components/crud-pagination";
import { request } from "@/lib/api";
import type { Acesso } from "./acesso-editor";
export function AccessList({usuarioId, readonly=false}: {usuarioId?:string; readonly?:boolean}) {
  const [rows, setRows] = useState<Acesso[]>([]);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [draft, setDraft] = useState({q:"", papel:""});
  const [filters, setFilters] = useState(draft);
  const [advanced, setAdvanced] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let current = true; setLoading(true);
    const query = new URLSearchParams({q: filters.q, limit: String(size), offset: String(page * size)});
    if(filters.papel) query.set("papel", filters.papel);
    if(usuarioId) query.set("usuario_id", usuarioId);
    request<{items: Acesso[]; total: number}>("/acessos?" + query)
      .then(r => { if(current) { setRows(r.items); setTotal(r.total); setError(""); } })
      .catch(e => { if(current) { setError(e.message); setRows([]); setTotal(0); } })
      .finally(() => { if(current) setLoading(false); });
    return () => { current = false; };
  }, [page, size, filters, refresh, usuarioId]);
  async function remove(row: Acesso) {
    if(!window.confirm("Revogar o acesso de " + row.nome + "?")) return;
    setLoading(true);
    try { await request("/acessos/" + row.id, {method:"DELETE"});
      if(rows.length === 1 && page > 0) setPage(v => v - 1); else setRefresh(v => v + 1);
    } catch(e) { setError(e instanceof Error ? e.message : "Falha ao revogar."); }
    finally { setLoading(false); }
  }
  const pagination = {total, pageIndex:page, pageSize:size, loading, onPageChange:setPage,
    onPageSizeChange:(n:number) => {setSize(n);setPage(0);}};
  return <div className="stack"><div className="row"><h2>{usuarioId ? "Perfis e escopos" : "Concessoes de acesso"}</h2>
    {!readonly && <Permission acao="acessos_incluir"><Link className="button" href={"/acessos/novo" + (usuarioId ? "?usuario=" + usuarioId : "")}><Plus size={16}/>Novo acesso</Link></Permission>}</div>
    <form className="stack crud-search-form" onSubmit={e => { e.preventDefault(); setFilters({...draft, q:draft.q.trim()}); setPage(0);setRefresh(v => v + 1); }}>
      <div className="row"><label className="field search-field"><span>Usuario</span><input className="input" value={draft.q}
        onChange={e => setDraft({...draft, q:e.target.value})}/></label><div className="actions">
        <button className="button" disabled={loading}><Search size={16}/>Buscar</button>
        <button className="icon-button" type="button" title="Filtros" aria-label="Filtros" aria-expanded={advanced}
          onClick={() => setAdvanced(v => !v)}><SlidersHorizontal size={16}/></button>
        <button className="button secondary" type="button" onClick={() => {const empty={q:"",papel:""};setDraft(empty);setFilters(empty);setPage(0);}}>Limpar</button>
      </div></div>{advanced && <label className="field"><span>Perfil (codigo)</span><input className="input" value={draft.papel}
        onChange={e => setDraft({...draft,papel:e.target.value})}/></label>}
    </form>{error && <p className="error" role="alert">{error}</p>}
    <CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr><th>Usuario</th><th>Papel</th><th>Escopo</th><th>Acoes</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.id}><td><Link className="crud-record-link" href={"/acessos/" + r.id}>{r.nome}</Link></td><td>{r.papel}</td><td>{r.instrumento_id || "Global"}</td><td><div className="actions">
        <Link className="icon-button" title="Visualizar" aria-label="Visualizar" href={"/acessos/" + r.id}><Eye size={16}/></Link>
        {!readonly && <><Permission acao="acessos_editar"><Link className="icon-button" title="Editar" aria-label="Editar" href={"/acessos/" + r.id + "/editar"}><Edit size={16}/></Link></Permission>
        <Permission acao="acessos_excluir"><button className="icon-button danger" title="Revogar acesso" aria-label="Revogar acesso" disabled={loading}
          onClick={() => remove(r)}><Trash2 size={16}/></button></Permission></>}
      </div></td></tr>)}{!rows.length && <tr><td colSpan={4}>{loading ? "Carregando..." : "Nenhum acesso encontrado."}</td></tr>}</tbody></table></div>
    <CrudPagination {...pagination}/>
  </div>;
}
