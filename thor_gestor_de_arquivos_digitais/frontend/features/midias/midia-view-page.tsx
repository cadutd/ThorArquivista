"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Edit } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { MidiaForm } from "@/features/midias/midia-form";
import { getMidia, listEventosMidia } from "@/lib/api/domain";
import type { EventoMidiaArmazenamento, MidiaArmazenamento } from "@/types/domain";

export function MidiaViewPage({ midiaId }: { midiaId: number }) {
  const query = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const eventosQuery = useQuery({
    queryKey: ["midias", midiaId, "eventos"],
    queryFn: () => listEventosMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const midia = query.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar midia</h1>
          <p className="text-sm text-muted-foreground">Consulta dos metadados da midia de armazenamento.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {midia ? (
            <Button asChild variant="outline">
              <Link href={`/midias/${midia.id}/editar`}>
                <Edit className="h-4 w-4" />
                Editar
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="outline">
            <Link href="/midias">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{midia?.nome ?? "Midia de armazenamento"}</CardTitle>
          <CardDescription>
            {query.isLoading
              ? "Carregando dados da midia."
              : midia
                ? midia.tipo_midia?.nome ?? "Tipo nao informado"
                : "Midia nao encontrada."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando midia...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : midia ? (
            <MidiaDetails midia={midia} />
          ) : (
            <p className="text-sm text-muted-foreground">Midia nao encontrada.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Eventos da midia</CardTitle>
          <CardDescription>Eventos de preservacao registrados diretamente sobre esta midia.</CardDescription>
        </CardHeader>
        <CardContent>
          {eventosQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando eventos...</p>
          ) : eventosQuery.error ? (
            <p className="text-sm text-destructive">{eventosQuery.error.message}</p>
          ) : (
            <EventosMidiaTable data={eventosQuery.data ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export function MidiaEditPage({ midiaId }: { midiaId: number }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar midia</h1>
          <p className="text-sm text-muted-foreground">Atualize os metadados da midia de armazenamento.</p>
        </div>
        <Button asChild variant="outline">
          <Link href={`/midias/${midiaId}`}>
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados da midia</CardTitle>
          <CardDescription>Campos obrigatorios sao validados antes do salvamento.</CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando midia...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <MidiaForm midia={query.data} onCreated={() => router.push(`/midias/${midiaId}`)} />
          ) : (
            <p className="text-sm text-muted-foreground">Midia nao encontrada.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MidiaDetails({ midia }: { midia: MidiaArmazenamento }) {
  const fields: Array<[string, ReactNode]> = [
    ["ID", midia.id],
    ["Nome", midia.nome],
    ["Tipo", midia.tipo_midia?.nome ?? "-"],
    ["Status", <StatusBadge key="status" value={midia.ativo ? "ATIVA" : "INATIVA"} />],
    ["Descricao", midia.descricao || "-"],
    ["Aquisicao", formatDate(midia.data_aquisicao)],
    ["Inicio de uso", formatDate(midia.data_inicio_uso)],
    ["Validade", formatDate(midia.data_validade)],
    ["Ultima checagem", formatDateTime(midia.ultima_checagem_integridade)],
    ["Proxima checagem", formatDateTime(midia.proxima_checagem_integridade)],
    ["Capacidade total", formatBytes(midia.capacidade_total_bytes)],
    ["Capacidade utilizada", formatBytes(midia.capacidade_utilizada_bytes)],
    ["Identificador fisico", midia.identificador_fisico || "-"],
    ["Posicao de armazenamento", midia.id_posicao_armazenamento ?? "-"],
    ["Criado em", formatDateTime(midia.criado_em)],
    ["Atualizado em", formatDateTime(midia.atualizado_em)],
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2">
      {fields.map(([label, value]) => (
        <div key={label} className="rounded-md border p-3">
          <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
          <div className="mt-1 text-sm">{value}</div>
        </div>
      ))}
    </section>
  );
}

function EventosMidiaTable({ data }: { data: EventoMidiaArmazenamento[] }) {
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Resultado</TableHead>
            <TableHead>Agente</TableHead>
            <TableHead>Correlacao</TableHead>
            <TableHead>Detalhe</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((evento) => (
              <TableRow key={evento.id}>
                <TableCell>{formatDateTime(evento.criado_em)}</TableCell>
                <TableCell>{evento.tipo_evento}</TableCell>
                <TableCell>
                  <StatusBadge value={evento.resultado} />
                </TableCell>
                <TableCell>{evento.agente || "-"}</TableCell>
                <TableCell>{evento.correlacao || "-"}</TableCell>
                <TableCell className="max-w-md">{evento.detalhe || "-"}</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                Nenhum evento encontrado para esta midia.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(value));
}

function formatBytes(value?: number | null) {
  if (value === undefined || value === null) return "-";
  return new Intl.NumberFormat("pt-BR").format(value);
}
