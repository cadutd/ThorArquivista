"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { request } from "@/lib/api";
import { CrudPagination } from "@/components/crud-pagination";
type Instrumento = { id: string; nome: string; descricao?: string };
type Registro = { id: string; titulo: string; dados: Record<string, unknown> };
export default function Consulta() {
  const [instruments, setInstruments] = useState<Instrumento[]>([]);
  const [instrument, setInstrument] = useState("");
  const [q, setQ] = useState("");
  const [applied, setApplied] = useState("");
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState<Registro[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [catalogOffset, setCatalogOffset] = useState(0);
  const [catalogTotal, setCatalogTotal] = useState(0);
  const [advanced, setAdvanced] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [facets, setFacets] = useState<Record<string, Record<string, number>>>({});
  const [fields, setFields] = useState<{ chave: string; nome: string; tipo: string }[]>([]);
  const [filters, setFilters] = useState<Record<string, unknown>>({});
  useEffect(() => {
    setFilters({}); setFacets({}); setFields([]);
    if(!instrument) return;
    let current = true;
    request<{ campos: typeof fields }>("/publico/instrumentos/" + instrument).then(s => { if(current) setFields(s.campos); }).catch(() => {});
    request<typeof facets>("/publico/instrumentos/" + instrument + "/facetas").then(f => { if(current) setFacets(f); }).catch(() => {});
    return () => { current = false; };
  }, [instrument]);
  useEffect(() => {
    let current = true;
    request<{ items: Instrumento[]; total: number }>("/publico/instrumentos?limit=20&offset=" + catalogOffset)
      .then(r => { if (current) { setInstruments(r.items); setCatalogTotal(r.total); } }).catch(e => { if (current) setError(e.message); });
    return () => { current = false; };
  }, [catalogOffset]);
  useEffect(() => {
    if (!instrument) { setItems([]); return; }
    let current = true; setLoading(true); setItems([]); setTotal(0); setError("");
    request<{ items: Registro[]; total: number }>("/publico/instrumentos/" + instrument +
      "/buscar?q=" + encodeURIComponent(applied) + "&limit=" + pageSize + "&offset=" + offset + "&filtros=" + encodeURIComponent(JSON.stringify(filters)))
      .then(r => { if (current) { setItems(r.items); setTotal(r.total); } })
      .catch(e => { if (current) setError(e.message); }).finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [instrument, applied, offset, filters, refresh, pageSize]);
  return <main className="container stack">
    <header className="row"><h1>Thor Pesquisador</h1><Link href="/login">Entrar</Link></header>
    <h2>Consulta publica</h2>
    <label className="field"><span>Instrumento</span><select className="select" value={instrument}
      onChange={e => { setInstrument(e.target.value); setOffset(0); }}>
      <option value="">Selecione</option>{instruments.map(i => <option key={i.id} value={i.id}>{i.nome}</option>)}
    </select></label>
    <div className="actions"><button className="button secondary" disabled={catalogOffset === 0}
      onClick={() => setCatalogOffset(v => Math.max(0, v - 20))}>Instrumentos anteriores</button>
      <button className="button secondary" disabled={catalogOffset + 20 >= catalogTotal}
        onClick={() => setCatalogOffset(v => v + 20)}>Proximos instrumentos</button></div>
    <form className="row crud-search-form" onSubmit={e => { e.preventDefault(); setApplied(q.trim()); setOffset(0); setRefresh(v => v + 1); }}>
      <input className="input" aria-label="Buscar registros publicados" value={q} onChange={e => setQ(e.target.value)} />
      <button className="button" disabled={!instrument || loading}><Search size={16}/>Buscar</button>
      <button className="icon-button" type="button" title="Filtros" aria-label="Filtros" aria-expanded={advanced}
        onClick={() => setAdvanced(v => !v)}><SlidersHorizontal size={16}/></button>
    </form>
    {advanced && <div className="grid">{fields.filter(f => facets["dados." + f.chave]).map(f => <label className="field" key={f.chave}><span>{f.nome}</span>
      <select className="select" value={filters[f.chave] === undefined ? "" : String(filters[f.chave])} onChange={e => {
        const next = {...filters}; if(e.target.value === "") delete next[f.chave];
        else next[f.chave] = f.tipo === "NUMERO" ? Number(e.target.value) : f.tipo === "BOOLEANO" ? e.target.value === "true" : e.target.value;
        setFilters(next); setOffset(0);
      }}><option value="">Todos</option>{Object.entries(facets["dados." + f.chave]).map(([value, count]) =>
        <option key={value} value={value}>{value} ({count})</option>)}</select></label>)}</div>}
    {error && <p className="error" role="alert">{error}</p>}
    {loading ? <p className="muted">Carregando...</p> : <div className="table-wrap"><table className="table">
      <thead><tr><th>Registro</th><th>Metadados publicados</th></tr></thead><tbody>{items.map(r => <tr key={r.id}>
        <td><Link className="crud-record-link" href={"/consulta/" + instrument + "/" + encodeURIComponent(r.id)}>{r.titulo}</Link></td>
        <td className="break-text">{Object.values(r.dados).map(String).join(" | ")}</td></tr>)}</tbody></table></div>}
    {instrument && !loading && !error && !items.length && <p className="muted">Nenhum registro publicado.</p>}
    <CrudPagination total={total} pageIndex={Math.floor(offset/pageSize)} pageSize={pageSize} loading={loading}
      onPageChange={n => setOffset(n * pageSize)} onPageSizeChange={n => { setPageSize(n); setOffset(0); }}/>
  </main>;
}
