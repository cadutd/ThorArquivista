"use client";

import { Save } from "lucide-react";
import { useState } from "react";
import type { Instrumento } from "@/types/domain";

export type InstrumentoFormData = {
  nome: string;
  tipo: Instrumento["tipo"];
  descricao: string;
  status: Instrumento["status"];
  visibilidade: Instrumento["visibilidade"];
};

const DEFAULT_FORM: InstrumentoFormData = {
  nome: "",
  tipo: "INVENTARIO",
  descricao: "",
  status: "RASCUNHO",
  visibilidade: "INTERNO"
};

type Props = {
  initialValue?: Partial<InstrumentoFormData>;
  saving?: boolean;
  error?: string;
  submitLabel?: string;
  onSubmit: (payload: Omit<InstrumentoFormData, "descricao"> & { descricao: string | null }) => Promise<void>;
};

export function InstrumentoForm({ initialValue, saving = false, error, submitLabel = "Salvar", onSubmit }: Props) {
  const [form, setForm] = useState<InstrumentoFormData>({ ...DEFAULT_FORM, ...initialValue });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length) return;
    await onSubmit({ ...form, nome: form.nome.trim(), descricao: form.descricao.trim() || null });
  }

  return (
    <form className="panel stack" onSubmit={submit}>
      <div className="grid">
        <Field label="Nome" required error={fieldErrors.nome}>
          <input className="input" required value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
        </Field>
        <Field label="Tipo" required error={fieldErrors.tipo}>
          <select className="select" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value as Instrumento["tipo"] })}>
            {["GUIA", "INVENTARIO", "CATALOGO", "INDICE", "BASE_TEMATICA", "OUTRO"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </Field>
        <Field label="Status" required error={fieldErrors.status}>
          <select className="select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as Instrumento["status"] })}>
            {["RASCUNHO", "PUBLICADO", "ARQUIVADO"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </Field>
        <Field label="Visibilidade" required error={fieldErrors.visibilidade}>
          <select className="select" value={form.visibilidade} onChange={(e) => setForm({ ...form, visibilidade: e.target.value as Instrumento["visibilidade"] })}>
            {["INTERNO", "PUBLICO", "RESTRITO"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Descricao">
        <textarea className="textarea" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
      </Field>
      {error ? <p className="error">{error}</p> : null}
      <div className="actions">
        <button className="button" type="submit" disabled={saving}>
          <Save size={16} />
          {saving ? "Salvando..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function validate(form: InstrumentoFormData) {
  const errors: Record<string, string> = {};
  if (!form.nome.trim()) errors.nome = "Informe o nome do instrumento.";
  if (!form.tipo) errors.tipo = "Selecione o tipo.";
  if (!form.status) errors.status = "Selecione o status.";
  if (!form.visibilidade) errors.visibilidade = "Selecione a visibilidade.";
  return errors;
}

function Field({ label, required, error, children }: { label: string; required?: boolean; error?: string; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{label}{required ? " *" : ""}</span>
      {children}
      {error ? <small className="error">{error}</small> : null}
    </label>
  );
}
