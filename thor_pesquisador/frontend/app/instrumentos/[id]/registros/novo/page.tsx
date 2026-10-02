"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { createRegistro, getSchema } from "@/lib/api";
import type { InstrumentoCampo } from "@/types/domain";

export default function NovoRegistroPage() {
  const { id } = useParams<{ id: string }>();
  const [nome, setNome] = useState("");
  const [campos, setCampos] = useState<InstrumentoCampo[]>([]);
  const [dados, setDados] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    getSchema(id)
      .then((schema) => {
        setNome(schema.nome);
        setCampos(schema.campos.filter((campo) => campo.aparece_cadastro));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar schema."));
  }, [id]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createRegistro(id, { dados: normalizeDados(campos, dados), status: "ATIVO" });
      window.location.assign(`/instrumentos/${id}/registros`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar registro.");
    }
  }

  return (
    <AppShell>
    <div className="stack">
      <div className="row">
        <div className="page-heading">
          <h1>Novo registro</h1>
          <p className="muted">{nome}</p>
        </div>
        <Link className="button secondary" href={`/instrumentos/${id}/registros`}>Voltar</Link>
      </div>
      <form className="panel stack" onSubmit={submit}>
        <div className="grid">
          {campos.map((campo) => (
            <DynamicField
              key={campo.id}
              campo={campo}
              value={dados[campo.chave]}
              onChange={(value) => setDados({ ...dados, [campo.chave]: value })}
            />
          ))}
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="button" type="submit">Salvar registro</button>
      </form>
    </div>
    </AppShell>
  );
}

function DynamicField({ campo, value, onChange }: { campo: InstrumentoCampo; value: unknown; onChange: (value: unknown) => void }) {
  const label = `${campo.nome}${campo.obrigatorio ? " *" : ""}`;
  if (campo.tipo === "TEXTO_LONGO") {
    return <label className="field"><span>{label}</span><textarea className="textarea" required={campo.obrigatorio} value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} /></label>;
  }
  if (campo.tipo === "NUMERO") {
    return <label className="field"><span>{label}</span><input className="input" type="number" required={campo.obrigatorio} value={String(value ?? "")} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")} /></label>;
  }
  if (campo.tipo === "DATA") {
    return <label className="field"><span>{label}</span><input className="input" type="date" required={campo.obrigatorio} value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} /></label>;
  }
  if (campo.tipo === "BOOLEANO") {
    return <label className="field"><span>{label}</span><select className="select" value={String(value ?? "false")} onChange={(e) => onChange(e.target.value === "true")}><option value="false">Nao</option><option value="true">Sim</option></select></label>;
  }
  if (campo.tipo === "LISTA_MULTIPLA") {
    return <label className="field"><span>{label}</span><input className="input" placeholder="Separe valores por virgula" value={Array.isArray(value) ? value.join(", ") : ""} onChange={(e) => onChange(e.target.value.split(",").map((item) => item.trim()).filter(Boolean))} /></label>;
  }
  return <label className="field"><span>{label}</span><input className="input" type={campo.tipo === "URL" ? "url" : "text"} required={campo.obrigatorio} value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} /></label>;
}

function normalizeDados(campos: InstrumentoCampo[], dados: Record<string, unknown>) {
  return Object.fromEntries(
    campos
      .map((campo) => [campo.chave, dados[campo.chave]])
      .filter(([, value]) => value !== undefined && value !== "")
  );
}
