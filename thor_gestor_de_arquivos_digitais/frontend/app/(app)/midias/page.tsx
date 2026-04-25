"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { MidiaForm } from "@/features/midias/midia-form";
import { MidiasTable } from "@/features/midias/midias-table";
import { listMidias } from "@/lib/api/domain";

export default function MidiasPage() {
  const [open, setOpen] = useState(false);
  const query = useQuery({ queryKey: ["midias"], queryFn: listMidias });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Mídias de Armazenamento</h1>
          <p className="text-sm text-muted-foreground">
            Repositórios, fitas, NAS e destinos cloud usados nas cópias digitais.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4" />
              Nova mídia
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova mídia</DialogTitle>
              <DialogDescription>Cadastre um destino de armazenamento.</DialogDescription>
            </DialogHeader>
            <MidiaForm onCreated={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inventário de mídias</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${query.data?.length ?? 0} registros listados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <MidiasTable data={query.data ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
