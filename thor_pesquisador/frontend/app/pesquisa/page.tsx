"use client";

import { Eye, RefreshCw, Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { CrudPagination } from "@/components/crud-pagination";
import { StatusBadge } from "@/components/status-badge";
import Link from "next/link";
import { mediaUrl } from "@/lib/imagens";
import { buscarAvancado, getFacetas, getSchema, listInstrumentos, reindexarInstrumento } from "@/lib/api";
import type { BuscaAvancadaResultado, FacetasResultado, Instrumento, InstrumentoCampo } from "@/types/domain";
type Query = { q: string; filters: Record<string, unknown>; sort: string[] };

export default function PesquisaPage() {
  const [instrumentos, setInstrumentos] = useState<Instrumento[]>([]);
  const [instrumentoId, setInstrumentoId] = useState("");
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sort, setSort] = useState("");
  const [resultado, setResultado] = useState<BuscaAvancadaResultado | null>(null);
  const [facetas, setFacetas] = useState<FacetasResultado | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [pageIndex, setPageIndex] = useState(0), [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(false), [applied, setApplied] = useState<Query>();
  const requestVersion = useRef(0);

  useEffect(() => {
    listInstrumentos({ limit: 100 })
      .then((page) => {
        setInstrumentos(page.items);
        setInstrumentoId(page.items[0]?.id ?? "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar instrumentos."));
  }, []);

  useEffect(() => {
    if (!instrumentoId) return;
    let current = true;
    requestVersion.current += 1;
    setResultado(null); setApplied(undefined); setPageIndex(0); setLoading(false);
    setCampos([]); setFacetas(null); setFilters({}); setSort(""); setStatus(""); setError("");
    Promise.all([getSchema(instrumentoId), getFacetas(instrumentoId).catch(() => null)])
      .then(([schema, facetData]) => {
        if (!current) return;
        setCampos(schema.campos);
        setFacetas(facetData);
      })
      .catch((err) => { if (current) setError(err instanceof Error ? err.message : "Falha ao carregar schema."); });
    return () => { current = false; requestVersion.current += 1; };
  }, [instrumentoId]);

  const filterable = useMemo(() => campos.filter((campo) => campo.filtro_avancado), [campos]);
  const sortable = useMemo(() => campos.filter((campo) => campo.ordenavel), [campos]);

  async function consultarPagina(query: Query, page: number, size: number) {
    if (!instrumentoId || loading) return;
    const version = ++requestVersion.current;
    setLoading(true);
    try {
      const data = await buscarAvancado(instrumentoId, {
        ...query, limit: size, offset: page * size
      });
      if (version !== requestVersion.current) return;
      setResultado(data);
      setApplied(query); setPageIndex(page); setPageSize(size);
      setError("");
    } catch (err) {
      if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Falha na busca avancada.");
    } finally { if (version === requestVersion.current) setLoading(false); }
  }
  function pesquisar(event?: React.FormEvent) {
    event?.preventDefault();
    return consultarPagina({ q: q.trim(),
      filters: Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== "")),
      sort: sort ? [sort] : [] }, 0, pageSize);
  }

  async function reindexar() {
    if (!instrumentoId) return;
    try {
      const job = await reindexarInstrumento(instrumentoId);
      setStatus(`Reindexacao enfileirada: ${job.status} (${job.id})`);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao reindexar.");
    }
  }

  const pagination = <CrudPagination total={resultado?.total ?? 0} pageIndex={pageIndex} pageSize={pageSize}
    loading={loading || !resultado} onPageChange={page => { if (applied) void consultarPagina(applied, page, pageSize); }}
    onPageSizeChange={size => { if (applied) void consultarPagina(applied, 0, size); }}/>;
  return (
    <AppShell>
      <div className="stack">
        <div className="page-heading">
          <h1>Pesquisa</h1>
        </div>

        <form className="panel stack" onSubmit={pesquisar}>
          <div className="grid">
            <Field label="Instrumento">
              <select className="select" value={instrumentoId} onChange={(event) => setInstrumentoId(event.target.value)}>
                {instrumentos.map((instrumento) => (
                  <option key={instrumento.id} value={instrumento.id}>{instrumento.nome}</option>
                ))}
              </select>
            </Field>
            <Field label="Texto">
              <input className="input" value={q} onChange={(event) => setQ(event.target.value)} placeholder="Buscar em titulo e texto geral" />
            </Field>
            <Field label="Ordenacao">
              <select className="select" value={sort} onChange={(event) => setSort(event.target.value)}>
                <option value="">Mais relevante</option>
                <option value="criado_em:desc">Criacao recente</option>
                <option value="atualizado_em:desc">Atualizacao recente</option>
                {sortable.map((campo) => (
                  <option key={campo.id} value={`${campo.chave}:asc`}>{campo.nome} crescente</option>
                ))}
              </select>
            </Field>
          </div>

          {filterable.length ? (
            <div className="grid">
              {filterable.map((campo) => (
                <Field key={campo.id} label={campo.nome}>
                  <input className="input" value={filters[campo.chave] ?? ""} onChange={(event) => setFilters({ ...filters, [campo.chave]: event.target.value })} />
                </Field>
              ))}
            </div>
          ) : null}

          <div className="actions">
            <button className="button" type="submit" disabled={loading}><Search size={16} />{loading ? "Pesquisando..." : "Pesquisar"}</button>
            <Permission acao="reindexar" instrumentoId={instrumentoId}><button className="button secondary" type="button" onClick={reindexar}><RefreshCw size={16} /> Reindexar instrumento</button></Permission>
          </div>
          {status ? <p className="muted">{status}</p> : null}
          {error ? <p className="error">{error}</p> : null}
        </form>

        {facetas?.facetas && Object.keys(facetas.facetas).length ? (
          <section className="panel stack">
            <h2 style={{ margin: 0 }}>Facetas</h2>
            <div className="grid">
              {Object.entries(facetas.facetas).map(([name, values]) => (
                <div className="card-content" key={name}>
                  <strong>{name.replace("dados.", "")}</strong>
                  <ul className="compact-list">
                    {Object.entries(values).map(([value, total]) => <li key={value}>{value}: {total}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <section className="card">
          <div className="card-content stack">
            <div className="row">
              <div>
                <h2 style={{ margin: 0 }}>Resultados</h2>
                <p className="muted" style={{ margin: "4px 0 0" }}>
                  {resultado ? `${resultado.total} resultado(s). ${resultado.indice_defasado ? "Indice ainda sem reindexacao concluida." : ""}` : "Nenhuma pesquisa realizada."}
                </p>
              </div>
            </div>
            {pagination}
            <div className="table-wrap">
              <table className="table" aria-busy={loading}>
                <thead><tr><th>Titulo</th><th>Status</th><th>Atualizado em</th><th className="crud-actions-heading">Acoes</th></tr></thead>
                <tbody>
                  {(resultado?.items ?? []).map((item) => (
                    <tr key={item.id}>
                      <td><div className="image-title">{item.imagem_principal_thumbnail&&<img className="image-thumb" src={mediaUrl(item.imagem_principal_thumbnail)} alt="" loading="lazy"/>}<div><Link className="crud-record-link" href={`/instrumentos/${item.instrumento_id}/registros/${encodeURIComponent(item.id)}`}>{item.titulo}</Link><br/><span className="muted">{item.texto_geral}</span>{item.possui_imagens&&<p className="muted">{item.total_imagens} imagem(ns)</p>}</div></div></td>
                      <td><StatusBadge value={item.status}/></td>
                      <td>{String(item.atualizado_em).slice(0, 10)}</td>
                      <td><div className="actions"><Link className="icon-button" title="Visualizar registro" aria-label="Visualizar registro"
                        href={`/instrumentos/${item.instrumento_id}/registros/${encodeURIComponent(item.id)}`}><Eye size={16}/></Link></div></td>
                    </tr>
                  ))}
                  {resultado && !resultado.items.length ? <tr><td colSpan={4} className="muted">Nenhum registro encontrado.</td></tr> : null}
                </tbody>
              </table>
            </div>
            {pagination}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}
