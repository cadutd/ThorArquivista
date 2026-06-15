"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { Filter, Plus, Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MidiaForm } from "@/features/midias/midia-form";
import { MidiasTable } from "@/features/midias/midias-table";
import { listMidiasPage, listTiposMidiaAtivos, type MidiaFilters } from "@/lib/api/domain";

const DEFAULT_PAGE_SIZE = 20;

export default function MidiasPage() {
  const [open, setOpen] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<MidiaFilters>({});
  const [filters, setFilters] = useState<MidiaFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const tiposQuery = useQuery({
    queryKey: ["tipos-midia", "ativos"],
    queryFn: listTiposMidiaAtivos,
  });
  const query = useQuery({
    queryKey: ["midias", filters, pageIndex, pageSize],
    queryFn: () =>
      listMidiasPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });

  const total = query.data?.total ?? 0;
  const data = query.data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  function submitSearch(nextFilters = draftFilters) {
    setPageIndex(0);
    setFilters(cleanMidiaFilters(nextFilters));
  }

  function clearFilters() {
    setDraftFilters({});
    setPageIndex(0);
    setFilters({});
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Midias de Armazenamento</h1>
          <p className="text-sm text-muted-foreground">
            Repositorios, fitas, NAS e destinos cloud usados nas copias digitais.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" />
                Nova midia
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>Nova midia</DialogTitle>
                <DialogDescription>Cadastre um destino de armazenamento.</DialogDescription>
              </DialogHeader>
              <MidiaForm onCreated={() => setOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar midia"
            value={draftFilters.q ?? ""}
            onChange={(event) => setDraftFilters((current) => ({ ...current, q: event.target.value }))}
            onKeyDown={(event) => {
              if (event.key === "Enter") submitSearch();
            }}
          />
        </div>
        <Button type="button" onClick={() => submitSearch()}>
          <Search className="h-4 w-4" />
          Pesquisar
        </Button>
        <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}>
          <Filter className="h-4 w-4" />
          Busca por metadado
        </Button>
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={query.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPageIndex(0);
        }}
      />

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <SelectFilter
            label="Tipo"
            value={draftFilters.tipo_midia_id ?? ""}
            onChange={(tipo_midia_id) =>
              setDraftFilters((current) => ({ ...current, tipo_midia_id: tipo_midia_id || undefined }))
            }
          >
            <option value="">Todos</option>
            {(tiposQuery.data ?? []).map((tipo) => (
              <option key={tipo.id} value={tipo.id}>
                {tipo.nome}
              </option>
            ))}
          </SelectFilter>
          <SelectFilter
            label="Status"
            value={draftFilters.ativo === undefined ? "" : String(draftFilters.ativo)}
            onChange={(ativo) =>
              setDraftFilters((current) => ({ ...current, ativo: ativo === "" ? undefined : ativo === "true" }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativa</option>
            <option value="false">Inativa</option>
          </SelectFilter>
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => submitSearch()}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button type="button" variant="outline" onClick={clearFilters}>
              Limpar filtros
            </Button>
          </div>
        </div>
      ) : null}

      {query.error ? (
        <div className="rounded-md border p-6 text-sm text-destructive">{query.error.message}</div>
      ) : (
        <MidiasTable data={data} />
      )}

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={query.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPageIndex(0);
        }}
      />
    </div>
  );
}

function SelectFilter({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
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
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>
          Anterior
        </Button>
        {pages.map((page, index) =>
          page === "ellipsis" ? (
            <span key={`ellipsis-${index}`} className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground">
              ...
            </span>
          ) : (
            <Button key={page} type="button" variant={page === currentPage ? "default" : "outline"} size="sm" className="min-w-9 px-2" disabled={isLoading || page === currentPage} onClick={() => onPageChange(page - 1)}>
              {page}
            </Button>
          ),
        )}
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>
          Proxima
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>
          Ultima
        </Button>
        <Label htmlFor="midias-page-size" className="text-sm text-muted-foreground">
          Por pagina:
        </Label>
        <select
          id="midias-page-size"
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

function cleanMidiaFilters(filters: MidiaFilters): MidiaFilters {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ) as MidiaFilters;
}
