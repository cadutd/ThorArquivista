"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { UnidadeForm } from "@/features/unidades/unidade-form";
import { UnidadesTable } from "@/features/unidades/unidades-table";
import { listUnidades } from "@/lib/api/domain";

export default function UnidadesPage() {
  const [open, setOpen] = useState(false);
  const query = useQuery({ queryKey: ["unidades"], queryFn: listUnidades });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Unidades de Acondicionamento</h1>
          <p className="text-sm text-muted-foreground">
            Cadastro, busca e acompanhamento das unidades físicas e digitais.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4" />
              Nova unidade
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Nova unidade</DialogTitle>
              <DialogDescription>Informe os metadados principais.</DialogDescription>
            </DialogHeader>
            <UnidadeForm onCreated={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Acervo</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${query.data?.length ?? 0} registros listados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <UnidadesTable data={query.data ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
