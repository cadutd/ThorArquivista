"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { DynamicInstrumentForm } from "@/features/instrumentos-pesquisa/dynamic-instrument-form";
import {
  createInstrumentoRegistro,
  getInstrumentoPesquisaSchema,
  getInstrumentoRegistro,
  updateInstrumentoRegistro,
} from "@/lib/api/domain";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function InstrumentoRegistroFormPage({
  instrumentoId,
  registroId,
}: {
  instrumentoId: string;
  registroId?: string;
}) {
  const router = useRouter();
  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });
  const registroQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "registros", registroId],
    queryFn: () => getInstrumentoRegistro(instrumentoId, registroId ?? ""),
    enabled: Boolean(registroId),
  });
  const mutation = useMutation({
    mutationFn: (dados: Record<string, unknown>) =>
      registroId
        ? updateInstrumentoRegistro(instrumentoId, registroId, { dados })
        : createInstrumentoRegistro(instrumentoId, { dados }),
    onSuccess: () => router.push(`/instrumentos-pesquisa/${instrumentoId}/registros`),
  });

  if (schemaQuery.isLoading || registroQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando formulário...</p>;
  }

  if (schemaQuery.error) {
    return <p className="text-sm text-destructive">{schemaQuery.error.message}</p>;
  }

  if (registroQuery.error) {
    return <p className="text-sm text-destructive">{registroQuery.error.message}</p>;
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
          {registroId ? "Edição de registro dinâmico." : "Cadastro de registro dinâmico."}
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{registroId ? "Editar registro" : "Novo registro"}</CardTitle>
          <CardDescription>{schema.campos.filter((campo) => campo.aparece_cadastro).length} campos no formulário.</CardDescription>
        </CardHeader>
        <CardContent>
          <DynamicInstrumentForm
            schema={schema}
            initialValues={registroQuery.data?.dados}
            isSaving={mutation.isPending}
            submitLabel={registroId ? "Salvar alterações" : "Criar registro"}
            onSubmit={(values) => mutation.mutate(values)}
          />
          {mutation.error ? <p className="mt-3 text-sm text-destructive">{mutation.error.message}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
