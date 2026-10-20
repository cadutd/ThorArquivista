"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { RegistroForm } from "@/components/registro-form";
import { Permission } from "@/components/permission";
import { createRegistro, getSchema } from "@/lib/api";
import type { InstrumentoCampo } from "@/types/domain";

export default function NovoRegistroPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [schema, setSchema] = useState<{ nome: string; campos: InstrumentoCampo[] }>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const base = `/instrumentos/${id}/registros`;

  useEffect(() => {
    let current = true;
    setSchema(undefined); setError("");
    getSchema(id).then(value => { if (current) setSchema(value); })
      .catch(err => { if (current) setError(err instanceof Error ? err.message : "Falha ao carregar campos."); });
    return () => { current = false; };
  }, [id]);

  async function save(dados: Record<string, unknown>) {
    if (!schema || saving) return;
    setSaving(true); setError("");
    try {
      await createRegistro(id, { dados, status: "ATIVO" });
      router.push(base);
    } catch (err) { setError(err instanceof Error ? err.message : "Falha ao criar registro."); }
    finally { setSaving(false); }
  }

  return <AppShell><div className="stack">
    <div className="row">
      <div className="page-heading"><h1>Novo registro</h1><p className="muted">{schema?.nome}</p></div>
      <Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link>
    </div>
    {!schema && <section className="panel">{error ? <p className="error" role="alert">{error}</p> : <p className="muted">Carregando...</p>}</section>}
    <Permission acao="registros_incluir" instrumentoId={id}>{schema && <RegistroForm key={id}
      campos={schema.campos} onSubmit={save} saving={saving} error={error}/>}</Permission>
  </div></AppShell>;
}
