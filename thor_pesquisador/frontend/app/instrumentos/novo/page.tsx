"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { InstrumentoForm } from "@/components/instrumento-form";
import { createInstrumento } from "@/lib/api";

export default function NovoInstrumentoPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(payload: Parameters<typeof createInstrumento>[0]) {
    setSaving(true);
    setError("");
    try {
      await createInstrumento(payload);
      router.push("/instrumentos");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar instrumento.");
    } finally {
      setSaving(false);
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
          <Link className="button secondary" href="/instrumentos"><ArrowLeft size={16} /> Voltar</Link>
        </div>
        <InstrumentoForm onSubmit={submit} saving={saving} error={error} submitLabel="Salvar instrumento" />
      </div>
    </AppShell>
  );
}
