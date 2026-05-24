"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FichaEspelhoPreview } from "@/features/ficha-espelho/ficha-espelho-preview";
import { obterModeloFichaEspelho } from "@/lib/api/ficha-espelho";
import { campoFichaEspelhoLabels } from "@/types/ficha-espelho";

export function ModeloFichaViewPage() {
  const params = useParams<{ id: string }>();
  const modeloId = Number(params.id);
  const query = useQuery({
    queryKey: ["fichas-espelho", "modelos", modeloId],
    queryFn: () => obterModeloFichaEspelho(modeloId),
    enabled: Number.isFinite(modeloId),
  });
  const modelo = query.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar modelo de ficha</h1>
          <p className="text-sm text-muted-foreground">Confira dados, campos e prévia de impressão do modelo.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {modelo ? (
            <Button asChild>
              <Link href={`/modelos-ficha-espelho/${modelo.id}/editar`}>
                <Edit className="h-4 w-4" />
                Editar
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="outline">
            <Link href="/modelos-ficha-espelho">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
        </div>
      </div>

      {query.isLoading ? <p className="text-sm text-muted-foreground">Carregando modelo...</p> : null}
      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}

      {modelo ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,520px)]">
          <Card>
            <CardHeader>
              <CardTitle>{modelo.nome}</CardTitle>
              <CardDescription>{modelo.descricao || "Sem descrição informada."}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-3 md:grid-cols-2">
                <ReadOnlyItem label="Status" value={modelo.ativo ? "Ativo" : "Inativo"} />
                <ReadOnlyItem label="Papel" value={modelo.tamanho_papel === "CARTA" ? "Carta" : "A4"} />
                <ReadOnlyItem label="Orientação" value={modelo.orientacao === "PAISAGEM" ? "Paisagem" : "Retrato"} />
                <ReadOnlyItem label="Colunas por página" value={String(modelo.colunas)} />
                <ReadOnlyItem label="Largura" value={`${modelo.largura_cm} cm`} />
                <ReadOnlyItem label="Altura" value={`${modelo.altura_cm} cm`} />
              </div>

              <section className="space-y-2">
                <h2 className="text-base font-semibold">Campos da ficha</h2>
                <div className="grid gap-2 md:grid-cols-2">
                  {modelo.campos.map((campo) => (
                    <div key={campo} className="rounded-md border px-3 py-2 text-sm">
                      {campoFichaEspelhoLabels[campo]}
                    </div>
                  ))}
                </div>
              </section>
            </CardContent>
          </Card>

          <section className="space-y-3">
            <div>
              <h2 className="text-base font-semibold">Prévia de impressão</h2>
              <p className="text-sm text-muted-foreground">Representação visual em escala do modelo selecionado.</p>
            </div>
            <FichaEspelhoPreview modelo={modelo} />
          </section>
        </div>
      ) : null}
    </div>
  );
}

function ReadOnlyItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}
