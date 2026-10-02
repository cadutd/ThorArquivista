"use client";

import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { createInstrumento } from "@/lib/api";
import type { Instrumento } from "@/types/domain";

export default function NovoInstrumentoPage() {
  const [form, setForm] = useState({
    nome: "",
    tipo: "INVENTARIO" as Instrumento["tipo"],
    descricao: "",
    status: "RASCUNHO" as Instrumento["status"],
    visibilidade: "INTERNO" as Instrumento["visibilidade"]
  });
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createInstrumento({ ...form, descricao: form.descricao || null });
      window.location.assign("/instrumentos");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar instrumento.");
    }
  }

  return (
    <AppShell>
    <div className="stack">
      <div className="row">
        <div className="page-heading">
          <h1>Novo instrumento</h1>
          <p>Configure os metadados principais do instrumento.</p>
        </div>
        <Link className="button secondary" href="/instrumentos">Voltar</Link>
      </div>
      <form className="panel stack" onSubmit={submit}>
        <div className="grid">
          <Field label="Nome" required>
            <input className="input" required value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
          </Field>
          <Field label="Tipo" required>
            <select className="select" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value as Instrumento["tipo"] })}>
              {["GUIA", "INVENTARIO", "CATALOGO", "INDICE", "BASE_TEMATICA", "OUTRO"].map((item) => <option key={item}>{item}</option>)}
            </select>
          </Field>
          <Field label="Status" required>
            <select className="select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as Instrumento["status"] })}>
              {["RASCUNHO", "PUBLICADO", "ARQUIVADO"].map((item) => <option key={item}>{item}</option>)}
            </select>
          </Field>
          <Field label="Visibilidade" required>
            <select className="select" value={form.visibilidade} onChange={(e) => setForm({ ...form, visibilidade: e.target.value as Instrumento["visibilidade"] })}>
              {["INTERNO", "PUBLICO", "RESTRITO"].map((item) => <option key={item}>{item}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Descricao">
          <textarea className="textarea" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
        </Field>
        {error ? <p className="error">{error}</p> : null}
        <button className="button" type="submit">Salvar</button>
      </form>
    </div>
    </AppShell>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return <label className="field"><span>{label}{required ? " *" : ""}</span>{children}</label>;
}
