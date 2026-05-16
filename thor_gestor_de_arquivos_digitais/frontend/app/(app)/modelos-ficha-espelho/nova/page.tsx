"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ModeloFichaForm } from "@/features/ficha-espelho/modelo-ficha-form";

export default function NovoModeloFichaPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Novo modelo de ficha</h1>
          <p className="text-sm text-muted-foreground">Defina dimensão, campos e formato de impressão.</p>
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
          <CardTitle>Criar</CardTitle>
          <CardDescription>Campos obrigatórios são marcados com asterisco.</CardDescription>
        </CardHeader>
        <CardContent>
          <ModeloFichaForm onSaved={() => router.push("/modelos-ficha-espelho")} />
        </CardContent>
      </Card>
    </div>
  );
}
