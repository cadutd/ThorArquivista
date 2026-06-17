"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getResumoIntegridadeMidias, listItensIntegridadeMidias } from "@/lib/api/domain";
import type { CategoriaIntegridadeMidia, MidiaArmazenamento } from "@/types/domain";

const DEFAULT_PAGE_SIZE = 20;

const grupos: Array<{
  key: CategoriaIntegridadeMidia;
  title: string;
  description: string;
}> = [
  {
    key: "validade_vencida",
    title: "Validade vencida",
    description: "Midias que ja passaram da data de validade.",
  },
  {
    key: "checagem_vencida",
    title: "Checagem vencida",
    description: "Midias com verificacao de integridade pendente.",
  },
  {
    key: "proximas_vencimento",
    title: "Proximas do vencimento",
    description: "Validade prevista para os proximos 90 dias.",
  },
  {
    key: "falha_ultima_checagem",
    title: "Falha na ultima checagem",
    description: "Midias com falha de integridade registrada.",
  },
  {
    key: "sem_checagem",
    title: "Sem checagem registrada",
    description: "Midias sem historico ou agenda de verificacao.",
  },
  {
    key: "com_alerta",
    title: "Com alerta",
    description: "Midias marcadas com alerta ou expiradas.",
  },
];

export function MidiaIntegridadePage() {
  const [selected, setSelected] = useState<CategoriaIntegridadeMidia>("checagem_vencida");
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const resumoQuery = useQuery({
    queryKey: ["midias", "integridade", "resumo"],
    queryFn: getResumoIntegridadeMidias,
  });

  const itensQuery = useQuery({
    queryKey: ["midias", "integridade", "itens", selected, pageIndex, pageSize],
    queryFn: () =>
      listItensIntegridadeMidias({
        categoria: selected,
        limit: pageSize,
        offset: pageIndex * pageSize,
      }),
  });

  const activeGroup = grupos.find((grupo) => grupo.key === selected) ?? grupos[0];
  const total = itensQuery.data?.total ?? 0;
  const data = itensQuery.data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  function selectGroup(key: CategoriaIntegridadeMidia) {
    setSelected(key);
    setPageIndex(0);
  }

  return (
    <div className="space-y-6">
      <div>
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Painel de Integridade</h1>
          <p className="text-sm text-muted-foreground">
            Acompanhamento de validade, checagens e alertas das midias de armazenamento.
          </p>
        </div>
      </div>

      {resumoQuery.error ? <p className="text-sm text-destructive">{resumoQuery.error.message}</p> : null}
      {itensQuery.error ? <p className="text-sm text-destructive">{itensQuery.error.message}</p> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {grupos.map((grupo) => {
          const count = resumoQuery.data?.[grupo.key] ?? 0;
          const active = grupo.key === selected;

          return (
            <button
              key={grupo.key}
              type="button"
              className={`rounded-md border bg-card p-4 text-left transition-colors hover:bg-muted/60 ${
                active ? "border-primary ring-1 ring-primary" : ""
              }`}
              onClick={() => selectGroup(grupo.key)}
            >
              <span className="block text-sm font-medium text-muted-foreground">{grupo.title}</span>
              <span className="mt-2 block text-3xl font-semibold tracking-normal">
                {resumoQuery.isLoading ? "..." : count}
              </span>
              <span className="mt-1 block text-xs text-muted-foreground">{grupo.description}</span>
            </button>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle className="text-lg">{activeGroup.title}</CardTitle>
            <CardDescription>
              {itensQuery.isFetching ? "Carregando registros..." : `${total} midias encontradas`}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            displayedCount={data.length}
            total={total}
            isLoading={itensQuery.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(nextPageSize) => {
              setPageSize(nextPageSize);
              setPageIndex(0);
            }}
          />
          <MidiasIntegridadeTable data={data} categoria={selected} />
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            displayedCount={data.length}
            total={total}
            isLoading={itensQuery.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(nextPageSize) => {
              setPageSize(nextPageSize);
              setPageIndex(0);
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function MidiasIntegridadeTable({
  data,
  categoria,
}: {
  data: MidiaArmazenamento[];
  categoria: CategoriaIntegridadeMidia;
}) {
  return (
    <div className="overflow-auto rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Midia</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Data de referencia</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((midia) => (
              <TableRow key={midia.id}>
                <TableCell className="font-medium">{midia.nome}</TableCell>
                <TableCell>{midia.tipo_midia?.nome ?? "-"}</TableCell>
                <TableCell>
                  <StatusBadge value={midia.status} />
                </TableCell>
                <TableCell className="whitespace-nowrap">{formatReferenceDate(midia, categoria)}</TableCell>
                <TableCell className="text-right">
                  <Button asChild variant="outline" size="icon" title="Visualizar midia" aria-label="Visualizar midia">
                    <Link href={`/midias/${midia.id}`}>
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                Nenhuma midia encontrada para esta categoria.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function PaginationControls({
  currentPage,
  totalPages,
  pageSize,
  displayedCount,
  total,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  displayedCount: number;
  total: number;
  isLoading: boolean;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}) {
  const pages = getPaginationItems(currentPage, totalPages);

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2">
      <p className="whitespace-nowrap text-sm text-muted-foreground">
        {displayedCount} registros de {total} | pagina {currentPage} de {totalPages}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>
          Primeira
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isLoading || currentPage <= 1}
          onClick={() => onPageChange(currentPage - 2)}
        >
          Anterior
        </Button>
        {pages.map((page, index) =>
          page === "ellipsis" ? (
            <span key={`ellipsis-${index}`} className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground">
              ...
            </span>
          ) : (
            <Button
              key={page}
              type="button"
              variant={page === currentPage ? "default" : "outline"}
              size="sm"
              className="min-w-9 px-2"
              disabled={isLoading || page === currentPage}
              onClick={() => onPageChange(page - 1)}
            >
              {page}
            </Button>
          ),
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isLoading || currentPage >= totalPages}
          onClick={() => onPageChange(currentPage)}
        >
          Proxima
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isLoading || currentPage >= totalPages}
          onClick={() => onPageChange(totalPages - 1)}
        >
          Ultima
        </Button>
        <label htmlFor="integridade-page-size" className="text-sm text-muted-foreground">
          Por pagina:
        </label>
        <select
          id="integridade-page-size"
          className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}

function getPaginationItems(currentPage: number, totalPages: number) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  return sortedPages.flatMap((page, index) => {
    const previousPage = sortedPages[index - 1];
    if (previousPage && page - previousPage > 1) return ["ellipsis" as const, page];
    return [page];
  });
}

function formatReferenceDate(midia: MidiaArmazenamento, categoria: CategoriaIntegridadeMidia) {
  if (categoria === "validade_vencida" || categoria === "proximas_vencimento") {
    return formatDate(midia.data_validade);
  }
  if (categoria === "checagem_vencida" || categoria === "sem_checagem") {
    return formatDateTime(midia.proxima_checagem_integridade);
  }
  return formatDateTime(midia.ultima_checagem_integridade ?? midia.atualizado_em);
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(value));
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
