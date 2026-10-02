"use client";

import Link from "next/link";
import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { listInstrumentos } from "@/lib/api";
import type { Instrumento } from "@/types/domain";

export default function InstrumentosPage() {
  const [items, setItems] = useState<Instrumento[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const page = await listInstrumentos({ q });
      setItems(page.items);
      setTotal(page.total);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar instrumentos.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <AppShell>
      <div className="stack">
        <div className="row">
          <div className="page-heading">
            <h1>Instrumentos</h1>
            <p className="muted">{total} instrumentos encontrados</p>
          </div>
          <Link className="button" href="/instrumentos/novo">
            <Plus size={18} />
            Novo instrumento
          </Link>
        </div>
        <section className="panel stack">
          <form
            className="row"
            onSubmit={(event) => {
              event.preventDefault();
              load();
            }}
          >
            <input className="input" style={{ maxWidth: 420 }} value={q} onChange={(event) => setQ(event.target.value)} placeholder="Buscar por nome ou descricao" />
            <button className="button" type="submit">
              <Search size={18} />
              Buscar
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
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
                  <td>{item.nome}</td>
                  <td>{item.tipo}</td>
                  <td>{item.status}</td>
                  <td>{item.visibilidade}</td>
                  <td className="actions">
                    <Link className="button secondary" href={`/instrumentos/${item.id}/campos`}>Campos</Link>
                    <Link className="button secondary" href={`/instrumentos/${item.id}/registros`}>Registros</Link>
                  </td>
                </tr>
              ))}
              {!items.length ? (
                <tr><td colSpan={5} className="muted">Nenhum instrumento encontrado.</td></tr>
              ) : null}
            </tbody>
          </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
