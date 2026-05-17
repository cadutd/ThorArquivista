"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getProcessoAdmissao } from "@/lib/api/admissao";
import { ProcessoAdmissaoForm } from "./processo-admissao-form";

export function ProcessoAdmissaoEditPage({ id }: { id: string }) {
  const router = useRouter();
  const query = useQuery({ queryKey: ["admissao", "processos", id], queryFn: () => getProcessoAdmissao(id) });
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar processo</h1>
          <p className="text-sm text-muted-foreground">{query.data?.numero_processo ?? "Carregando processo..."}</p>
        </div>
        <Button asChild variant="outline"><Link href={query.data ? `/admissao/${query.data.id}` : "/admissao"}><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Processo de Admissão</CardTitle><CardDescription>Atualize os dados do dossiê de admissão.</CardDescription></CardHeader>
        <CardContent>
          {query.isLoading ? <p className="text-sm text-muted-foreground">Carregando...</p> : query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : query.data ? <ProcessoAdmissaoForm processo={query.data} onSaved={(processo) => router.push(`/admissao/${processo.id}`)} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}
