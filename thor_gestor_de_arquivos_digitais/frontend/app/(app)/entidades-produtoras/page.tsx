"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EntidadesProdutorasPage } from "@/features/entidades-produtoras/entidades-produtoras-page";
import { listEntidadesProdutorasPage } from "@/lib/api/entidades-produtoras";

export default function EntidadesProdutorasRoute() {
  const count = useQuery({
    queryKey: ["entidades-produtoras", "count"],
    queryFn: () => listEntidadesProdutorasPage({ limit: 1 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Entidades Produtoras</h1>
          <p className="text-sm text-muted-foreground">
            Cadastro de agentes produtores, acumuladores e mantenedores de documentos.
          </p>
        </div>
        <Button asChild className="!text-white hover:!text-white">
          <Link href="/entidades-produtoras/nova" className="!text-white">
            <Plus className="h-4 w-4" />
            Nova entidade produtora
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cadastro</CardTitle>
          <CardDescription>
            {count.isLoading ? "Carregando registros..." : `${count.data?.total ?? 0} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EntidadesProdutorasPage />
        </CardContent>
      </Card>
    </div>
  );
}
