"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Clock } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { listEventos, listUnidades } from "@/lib/api/domain";

export default function EventosPage() {
  const unidades = useQuery({ queryKey: ["unidades"], queryFn: listUnidades });
  const [unidadeId, setUnidadeId] = useState<number | null>(null);
  const selectedId = unidadeId ?? unidades.data?.[0]?.id ?? null;
  const eventos = useQuery({
    queryKey: ["eventos", selectedId],
    queryFn: () => listEventos(selectedId as number),
    enabled: Boolean(selectedId),
  });

  const selectedUnidade = useMemo(
    () => unidades.data?.find((item) => item.id === selectedId),
    [selectedId, unidades.data],
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Eventos de Preservação</h1>
        <p className="text-sm text-muted-foreground">
          Linha do tempo de ingestão, fixidez, replicação e migração.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Unidade monitorada</CardTitle>
          <CardDescription>Selecione uma unidade para consultar seus eventos.</CardDescription>
        </CardHeader>
        <CardContent className="max-w-xl space-y-2">
          <Label>Unidade</Label>
          <select
            className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={selectedId ?? ""}
            onChange={(event) => setUnidadeId(Number(event.target.value))}
          >
            {(unidades.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.identificador} - {item.titulo}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Tabs defaultValue="timeline">
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="summary">Resumo</TabsTrigger>
        </TabsList>
        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <CardTitle>{selectedUnidade?.identificador ?? "Sem unidade selecionada"}</CardTitle>
              <CardDescription>
                {eventos.isLoading ? "Carregando eventos..." : `${eventos.data?.length ?? 0} eventos registrados`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {eventos.error ? (
                <p className="text-sm text-destructive">{eventos.error.message}</p>
              ) : (
                <div className="space-y-4">
                  {(eventos.data ?? []).map((evento) => (
                    <div key={evento.id} className="flex gap-4 rounded-md border p-4">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                        <Activity className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{evento.tipo_evento}</span>
                          <StatusBadge value={evento.resultado} />
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {evento.detalhe ?? "Sem detalhe registrado."}
                        </p>
                        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3.5 w-3.5" />
                          {evento.criado_em ?? "Data não informada"}
                        </div>
                      </div>
                    </div>
                  ))}
                  {!eventos.isLoading && !eventos.data?.length ? (
                    <p className="rounded-md border p-4 text-sm text-muted-foreground">
                      Nenhum evento registrado para a unidade selecionada.
                    </p>
                  ) : null}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="summary">
          <Card>
            <CardHeader>
              <CardTitle>Resumo de auditoria</CardTitle>
              <CardDescription>Consolidação inicial para operação.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-3">
              {["SUCESSO", "ALERTA", "FALHA"].map((status) => (
                <div key={status} className="rounded-md border p-4">
                  <StatusBadge value={status} />
                  <p className="mt-3 text-2xl font-semibold">
                    {(eventos.data ?? []).filter((item) => item.resultado === status).length}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
