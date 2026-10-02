"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { createCampo, getInstrumento, listCampos } from "@/lib/api";
import type { Instrumento, InstrumentoCampo, TipoCampo } from "@/types/domain";

export default function CamposPage() {
  const { id } = useParams<{ id: string }>();
  const [instrumento, setInstrumento] = useState<Instrumento | null>(null);
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    nome: "",
    chave: "",
    tipo: "TEXTO_CURTO" as TipoCampo,
    ordem: 0,
    obrigatorio: false,
    aparece_busca: true,
    aparece_listagem: true,
    aparece_cadastro: true,
    filtro_avancado: false,
    facetavel: false,
    ordenavel: false
  });

  async function load() {
    try {
      const [inst, list] = await Promise.all([getInstrumento(id), listCampos(id)]);
      setInstrumento(inst);
      setCampos(list);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar campos.");
    }
  }

  useEffect(() => { load(); }, [id]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createCampo(id, { ...form, multiplo: form.tipo === "LISTA_MULTIPLA" });
      setForm({ ...form, nome: "", chave: "", ordem: form.ordem + 1 });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar campo.");
    }
  }

  return (
    <AppShell>
    <div className="stack">
      <div className="row">
        <div className="page-heading">
          <h1>Campos</h1>
          <p className="muted">{instrumento?.nome}</p>
        </div>
        <Link className="button secondary" href="/instrumentos">Voltar</Link>
      </div>
      <form className="panel stack" onSubmit={submit}>
        <h2>Novo campo</h2>
        <div className="grid">
          <Field label="Nome"><input className="input" required value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} /></Field>
          <Field label="Chave"><input className="input" required pattern="^[a-zA-Z][a-zA-Z0-9_]*$" value={form.chave} onChange={(e) => setForm({ ...form, chave: e.target.value })} /></Field>
          <Field label="Tipo">
            <select className="select" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoCampo })}>
              {["TEXTO_CURTO", "TEXTO_LONGO", "NUMERO", "DATA", "BOOLEANO", "LISTA_SIMPLES", "LISTA_MULTIPLA", "URL"].map((tipo) => <option key={tipo}>{tipo}</option>)}
            </select>
          </Field>
          <Field label="Ordem"><input className="input" type="number" value={form.ordem} onChange={(e) => setForm({ ...form, ordem: Number(e.target.value) })} /></Field>
        </div>
        <div className="actions">
          <label><input type="checkbox" checked={form.obrigatorio} onChange={(e) => setForm({ ...form, obrigatorio: e.target.checked })} /> Obrigatorio</label>
          <label><input type="checkbox" checked={form.aparece_cadastro} onChange={(e) => setForm({ ...form, aparece_cadastro: e.target.checked })} /> Cadastro</label>
          <label><input type="checkbox" checked={form.aparece_listagem} onChange={(e) => setForm({ ...form, aparece_listagem: e.target.checked })} /> Listagem</label>
          <label><input type="checkbox" checked={form.aparece_busca} onChange={(e) => setForm({ ...form, aparece_busca: e.target.checked })} /> Busca</label>
          <label><input type="checkbox" checked={form.filtro_avancado} onChange={(e) => setForm({ ...form, filtro_avancado: e.target.checked })} /> Filtro avancado</label>
          <label><input type="checkbox" checked={form.facetavel} onChange={(e) => setForm({ ...form, facetavel: e.target.checked })} /> Faceta</label>
          <label><input type="checkbox" checked={form.ordenavel} onChange={(e) => setForm({ ...form, ordenavel: e.target.checked })} /> Ordenacao</label>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="button" type="submit">Adicionar campo</button>
      </form>
      <section className="panel">
        <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Ordem</th><th>Nome</th><th>Chave</th><th>Tipo</th><th>Obrigatorio</th><th>Busca avancada</th></tr></thead>
          <tbody>
            {campos.map((campo) => <tr key={campo.id}><td>{campo.ordem}</td><td>{campo.nome}</td><td>{campo.chave}</td><td>{campo.tipo}</td><td>{campo.obrigatorio ? "Sim" : "Nao"}</td><td>{[campo.filtro_avancado ? "Filtro" : "", campo.facetavel ? "Faceta" : "", campo.ordenavel ? "Ordenacao" : ""].filter(Boolean).join(", ") || "Nao"}</td></tr>)}
          </tbody>
        </table>
        </div>
      </section>
    </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}
