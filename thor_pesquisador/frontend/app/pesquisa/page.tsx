"use client";

import { RefreshCw, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { buscarAvancado, getFacetas, getSchema, listInstrumentos, reindexarInstrumento } from "@/lib/api";
import type { BuscaAvancadaResultado, FacetasResultado, Instrumento, InstrumentoCampo } from "@/types/domain";

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
    Promise.all([getSchema(instrumentoId), getFacetas(instrumentoId).catch(() => null)])
      .then(([schema, facetData]) => {
        setCampos(schema.campos);
        setFacetas(facetData);
        setFilters({});
        setResultado(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar schema."));
  }, [instrumentoId]);

  const filterable = useMemo(() => campos.filter((campo) => campo.filtro_avancado), [campos]);
  const sortable = useMemo(() => campos.filter((campo) => campo.ordenavel), [campos]);

  async function pesquisar(event?: React.FormEvent) {
    event?.preventDefault();
    if (!instrumentoId) return;
    try {
      const cleanFilters = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ""));
      const data = await buscarAvancado(instrumentoId, {
        q,
        filters: cleanFilters,
        sort: sort ? [sort] : [],
        limit: 20,
        offset: 0
      });
      setResultado(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na busca avancada.");
    }
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

  return (
    <AppShell>
      <div className="stack">
        <div className="page-heading">
          <h1>Pesquisa</h1>
          <p>Busca avancada em indice Meilisearch derivado dos registros dinamicos.</p>
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
            <button className="button" type="submit"><Search size={16} /> Pesquisar</button>
            <button className="button secondary" type="button" onClick={reindexar}><RefreshCw size={16} /> Reindexar instrumento</button>
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
                  {resultado ? `${resultado.total} resultado(s). ${resultado.indice_defasado ? "Indice ainda sem reindexacao concluida." : ""}` : "Execute uma busca para listar registros indexados."}
                </p>
              </div>
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Titulo</th><th>Status</th><th>Atualizado em</th></tr></thead>
                <tbody>
                  {(resultado?.items ?? []).map((item) => (
                    <tr key={item.id}>
                      <td><strong>{item.titulo}</strong><br /><span className="muted">{item.texto_geral}</span></td>
                      <td>{item.status}</td>
                      <td>{String(item.atualizado_em).slice(0, 10)}</td>
                    </tr>
                  ))}
                  {resultado && !resultado.items.length ? <tr><td colSpan={3} className="muted">Nenhum registro encontrado.</td></tr> : null}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}
