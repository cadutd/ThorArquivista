"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UnidadeForm } from "@/features/unidades/unidade-form";
import { getUnidade } from "@/lib/api/domain";

type Props = {
  unidadeId: number;
};

export function UnidadeEditPage({ unidadeId }: Props) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["unidades", unidadeId],
    queryFn: () => getUnidade(unidadeId),
    enabled: Number.isFinite(unidadeId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar unidade</h1>
          <p className="text-sm text-muted-foreground">
            Atualize os metadados da unidade de acondicionamento.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/unidades">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Edição</CardTitle>
          <CardDescription>
            {query.data
              ? `Unidade ${query.data.identificador}`
              : "Carregando dados da unidade."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando unidade...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <UnidadeForm unidade={query.data} onSaved={() => router.push("/unidades")} />
          ) : (
            <p className="text-sm text-muted-foreground">Unidade não encontrada.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
