"use client";

import Link from "next/link";
import { Edit, Eye, FileText, Plus, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { deleteInstrumento, listInstrumentos } from "@/lib/api";
import type { Instrumento } from "@/types/domain";

const PAGE_SIZES = [10, 20, 50, 100];

export default function InstrumentosPage() {
  const [items, setItems] = useState<Instrumento[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ q: "" });
  const [draftFilters, setDraftFilters] = useState({ q: "" });
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const offset = pageIndex * pageSize;

  async function load() {
    setLoading(true);
    try {
      const page = await listInstrumentos({ q: filters.q, limit: pageSize, offset });
      setItems(page.items);
      setTotal(page.total);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar instrumentos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filters, pageIndex, pageSize]);

  function submitSearch(event: React.FormEvent) {
    event.preventDefault();
    setPageIndex(0);
    setFilters({ q: draftFilters.q.trim() });
  }

  async function remove(item: Instrumento) {
    const confirmed = window.confirm(`Excluir o instrumento "${item.nome}"? Esta acao tambem remove campos e registros vinculados.`);
    if (!confirmed) return;
    setLoading(true);
    try {
      await deleteInstrumento(item.id);
      if (items.length === 1 && pageIndex > 0) setPageIndex(pageIndex - 1);
      else await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir instrumento.");
    } finally {
      setLoading(false);
    }
  }

  const pageNumbers = useMemo(() => {
    const first = Math.max(0, pageIndex - 2);
    const last = Math.min(totalPages - 1, pageIndex + 2);
    return Array.from({ length: last - first + 1 }, (_, index) => first + index);
  }, [pageIndex, totalPages]);

  return (
    <AppShell>
      <div className="stack">
        <div className="row">
          <div className="page-heading">
            <h1>Instrumentos</h1>
            <p className="muted">{loading ? "Carregando..." : `${total} instrumentos encontrados`}</p>
          </div>
          <Link className="button" href="/instrumentos/novo">
            <Plus size={18} />
            Novo instrumento
          </Link>
        </div>
        <section className="panel stack">
          <form className="row" onSubmit={submitSearch}>
            <label className="field search-field">
              <span>Busca simples</span>
              <input className="input" value={draftFilters.q} onChange={(event) => setDraftFilters({ q: event.target.value })} placeholder="Buscar por nome ou descricao" />
            </label>
            <div className="actions">
              <button className="button" type="submit" disabled={loading}>
                <Search size={18} />
                Buscar
              </button>
              <button
                className="button secondary"
                type="button"
                disabled={loading}
                onClick={() => {
                  setDraftFilters({ q: "" });
                  setFilters({ q: "" });
                  setPageIndex(0);
                }}
              >
                <SlidersHorizontal size={18} />
                Limpar filtros
              </button>
            </div>
          </form>
          {error ? <p className="error">{error}</p> : null}
          <Pagination
            total={total}
            pageIndex={pageIndex}
            pageSize={pageSize}
            totalPages={totalPages}
            pageNumbers={pageNumbers}
            loading={loading}
            onPageChange={setPageIndex}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPageIndex(0);
            }}
          />
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Tipo</th>
                  <th>Status</th>
                  <th>Visibilidade</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.nome}</strong>
                      {item.descricao ? <><br /><span className="muted">{item.descricao}</span></> : null}
                    </td>
                    <td>{item.tipo}</td>
                    <td>{item.status}</td>
                    <td>{item.visibilidade}</td>
                    <td className="actions">
                      <Link className="icon-button" title="Visualizar" href={`/instrumentos/${item.id}`}><Eye size={16} /></Link>
                      <Link className="icon-button" title="Editar" href={`/instrumentos/${item.id}/editar`}><Edit size={16} /></Link>
                      <Link className="icon-button" title="Campos" href={`/instrumentos/${item.id}/campos`}><SlidersHorizontal size={16} /></Link>
                      <Link className="icon-button" title="Registros" href={`/instrumentos/${item.id}/registros`}><FileText size={16} /></Link>
                      <button className="icon-button danger" type="button" title="Excluir" disabled={loading} onClick={() => remove(item)}><Trash2 size={16} /></button>
                    </td>
                  </tr>
                ))}
                {!items.length ? (
                  <tr><td colSpan={5} className="muted">Nenhum instrumento encontrado.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
          <Pagination
            total={total}
            pageIndex={pageIndex}
            pageSize={pageSize}
            totalPages={totalPages}
            pageNumbers={pageNumbers}
            loading={loading}
            onPageChange={setPageIndex}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPageIndex(0);
            }}
          />
        </section>
      </div>
    </AppShell>
  );
}

function Pagination({
  total,
  pageIndex,
  pageSize,
  totalPages,
  pageNumbers,
  loading,
  onPageChange,
  onPageSizeChange
}: {
  total: number;
  pageIndex: number;
  pageSize: number;
  totalPages: number;
  pageNumbers: number[];
  loading: boolean;
  onPageChange: (value: number) => void;
  onPageSizeChange: (value: number) => void;
}) {
  const start = total === 0 ? 0 : pageIndex * pageSize + 1;
  const end = Math.min(total, (pageIndex + 1) * pageSize);

  return (
    <div className="pagination">
      <span className="muted">{start}-{end} de {total} | pagina {pageIndex + 1} de {totalPages}</span>
      <div className="actions">
        <select className="select page-size" value={pageSize} disabled={loading} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          {PAGE_SIZES.map((size) => <option key={size} value={size}>{size}/pagina</option>)}
        </select>
        <button className="button secondary" type="button" disabled={loading || pageIndex === 0} onClick={() => onPageChange(0)}>Primeira</button>
        <button className="button secondary" type="button" disabled={loading || pageIndex === 0} onClick={() => onPageChange(pageIndex - 1)}>Anterior</button>
        {pageNumbers.map((page) => (
          <button className={page === pageIndex ? "button" : "button secondary"} type="button" key={page} disabled={loading} onClick={() => onPageChange(page)}>
            {page + 1}
          </button>
        ))}
        <button className="button secondary" type="button" disabled={loading || pageIndex >= totalPages - 1} onClick={() => onPageChange(pageIndex + 1)}>Proxima</button>
        <button className="button secondary" type="button" disabled={loading || pageIndex >= totalPages - 1} onClick={() => onPageChange(totalPages - 1)}>Ultima</button>
      </div>
    </div>
  );
}
