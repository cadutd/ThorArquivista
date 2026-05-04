"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DynamicInstrumentForm } from "@/features/instrumentos-pesquisa/dynamic-instrument-form";
import { getInstrumentoPesquisaSchema } from "@/lib/api/domain";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function DynamicInstrumentCadastroPage({ instrumentoId }: { instrumentoId: string }) {
  const [lastSubmit, setLastSubmit] = useState<Record<string, unknown> | null>(null);
  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });

  if (schemaQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando schema do instrumento...</p>;
  }

  if (schemaQuery.error) {
    return <p className="text-sm text-destructive">{schemaQuery.error.message}</p>;
  }

  const schema = schemaQuery.data;
  if (!schema) {
    return <p className="text-sm text-muted-foreground">Schema não encontrado.</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{schema.instrumento.nome}</h1>
        <p className="text-sm text-muted-foreground">
          Cadastro dinâmico montado a partir dos campos configurados no instrumento.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Novo registro</CardTitle>
          <CardDescription>{schema.campos.filter((campo) => campo.aparece_cadastro).length} campos no formulário.</CardDescription>
        </CardHeader>
        <CardContent>
          <DynamicInstrumentForm schema={schema} onSubmit={(values) => setLastSubmit(values)} />
        </CardContent>
      </Card>
      {lastSubmit ? (
        <Card>
          <CardHeader>
            <CardTitle>Payload do formulário</CardTitle>
            <CardDescription>Prévia dos dados capturados pelo componente dinâmico.</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(lastSubmit, null, 2)}</pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
