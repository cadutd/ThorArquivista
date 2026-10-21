"use client";
import Link from "next/link";
import { ArrowLeft, Eye, FileUp, Plus, RefreshCw, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";
import { CrudPagination } from "./crud-pagination";
import { usePermission } from "./permission";
import { acionarImportacao, listarImportacoesAssincronas, podeCancelarImportacao, podeRetomarImportacao, statusImportacao } from "@/lib/importacoes-assincronas";
import type { JobImportacao } from "@/lib/importacoes-assincronas";

const EMPTY = { q: "", status: "" };
export function ImportacoesLista({ instrumentoId: id }: { instrumentoId: string }) {
  const canImport = usePermission("registros_incluir", id);
  const [items, setItems] = useState<JobImportacao[]>([]), [total, setTotal] = useState(0);
  const [filters, setFilters] = useState(EMPTY), [draft, setDraft] = useState(EMPTY);
  const [advanced, setAdvanced] = useState(false);
  const [pageIndex, setPageIndex] = useState(0), [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true), [mutating, setMutating] = useState(false);
  const [error, setError] = useState(""), [revision, setRevision] = useState(0);
  const base = "/instrumentos/" + id + "/registros";
  const busy = loading || mutating;
  useEffect(() => {
    if (!canImport) return;
    const controller = new AbortController();
    setLoading(true); setError("");
    listarImportacoesAssincronas(id, { ...filters, limit: pageSize, offset: pageIndex * pageSize }, controller.signal)
      .then(page => {
        if (controller.signal.aborted) return;
        setItems(page.items); setTotal(page.total);
        const last = Math.max(0, Math.ceil(page.total / pageSize) - 1);
        if (pageIndex > last) setPageIndex(last);
      }).catch(err => {
        if (!controller.signal.aborted) { setItems([]); setTotal(0); setError(err instanceof Error ? err.message : "Falha ao carregar importacoes."); }
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [id, canImport, filters, pageIndex, pageSize, revision]);
  async function action(job: JobImportacao, acao: "cancelar" | "retomar") {
    if (busy || !canImport || (acao === "cancelar" && !window.confirm("Cancelar esta importacao?"))) return;
    setMutating(true); setError("");
    try { await acionarImportacao(id, job.id, acao); setRevision(value => value + 1); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao atualizar importacao."); }
    finally { setMutating(false); }
  }
  const pagination = <CrudPagination total={total} pageIndex={pageIndex} pageSize={pageSize} loading={busy}
    onPageChange={setPageIndex} onPageSizeChange={size => { setPageSize(size); setPageIndex(0); }}/>;
  if (!canImport) return <section className="stack"><h1>Importacoes</h1><p role="status">Sem permissao para importar registros neste instrumento.</p></section>;
  return <div className="stack">
    <div className="row"><div className="page-heading"><h1>Importacoes</h1><p className="muted">{loading ? "Carregando..." : total + " importacoes encontradas"}</p></div>
      <div className="actions"><Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link>
        <Link className="button secondary" href={base + "/importar"}><FileUp size={16}/>Importacao sincrona</Link>
        <Link className="button" href={base + "/importacoes/nova"}><Plus size={16}/>Nova importacao</Link></div>
    </div>
    <section className="panel stack">
      <form className="stack crud-search-form" onSubmit={event => { event.preventDefault(); if (!busy) { setPageIndex(0); setFilters({ ...draft, q: draft.q.trim() }); } }}>
        <div className="row"><label className="field search-field"><span>Busca simples</span><input className="input"
          maxLength={150} value={draft.q} onChange={event => setDraft({ ...draft, q: event.target.value })}/></label>
          <div className="actions"><button className="button" type="submit" disabled={busy}><Search size={16}/>Buscar</button>
            <button className="icon-button" type="button" title="Filtros avancados" aria-label="Filtros avancados"
              aria-expanded={advanced} onClick={() => setAdvanced(value => !value)}><SlidersHorizontal size={16}/></button>
            <button className="button secondary" type="button" disabled={busy}
              onClick={() => { setDraft(EMPTY); setFilters({ ...EMPTY }); setPageIndex(0); }}><X size={16}/>Limpar filtros</button>
            <button className="icon-button" type="button" title="Atualizar importacoes" aria-label="Atualizar importacoes"
              disabled={busy} onClick={() => setRevision(value => value + 1)}><RefreshCw size={16}/></button></div>
        </div>
        {advanced && <label className="field"><span>Status</span><select className="select" value={draft.status}
          onChange={event => setDraft({ ...draft, status: event.target.value })}><option value="">Todos</option>
          {statusImportacao.map(status => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
        </select></label>}
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      {pagination}
      <div className="table-wrap"><table className="table" aria-label="Importacoes" aria-busy={busy}>
        <thead><tr><th>Arquivo</th><th>Status</th><th>Importados</th><th>Criada em</th><th>Acoes</th></tr></thead>
        <tbody>{items.map(job => <tr key={job.id}>
          <td className="break-text"><Link className="crud-record-link" href={base + "/importacoes/" + encodeURIComponent(job.id)}>{job.nome_arquivo}</Link></td>
          <td>{job.status.replaceAll("_", " ")}</td><td>{job.processados} de {job.total}</td>
          <td>{new Date(job.criado_em).toLocaleString("pt-BR")}</td><td><div className="actions">
            <Link className="icon-button" title="Visualizar importacao" aria-label="Visualizar importacao"
              href={base + "/importacoes/" + encodeURIComponent(job.id)}><Eye size={16}/></Link>
            {podeRetomarImportacao(job.status) && <button className="icon-button" type="button" title="Retomar importacao"
              aria-label="Retomar importacao" disabled={busy} onClick={() => action(job, "retomar")}><RotateCcw size={16}/></button>}
            {podeCancelarImportacao(job.status) && <button className="icon-button danger" type="button" title="Cancelar importacao"
              aria-label="Cancelar importacao" disabled={busy} onClick={() => action(job, "cancelar")}><X size={16}/></button>}
          </div></td>
        </tr>)}
        {!items.length && <tr><td colSpan={5} className="muted">{loading ? "Carregando..." : error ? "Listagem indisponivel." : "Nenhuma importacao encontrada."}</td></tr>}
        </tbody>
      </table></div>
      {pagination}
    </section>
  </div>;
}
