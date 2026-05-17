"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getEntidadeProdutora } from "@/lib/api/entidades-produtoras";
import { EntidadeProdutoraForm } from "./entidade-produtora-form";

export function EntidadeProdutoraEditPage({ entidadeId }: { entidadeId: string }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["entidades-produtoras", entidadeId],
    queryFn: () => getEntidadeProdutora(entidadeId),
    enabled: Boolean(entidadeId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar entidade produtora</h1>
          <p className="text-sm text-muted-foreground">Atualize os dados cadastrais e hierárquicos.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/entidades-produtoras">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Edição</CardTitle>
          <CardDescription>{query.data ? query.data.nome : "Carregando dados da entidade."}</CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando entidade...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <EntidadeProdutoraForm entidade={query.data} onSaved={() => router.push("/entidades-produtoras")} />
          ) : (
            <p className="text-sm text-muted-foreground">Entidade não encontrada.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
