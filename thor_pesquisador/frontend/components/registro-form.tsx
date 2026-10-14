"use client";
import { useState } from "react";
import { Save } from "lucide-react";
import type { InstrumentoCampo } from "@/types/domain";
export function RegistroForm({campos, initial = {}, onSubmit, saving, error}: {
  campos: InstrumentoCampo[]; initial?: Record<string, unknown>;
  onSubmit: (dados: Record<string, unknown>) => Promise<void>; saving: boolean; error?: string;
}) {
  const [dados, setDados] = useState(initial);
  return <form className="stack" onSubmit={e => { e.preventDefault(); onSubmit(dados); }}>
    <div className="grid">{campos.filter(c => c.aparece_cadastro).map(c =>
      <DynamicField key={c.id} campo={c} value={dados[c.chave]} onChange={v => setDados({...dados, [c.chave]: v})}/>)}</div>
    {error && <p className="error" role="alert">{error}</p>}
    <button className="button" disabled={saving}><Save size={16}/>{saving ? "Salvando..." : "Salvar registro"}</button>
  </form>;
}
export function DynamicField({campo, value, onChange}: {
  campo: InstrumentoCampo; value: unknown; onChange: (value: unknown) => void;
}) {
  const label = campo.nome + (campo.obrigatorio ? " *" : "");
  if(campo.tipo === "BOOLEANO") return <label className="field"><span>{label}</span><select className="select"
    value={String(value ?? false)} onChange={e => onChange(e.target.value === "true")}><option value="false">Nao</option><option value="true">Sim</option></select></label>;
  if(campo.tipo === "TEXTO_LONGO") return <label className="field"><span>{label}</span><textarea className="textarea"
    required={campo.obrigatorio} value={String(value ?? "")} onChange={e => onChange(e.target.value)}/></label>;
  if(campo.tipo === "LISTA_MULTIPLA") return <label className="field"><span>{label}</span><input className="input"
    required={campo.obrigatorio} value={Array.isArray(value) ? value.join(", ") : ""} onChange={e =>
      onChange(e.target.value.split(",").map(s => s.trim()).filter(Boolean))}/></label>;
  return <label className="field"><span>{label}</span><input className="input" required={campo.obrigatorio}
    type={campo.tipo === "NUMERO" ? "number" : campo.tipo === "DATA" ? "date" : campo.tipo === "URL" ? "url" : "text"}
    value={String(value ?? "")} onChange={e => onChange(campo.tipo === "NUMERO" && e.target.value ? Number(e.target.value) : e.target.value)}/></label>;
}
