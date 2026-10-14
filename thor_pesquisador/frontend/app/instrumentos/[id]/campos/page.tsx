"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { ModalFrame } from "@/components/modal-frame";
import { createCampo, getInstrumento, listCampos, request } from "@/lib/api";
import type { Instrumento, InstrumentoCampo, TipoCampo } from "@/types/domain";

export default function CamposPage() {
  const { id } = useParams<{ id: string }>();
  const [instrumento, setInstrumento] = useState<Instrumento | null>(null);
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<InstrumentoCampo>();
  const [form, setForm] = useState({
    nome: "",
    chave: "",
    tipo: "TEXTO_CURTO" as TipoCampo,
    ordem: 0,
    obrigatorio: false,
    aparece_busca: true,
    exibir_publico: false,
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
      <Permission acao="campos_incluir" instrumentoId={id}><form className="panel stack" onSubmit={submit}>
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
          <label><input type="checkbox" checked={form.exibir_publico} onChange={(e) => setForm({ ...form, exibir_publico: e.target.checked })} /> Exibir publico</label>
          <label><input type="checkbox" checked={form.filtro_avancado} onChange={(e) => setForm({ ...form, filtro_avancado: e.target.checked })} /> Filtro avancado</label>
          <label><input type="checkbox" checked={form.facetavel} onChange={(e) => setForm({ ...form, facetavel: e.target.checked })} /> Faceta</label>
          <label><input type="checkbox" checked={form.ordenavel} onChange={(e) => setForm({ ...form, ordenavel: e.target.checked })} /> Ordenacao</label>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="button" type="submit">Adicionar campo</button>
      </form></Permission>
      <section className="panel">
        <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Nome</th><th>Ordem</th><th>Chave</th><th>Tipo</th><th>Obrigatorio</th><th>Busca avancada</th><th>Publico</th></tr></thead>
          <tbody>
            {campos.map((campo) => <tr key={campo.id}><td><a className="crud-record-link" href={"#campo-" + campo.id} onClick={e => {e.preventDefault();setSelected(campo);}}>{campo.nome}</a></td><td>{campo.ordem}</td><td>{campo.chave}</td><td>{campo.tipo}</td><td>{campo.obrigatorio ? "Sim" : "Nao"}</td><td>{[campo.filtro_avancado ? "Filtro" : "", campo.facetavel ? "Faceta" : "", campo.ordenavel ? "Ordenacao" : ""].filter(Boolean).join(", ") || "Nao"}</td><td>{campo.exibir_publico ? "Sim" : "Nao"}<Permission acao="campos_editar" instrumentoId={id}><input type="checkbox" aria-label={"Exibir publicamente " + campo.nome} checked={!!campo.exibir_publico} onChange={e => request("/instrumentos/" + id + "/campos/" + campo.id, {method:"PUT", body:JSON.stringify({exibir_publico:e.target.checked})}).then(load).catch(e=>setError(e.message))}/></Permission></td></tr>)}
          </tbody>
        </table>
        </div>
      </section>
      {selected && <ModalFrame title="Visualizar campo" onClose={() => setSelected(undefined)}>
        <div className="row"><h2>{selected.nome}</h2><button className="button secondary" autoFocus onClick={() => setSelected(undefined)}>Fechar</button></div>
        <dl className="detail-grid">{Object.entries({Nome:selected.nome,Chave:selected.chave,Tipo:selected.tipo,Ordem:selected.ordem,
          Obrigatorio:selected.obrigatorio ? "Sim" : "Nao",Publico:selected.exibir_publico ? "Sim" : "Nao"}).map(([key,value]) =>
          <div className="detail-item" key={key}><dt>{key}</dt><dd>{String(value)}</dd></div>)}</dl>
      </ModalFrame>}
    </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}
