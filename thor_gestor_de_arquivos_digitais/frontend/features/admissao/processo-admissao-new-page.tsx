"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProcessoAdmissaoForm } from "./processo-admissao-form";

export function ProcessoAdmissaoNewPage() {
  const router = useRouter();
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Novo processo de admissão</h1>
          <p className="text-sm text-muted-foreground">Abra o dossiê operacional antes de acordos, sessões e SIPs.</p>
        </div>
        <Button asChild variant="outline"><Link href="/admissao"><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Processo de Admissão</CardTitle><CardDescription>Campos obrigatórios são marcados com asterisco.</CardDescription></CardHeader>
        <CardContent><ProcessoAdmissaoForm onSaved={(processo) => router.push(`/admissao/${processo.id}`)} /></CardContent>
      </Card>
    </div>
  );
}
