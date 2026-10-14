"use client";

import Link from "next/link";
import { Eye, Search } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { getSchema, listRegistros, searchRegistros } from "@/lib/api";
import type { InstrumentoCampo, Registro } from "@/types/domain";

export default function RegistrosPage() {
  const { id } = useParams<{ id: string }>();
  const [nome, setNome] = useState("");
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [items, setItems] = useState<Registro[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const requestId = useRef(0);
  const [error, setError] = useState("");

  const load = useCallback(async (query: string, cursor?: string | null, withSchema = false) => {
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError("");
    if (!cursor) {
      setItems([]);
      setNextCursor(null);
    }
    try {
      const [schema, page] = await Promise.all([
        withSchema ? getSchema(id) : Promise.resolve(null),
        query ? searchRegistros(id, query, cursor) : listRegistros(id, cursor)
      ]);
      if (currentRequest !== requestId.current) return;
      if (schema) {
        setNome(schema.nome);
        setCampos(schema.campos);
      }
      setItems((previous) => cursor ? [...previous, ...page.items] : page.items);
      setNextCursor(page.next_cursor ?? null);
      setError("");
    } catch (err) {
      if (currentRequest !== requestId.current) return;
      setError(err instanceof Error ? err.message : "Falha ao carregar registros.");
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    setQ("");
    setAppliedQuery("");
    setNome("");
    setCampos([]);
    load("", null, true);
    return () => { requestId.current++; };
  }, [load]);

  async function buscar(event: React.FormEvent) {
    event.preventDefault();
    if (loading) return;
    const query = q.trim();
    setAppliedQuery(query);
    await load(query);
  }

  const listagem = campos.filter((campo) => campo.aparece_listagem);

  return (
    <AppShell>
    <div className="stack">
      <div className="row">
        <div className="page-heading">
          <h1>Registros</h1>
          <p className="muted">{nome}</p>
        </div>
        <div className="actions">
          <Link className="button secondary" href="/instrumentos">Voltar</Link>
          <Permission acao="registros_incluir" instrumentoId={id}><Link className="button" href={`/instrumentos/${id}/registros/novo`}>Novo registro</Link></Permission>
        </div>
      </div>
      <section className="panel stack">
        <form className="row crud-search-form" onSubmit={buscar}>
          <input className="input" name="q" aria-label="Busca simples" style={{ maxWidth: 420 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Busca simples" />
          <button className="button" type="submit" disabled={loading}><Search size={18} />{loading ? "Buscando..." : "Buscar"}</button>
        </form>
        {error ? <p className="error">{error}</p> : null}
        <div className="table-wrap">
        <table className="table" aria-busy={loading}>
          <thead>
            <tr>
              {listagem.length ? listagem.map((campo) => <th key={campo.id}>{campo.nome}</th>) : <th>Registro</th>}
              <th>Status</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                {listagem.length ? listagem.map((campo, index) => <td key={campo.id}>{index === 0 ?
                  <Link className="crud-record-link" href={`/instrumentos/${id}/registros/${encodeURIComponent(item.id)}`}>{formatValue(item.dados[campo.chave])}</Link> :
                  formatValue(item.dados[campo.chave])}</td>) :
                  <td><Link className="crud-record-link" href={`/instrumentos/${id}/registros/${encodeURIComponent(item.id)}`}>{item.id}</Link></td>}
                <td>{item.status}</td>
                <td><Link className="icon-button" title="Visualizar registro" aria-label="Visualizar registro" href={`/instrumentos/${id}/registros/${encodeURIComponent(item.id)}`}><Eye size={16}/></Link></td>
              </tr>
            ))}
            {!items.length ? <tr><td colSpan={Math.max(1, listagem.length) + 2} className="muted">{loading ? "Carregando..." : error ? "Listagem indisponivel." : "Nenhum registro encontrado."}</td></tr> : null}
          </tbody>
        </table>
        </div>
        {nextCursor ? <button className="button secondary" disabled={loading} onClick={() => load(appliedQuery, nextCursor)}>Carregar mais</button> : null}
      </section>
    </div>
    </AppShell>
  );
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
