"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { DynamicInstrumentForm } from "@/features/instrumentos-pesquisa/dynamic-instrument-form";
import { createInstrumentoRegistro, getInstrumentoPesquisaSchema } from "@/lib/api/domain";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function DynamicInstrumentCadastroPage({ instrumentoId }: { instrumentoId: string }) {
  const [lastSubmit, setLastSubmit] = useState<Record<string, unknown> | null>(null);
  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });
  const createRegistro = useMutation({
    mutationFn: (dados: Record<string, unknown>) => createInstrumentoRegistro(instrumentoId, { dados }),
    onSuccess: (registro) => setLastSubmit({ id: registro.id, dados: registro.dados }),
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
          <DynamicInstrumentForm schema={schema} onSubmit={(values) => createRegistro.mutate(values)} />
          {createRegistro.error ? <p className="mt-3 text-sm text-destructive">{createRegistro.error.message}</p> : null}
        </CardContent>
      </Card>
      {lastSubmit ? (
        <Card>
          <CardHeader>
            <CardTitle>Registro salvo</CardTitle>
            <CardDescription>Documento criado no MongoDB para este instrumento.</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(lastSubmit, null, 2)}</pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
