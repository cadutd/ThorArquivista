"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Eye, Search, SlidersHorizontal } from "lucide-react";
import { request } from "@/lib/api";
import { CrudPagination } from "./crud-pagination";
import { PortalShell } from "./portal-shell";

type RecordRow = { id: string; titulo: string; dados: Record<string, unknown> };
type Field = {
  chave: string; nome: string; tipo: string; aparece_listagem?: boolean; filtro_avancado?: boolean; facetavel?: boolean;
};

export function PortalRecords({ id }: { id: string }) {
  return <PortalShell><Records key={id} id={id}/></PortalShell>;
}

function Records({ id }: { id: string }) {
  const [name, setName] = useState("Instrumento");
  const [fields, setFields] = useState<Field[]>([]);
  const [facets, setFacets] = useState<Record<string, Record<string, number>>>({});
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState<Record<string, unknown>>({});
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [applied, setApplied] = useState("");
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(20);
  const [refresh, setRefresh] = useState(0);
  const [items, setItems] = useState<RecordRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [schemaError, setSchemaError] = useState("");
  const [facetError, setFacetError] = useState("");
  const [advanced, setAdvanced] = useState(false);
  const counted = useRef("");
  const path = "/publico/instrumentos/" + id;
  const listPath = "/consulta/" + id;

  useEffect(() => {
    let live = true;
    setSchemaError("");
    request<{ nome: string; campos: Field[] }>(path).then(schema => {
      if (live) { setName(schema.nome); setFields(schema.campos); }
    }).catch(err => { if (live) setSchemaError(err.message); });
    return () => { live = false; };
  }, [path]);

  useEffect(() => {
    if (!advanced) return;
    let live = true;
    setFacetError("");
    request<typeof facets>(path + "/facetas").then(result => { if (live) setFacets(result); })
      .catch(err => { if (live) setFacetError(err.message); });
    return () => { live = false; };
  }, [path, advanced]);

  useEffect(() => {
    let live = true;
    setLoading(true); setError("");
    request<{ items: RecordRow[]; total: number }>(path + "/buscar?" + new URLSearchParams({
      q: applied, limit: String(size), offset: String(page * size), filtros: JSON.stringify(filters)
    })).then(result => {
      if (!live) return;
      setItems(result.items); setTotal(result.total);
      const lastPage = Math.max(0, Math.ceil(result.total / size) - 1);
      if (page > lastPage) setPage(lastPage);
      if (counted.current !== id) {
        counted.current = id;
        void request(path + "/acessos", { method: "POST" }).catch(() => { counted.current = ""; });
      }
    }).catch(err => {
      if (live) { setError(err.message); setItems([]); setTotal(0); }
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [path, id, applied, filters, page, size, refresh]);

  function buscar(event: React.FormEvent) {
    event.preventDefault();
    if (loading) return;
    setApplied(q.trim()); setFilters({ ...draft }); setPage(0); setRefresh(value => value + 1);
  }

  function clear() {
    setQ(""); setApplied(""); setDraft({}); setFilters({}); setPage(0);
  }

  function setFilter(key: string, value: unknown) {
    setDraft(previous => {
      const next = { ...previous };
      if (value === "" || value === null || value === undefined) delete next[key];
      else next[key] = value;
      return next;
    });
  }

  const columns = fields.filter(field => field.aparece_listagem);
  const searchable = fields.filter(field => field.facetavel || field.filtro_avancado);
  const pagination = {
    total, pageIndex: page, pageSize: size, loading, onPageChange: setPage,
    onPageSizeChange: (value: number) => { setSize(value); setPage(0); }
  };

  return <div className="portal-width portal-section stack">
    <div className="row">
      <div className="page-heading"><h1>{name}</h1><p className="muted">
        {loading ? "Carregando..." : total + " registros publicados"}
      </p></div>
      <Link className="button secondary" href="/consulta"><ArrowLeft size={16}/>Voltar</Link>
    </div>
    <section className="panel stack">
      <form className="stack crud-search-form" onSubmit={buscar}>
        <div className="row">
          <label className="field search-field"><span>Busca simples</span>
            <input className="input" aria-label="Buscar registros publicados" placeholder="Busca simples" maxLength={1000}
              value={q} onChange={event => setQ(event.target.value)}/></label>
          <div className="actions">
            <button className="button" type="submit" disabled={loading}><Search size={18}/>Buscar</button>
            <button className="icon-button" type="button" title="Filtros avancados" aria-label="Filtros avancados"
              aria-expanded={advanced} onClick={() => setAdvanced(value => !value)}><SlidersHorizontal size={18}/></button>
            <button className="button secondary" type="button" disabled={loading} onClick={clear}>
              <SlidersHorizontal size={18}/>Limpar filtros
            </button>
          </div>
        </div>
        {advanced && <div className="grid">{searchable.map(field =>
          <RecordFilter key={field.chave} field={field} facets={facets["dados." + field.chave]}
            value={draft[field.chave]} onChange={value => setFilter(field.chave, value)}/>
        )}</div>}
      </form>
      {(error || schemaError || facetError) && <p className="error" role="alert">{error || schemaError || facetError}</p>}
      <CrudPagination {...pagination}/>
      <div className="table-wrap"><table className="table" aria-busy={loading}>
        <thead><tr>
          {columns.length ? columns.map(field => <th key={field.chave}>{field.nome}</th>) : <th>Registro</th>}
          <th className="crud-actions-heading">Acoes</th>
        </tr></thead>
        <tbody>{items.map(row => {
          const detailPath = listPath + "/" + encodeURIComponent(row.id);
          return <tr key={row.id}>
            {columns.length ? columns.map((field, index) => <td key={field.chave} className="break-text">
              {index === 0 ? <Link className="crud-record-link" prefetch={false} href={detailPath}>
                {formatValue(row.dados[field.chave])}
              </Link> : formatValue(row.dados[field.chave])}
            </td>) : <td><Link className="crud-record-link" prefetch={false} href={detailPath}>{row.titulo || row.id}</Link></td>}
            <td><div className="actions">
              <Link className="icon-button" title="Visualizar registro" aria-label="Visualizar registro"
                prefetch={false} href={detailPath}><Eye size={16}/></Link>
            </div></td>
          </tr>;
        })}
        {!items.length && <tr><td colSpan={Math.max(1, columns.length) + 1} className="muted">
          {loading ? "Carregando..." : error || schemaError ? "Consulta indisponivel." : "Nenhum registro publicado."}
        </td></tr>}
        </tbody>
      </table></div>
      <CrudPagination {...pagination}/>
    </section>
  </div>;
}

function RecordFilter({ field, facets, value, onChange }: {
  field: Field; facets?: Record<string, number>; value: unknown; onChange: (value: unknown) => void;
}) {
  function parse(value: string) {
    if (value === "") return undefined;
    return field.tipo === "NUMERO" ? Number(value) : field.tipo === "BOOLEANO" ? value === "true" : value;
  }
  if (facets && Object.keys(facets).length) return <label className="field"><span>{field.nome}</span>
    <select className="select" aria-label={field.nome} value={String(value ?? "")} onChange={event => onChange(parse(event.target.value))}>
      <option value="">Todos</option>
      {Object.entries(facets).map(([option, count]) =>
        <option key={option} value={option}>{field.tipo === "BOOLEANO" ? option === "true" ? "Sim" : "Nao" : option} ({count})</option>)}
    </select>
  </label>;
  if (field.tipo === "BOOLEANO") return <label className="field"><span>{field.nome}</span>
    <select className="select" aria-label={field.nome} value={String(value ?? "")} onChange={event => onChange(parse(event.target.value))}>
      <option value="">Todos</option><option value="false">Nao</option><option value="true">Sim</option>
    </select>
  </label>;
  return <label className="field"><span>{field.nome}</span>
    <input className="input" type={field.tipo === "NUMERO" ? "number" : field.tipo === "DATA" ? "date" : "text"}
      step={field.tipo === "NUMERO" ? "any" : undefined} value={String(value ?? "")} maxLength={1000}
      onChange={event => onChange(parse(event.target.value))}/>
  </label>;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
