"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getMidia } from "@/lib/api/domain";
import type { MidiaArmazenamento } from "@/types/domain";

export function MidiaViewPage({ midiaId }: { midiaId: number }) {
  const query = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const midia = query.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar mídia</h1>
          <p className="text-sm text-muted-foreground">Consulta dos metadados da mídia de armazenamento.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/midias">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{midia?.nome ?? "Mídia de armazenamento"}</CardTitle>
          <CardDescription>
            {query.isLoading
              ? "Carregando dados da mídia."
              : midia
                ? midia.tipo
                : "Mídia não encontrada."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando mídia...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : midia ? (
            <MidiaDetails midia={midia} />
          ) : (
            <p className="text-sm text-muted-foreground">Mídia não encontrada.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MidiaDetails({ midia }: { midia: MidiaArmazenamento }) {
  const fields: Array<[string, ReactNode]> = [
    ["ID", midia.id],
    ["Nome", midia.nome],
    ["Tipo", midia.tipo],
    ["Status", <StatusBadge key="status" value={midia.ativo ? "ATIVA" : "INATIVA"} />],
    ["Descrição", midia.descricao || "-"],
    ["Posição de armazenamento", midia.id_posicao_armazenamento ?? "-"],
    ["Criado em", formatDateTime(midia.criado_em)],
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2">
      {fields.map(([label, value]) => (
        <div key={label} className="rounded-md border p-3">
          <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
          <div className="mt-1 text-sm">{value}</div>
        </div>
      ))}
    </section>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
