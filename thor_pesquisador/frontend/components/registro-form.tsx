"use client";
import { useState } from "react";
import { Save } from "lucide-react";
import type { InstrumentoCampo } from "@/types/domain";
export function RegistroForm({campos, initial = {}, onSubmit, saving, error}: {
  campos: InstrumentoCampo[]; initial?: Record<string, unknown>;
  onSubmit: (dados: Record<string, unknown>) => Promise<void>; saving: boolean; error?: string;
}) {
  const [dados, setDados] = useState<Record<string, unknown>>(() => ({
    ...Object.fromEntries(campos.filter(c => c.aparece_cadastro && c.tipo === "BOOLEANO").map(c => [c.chave, false])),
    ...initial
  }));
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (saving) return;
    const errors: Record<string, string> = {};
    for (const campo of campos.filter(c => c.aparece_cadastro && c.obrigatorio)) {
      const value = dados[campo.chave];
      if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length))
        errors[campo.chave] = "Informe " + campo.nome + ".";
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length) return;
    const known = new Set(campos.map(c => c.chave));
    const normalized = Object.fromEntries(Object.entries(dados).filter(([key]) => known.has(key)).map(([key, value]) =>
      [key, value === "" ? null : value]));
    await onSubmit(normalized);
  }
  return <form className="panel stack" onSubmit={submit}>
    <fieldset className="registro-fields" disabled={saving}>
    <div className="grid">{campos.filter(c => c.aparece_cadastro).map(c =>
      <div key={c.id} className={c.tipo === "TEXTO_LONGO" ? "crud-field-wide" : undefined}><DynamicField campo={c} value={dados[c.chave]} onChange={v => setDados({...dados, [c.chave]: v})}/>
        {fieldErrors[c.chave] && <p className="error" role="alert">{fieldErrors[c.chave]}</p>}</div>)}</div>
    </fieldset>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions"><button className="button" type="submit" disabled={saving}><Save size={16}/>{saving ? "Salvando..." : "Salvar registro"}</button></div>
  </form>;
}
export function DynamicField({campo, value, onChange, filter = false}: {
  campo: InstrumentoCampo; value: unknown; onChange: (value: unknown) => void; filter?: boolean;
}) {
  const required = campo.obrigatorio && !filter;
  const label = campo.nome + (required ? " *" : "");
  if(campo.tipo === "BOOLEANO") return <label className="field"><span>{label}</span><select className="select" aria-label={label}
    value={String(value ?? (filter ? "" : false))} onChange={e => onChange(e.target.value === "" ? null : e.target.value === "true")}>
    {filter && <option value="">Todos</option>}<option value="false">Nao</option><option value="true">Sim</option></select></label>;
  if(campo.tipo === "TEXTO_LONGO") return <label className="field"><span>{label}</span><textarea className="textarea"
    required={required} value={String(value ?? "")} onChange={e => onChange(e.target.value)}/></label>;
  if(campo.tipo === "LISTA_MULTIPLA") return <label className="field"><span>{label}</span><input className="input"
    required={required} value={Array.isArray(value) ? value.join(", ") : ""} onChange={e =>
      onChange(e.target.value.split(",").map(s => s.trim()).filter(Boolean))}/></label>;
  return <label className="field"><span>{label}</span><input className="input" required={required} step={campo.tipo === "NUMERO" ? "any" : undefined}
    type={campo.tipo === "NUMERO" ? "number" : campo.tipo === "DATA" ? "date" : campo.tipo === "URL" && !filter ? "url" : "text"}
    value={String(value ?? "")} onChange={e => onChange(campo.tipo === "NUMERO" && e.target.value ? Number(e.target.value) : e.target.value)}/></label>;
}
