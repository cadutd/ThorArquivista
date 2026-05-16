"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ModeloFichaForm } from "@/features/ficha-espelho/modelo-ficha-form";
import { obterModeloFichaEspelho } from "@/lib/api/ficha-espelho";

export function ModeloFichaEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const modeloId = Number(params.id);
  const query = useQuery({
    queryKey: ["fichas-espelho", "modelos", modeloId],
    queryFn: () => obterModeloFichaEspelho(modeloId),
    enabled: Number.isFinite(modeloId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar modelo de ficha</h1>
          <p className="text-sm text-muted-foreground">Atualize dimensão, campos e parâmetros de impressão.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/modelos-ficha-espelho">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Modelo</CardTitle>
          <CardDescription>Campos obrigatórios são marcados com asterisco.</CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? <p className="text-sm text-muted-foreground">Carregando modelo...</p> : null}
          {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
          {query.data ? <ModeloFichaForm modelo={query.data} onSaved={() => router.push("/modelos-ficha-espelho")} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}
