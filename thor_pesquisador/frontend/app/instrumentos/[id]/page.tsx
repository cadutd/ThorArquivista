"use client";

import Link from "next/link";
import { ArrowLeft, Edit, FileText, SlidersHorizontal } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getInstrumento } from "@/lib/api";
import type { Instrumento } from "@/types/domain";

export default function InstrumentoDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [instrumento, setInstrumento] = useState<Instrumento | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getInstrumento(id)
      .then((data) => {
        setInstrumento(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar instrumento."));
  }, [id]);

  return (
    <AppShell>
      <div className="stack">
        <div className="row">
          <div className="page-heading">
            <h1>{instrumento?.nome ?? "Instrumento"}</h1>
            <p>Visualizacao dos metadados principais.</p>
          </div>
          <div className="actions">
            <Link className="button secondary" href="/instrumentos"><ArrowLeft size={16} /> Voltar</Link>
            <Link className="button" href={`/instrumentos/${id}/editar`}><Edit size={16} /> Editar</Link>
          </div>
        </div>
        {error ? <section className="panel"><p className="error">{error}</p></section> : null}
        {instrumento ? (
          <section className="panel stack">
            <div className="detail-grid">
              <Detail label="Nome" value={instrumento.nome} />
              <Detail label="Tipo" value={instrumento.tipo} />
              <Detail label="Status" value={instrumento.status} />
              <Detail label="Visibilidade" value={instrumento.visibilidade} />
              <Detail label="Versao do schema" value={String(instrumento.schema_version)} />
              <Detail label="Criado em" value={formatDate(instrumento.criado_em)} />
              <Detail label="Atualizado em" value={formatDate(instrumento.atualizado_em)} />
            </div>
            <Detail label="Descricao" value={instrumento.descricao || "-"} />
            <div className="actions">
              <Link className="button secondary" href={`/instrumentos/${id}/campos`}><SlidersHorizontal size={16} /> Campos</Link>
              <Link className="button secondary" href={`/instrumentos/${id}/registros`}><FileText size={16} /> Registros</Link>
            </div>
          </section>
        ) : (
          <section className="panel"><p className="muted">Carregando instrumento...</p></section>
        )}
      </div>
    </AppShell>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("pt-BR");
}
