"use client";

import Link from "next/link";
import { Search } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getSchema, listRegistros, searchRegistros } from "@/lib/api";
import type { InstrumentoCampo, Registro } from "@/types/domain";

export default function RegistrosPage() {
  const { id } = useParams<{ id: string }>();
  const [nome, setNome] = useState("");
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [items, setItems] = useState<Registro[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  async function load(cursor?: string | null) {
    try {
      const [schema, page] = await Promise.all([getSchema(id), listRegistros(id, cursor)]);
      setNome(schema.nome);
      setCampos(schema.campos);
      setItems(cursor ? [...items, ...page.items] : page.items);
      setNextCursor(page.next_cursor ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar registros.");
    }
  }

  useEffect(() => { load(); }, [id]);

  async function buscar(event: React.FormEvent) {
    event.preventDefault();
    if (!q.trim()) {
      await load();
      return;
    }
    try {
      const page = await searchRegistros(id, q);
      setItems(page.items);
      setNextCursor(page.next_cursor ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar registros.");
    }
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
          <Link className="button" href={`/instrumentos/${id}/registros/novo`}>Novo registro</Link>
        </div>
      </div>
      <section className="panel stack">
        <form className="row" onSubmit={buscar}>
          <input className="input" style={{ maxWidth: 420 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Busca simples" />
          <button className="button" type="submit"><Search size={18} /> Buscar</button>
        </form>
        {error ? <p className="error">{error}</p> : null}
        <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              {listagem.map((campo) => <th key={campo.id}>{campo.nome}</th>)}
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                {listagem.map((campo) => <td key={campo.id}>{formatValue(item.dados[campo.chave])}</td>)}
                <td>{item.status}</td>
              </tr>
            ))}
            {!items.length ? <tr><td colSpan={listagem.length + 1} className="muted">Nenhum registro encontrado.</td></tr> : null}
          </tbody>
        </table>
        </div>
        {nextCursor ? <button className="button secondary" onClick={() => load(nextCursor)}>Carregar mais</button> : null}
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
