"use client";

import Link from "next/link";
import { ArrowLeft, Edit, Eye, FileUp, Plus, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { CrudPagination } from "@/components/crud-pagination";
import { Permission } from "@/components/permission";
import { DynamicField } from "@/components/registro-form";
import { consultarRegistros, deleteRegistro, getSchema } from "@/lib/api";
import type { InstrumentoCampo, Registro } from "@/types/domain";

type Filters = { q: string; status: string; filtros: Record<string, unknown> };
const EMPTY_FILTERS: Filters = { q: "", status: "", filtros: {} };

export default function RegistrosPage() {
  const { id } = useParams<{ id: string }>();
  return <RegistrosList key={id} id={id}/>;
}

function RegistrosList({ id }: { id: string }) {
  const [nome, setNome] = useState("");
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [items, setItems] = useState<Registro[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [draftFilters, setDraftFilters] = useState(EMPTY_FILTERS);
  const [advanced, setAdvanced] = useState(false);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState(false);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  const [schemaError, setSchemaError] = useState("");
  const busy = loading || removing;
  const base = `/instrumentos/${id}/registros`;

  useEffect(() => {
    let current = true;
    setNome(""); setCampos([]); setSchemaError("");
    getSchema(id).then(schema => {
      if (current) { setNome(schema.nome); setCampos(schema.campos); }
    }).catch(err => {
      if (current) setSchemaError(err instanceof Error ? err.message : "Falha ao carregar campos.");
    });
    return () => { current = false; };
  }, [id]);

  useEffect(() => {
    let current = true;
    setLoading(true); setError("");
    consultarRegistros(id, { ...filters, limit: pageSize, offset: pageIndex * pageSize })
      .then(page => {
        if (!current) return;
        setItems(page.items); setTotal(page.total);
        const lastPage = Math.max(0, Math.ceil(page.total / pageSize) - 1);
        if (pageIndex > lastPage) setPageIndex(lastPage);
      })
      .catch(err => {
        if (current) { setItems([]); setTotal(0); setError(err instanceof Error ? err.message : "Falha ao carregar registros."); }
      })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [id, filters, pageIndex, pageSize, revision]);

  function buscar(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    setPageIndex(0);
    setFilters({ ...draftFilters, q: draftFilters.q.trim(), filtros: { ...draftFilters.filtros } });
  }

  function clear() {
    setDraftFilters(EMPTY_FILTERS); setFilters({ ...EMPTY_FILTERS }); setPageIndex(0);
  }

  async function remove(item: Registro) {
    if (busy || !window.confirm("Excluir este registro? Seu historico sera preservado e ele deixara de aparecer na consulta.")) return;
    setRemoving(true); setError("");
    try {
      await deleteRegistro(id, item.id);
      if (items.length === 1 && pageIndex > 0) setPageIndex(pageIndex - 1);
      else setRevision(value => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir registro.");
    } finally { setRemoving(false); }
  }

  const listagem = campos.filter(campo => campo.aparece_listagem);
  const pagination = <CrudPagination total={total} pageIndex={pageIndex} pageSize={pageSize} loading={busy}
    onPageChange={setPageIndex} onPageSizeChange={value => { setPageSize(value); setPageIndex(0); }}/>;

  return <AppShell><div className="stack">
    <div className="row">
      <div className="page-heading"><h1>Registros</h1><p className="muted">{nome}</p>
        <p className="muted">{loading ? "Carregando..." : `${total} registros encontrados`}</p></div>
      <div className="actions">
        <Link className="button secondary" href="/instrumentos"><ArrowLeft size={16}/>Voltar</Link>
        <Permission acao="registros_incluir" instrumentoId={id}>
          <Link className="button secondary" href={base + "/importacoes"} title="Importacoes"><FileUp size={18}/>Importacoes</Link>
        </Permission>
        <Permission acao="registros_incluir" instrumentoId={id}>
          <Link className="button" href={base + "/novo"}><Plus size={18}/>Novo registro</Link>
        </Permission>
      </div>
    </div>
    <section className="panel stack">
      <form className="stack crud-search-form" onSubmit={buscar}>
        <div className="row">
          <label className="field search-field"><span>Busca simples</span>
            <input className="input" value={draftFilters.q} placeholder="Busca simples" maxLength={1000}
              onChange={e => setDraftFilters({ ...draftFilters, q: e.target.value })}/></label>
          <div className="actions">
            <button className="button" type="submit" disabled={busy}><Search size={18}/>Buscar</button>
            <button className="icon-button" type="button" title="Filtros avancados" aria-label="Filtros avancados"
              aria-expanded={advanced} onClick={() => setAdvanced(value => !value)}><SlidersHorizontal size={18}/></button>
            <button className="button secondary" type="button" disabled={busy} onClick={clear}><SlidersHorizontal size={18}/>Limpar filtros</button>
          </div>
        </div>
        {advanced && <div className="grid">
          <label className="field"><span>Status</span><select className="select" aria-label="Status" value={draftFilters.status}
            onChange={e => setDraftFilters({ ...draftFilters, status: e.target.value })}>
            <option value="">Todos</option><option value="ATIVO">ATIVO</option><option value="INATIVO">INATIVO</option>
          </select></label>
          {campos.filter(campo => campo.aparece_busca).map(campo => <DynamicField key={campo.id}
            campo={campo} filter value={draftFilters.filtros[campo.chave]}
            onChange={value => setDraftFilters(previous => ({ ...previous, filtros: { ...previous.filtros, [campo.chave]: value } }))}/>)}
        </div>}
      </form>
      {(error || schemaError) && <p className="error" role="alert">{error || schemaError}</p>}
      {pagination}
      <div className="table-wrap"><table className="table" aria-busy={busy}>
        <thead><tr>{listagem.length ? listagem.map(campo => <th key={campo.id}>{campo.nome}</th>) : <th>Registro</th>}
          <th>Status</th><th>Acoes</th></tr></thead>
        <tbody>{items.map(item => {
          const path = base + "/" + encodeURIComponent(item.id);
          return <tr key={item.id}>
            {listagem.length ? listagem.map((campo, index) => <td key={campo.id}>{index === 0 ?
              <Link className="crud-record-link" href={path}>{formatValue(item.dados[campo.chave])}</Link> :
              formatValue(item.dados[campo.chave])}</td>) :
              <td><Link className="crud-record-link" href={path}>{item.id}</Link></td>}
            <td>{item.status}</td>
            <td><div className="actions">
              <Link className="icon-button" title="Visualizar registro" aria-label="Visualizar registro" href={path}><Eye size={16}/></Link>
              {item.status_editorial !== "ARQUIVADO" && <Permission acao="registros_editar" instrumentoId={id}>
                <Link className="icon-button" title="Editar registro" aria-label="Editar registro" href={path + "/editar"}><Edit size={16}/></Link>
              </Permission>}
              <Permission acao="registros_excluir" instrumentoId={id}>
                <button className="icon-button danger" type="button" title="Excluir registro" aria-label="Excluir registro"
                  disabled={busy} onClick={() => remove(item)}><Trash2 size={16}/></button>
              </Permission>
            </div></td>
          </tr>;
        })}
        {!items.length && <tr><td colSpan={Math.max(1, listagem.length) + 2} className="muted">
          {loading ? "Carregando..." : error ? "Listagem indisponivel." : "Nenhum registro encontrado."}
        </td></tr>}
        </tbody>
      </table></div>
      {pagination}
    </section>
  </div></AppShell>;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
