"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { InstrumentoForm, type InstrumentoFormData } from "@/components/instrumento-form";
import { getInstrumento, updateInstrumento } from "@/lib/api";

export default function EditarInstrumentoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [initialValue, setInitialValue] = useState<InstrumentoFormData | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getInstrumento(id)
      .then((instrumento) => {
        setInitialValue({
          nome: instrumento.nome,
          tipo: instrumento.tipo,
          descricao: instrumento.descricao ?? "",
          status: instrumento.status,
          visibilidade: instrumento.visibilidade
        });
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar instrumento."));
  }, [id]);

  async function submit(payload: Parameters<typeof updateInstrumento>[1]) {
    setSaving(true);
    setError("");
    try {
      await updateInstrumento(id, payload);
      router.push("/instrumentos");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar instrumento.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="stack">
        <div className="row">
          <div className="page-heading">
            <h1>Editar instrumento</h1>
            <p>Atualize os metadados principais do instrumento.</p>
          </div>
          <Link className="button secondary" href="/instrumentos"><ArrowLeft size={16} /> Voltar</Link>
        </div>
        {initialValue ? (
          <InstrumentoForm initialValue={initialValue} onSubmit={submit} saving={saving} error={error} submitLabel="Salvar alteracoes" />
        ) : (
          <section className="panel">{error ? <p className="error">{error}</p> : <p className="muted">Carregando instrumento...</p>}</section>
        )}
      </div>
    </AppShell>
  );
}
