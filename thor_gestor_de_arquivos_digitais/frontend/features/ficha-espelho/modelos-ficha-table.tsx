"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { Edit, Filter, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { excluirModeloFichaEspelho } from "@/lib/api/ficha-espelho";
import type { ModeloFichaEspelho } from "@/types/ficha-espelho";

export type ModeloFichaFilters = Partial<{
  q: string;
  ativo: boolean | "";
}>;

export function ModelosFichaTable({
  data,
  filters,
  onSearch,
  pageIndex,
  pageSize,
  total,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: {
  data: ModeloFichaEspelho[];
  filters: ModeloFichaFilters;
  onSearch: (filters: ModeloFichaFilters) => void;
  pageIndex: number;
  pageSize: number;
  total: number;
  isLoading: boolean;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}) {
  const queryClient = useQueryClient();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<ModeloFichaFilters>(filters);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  const deleteMutation = useMutation({
    mutationFn: excluirModeloFichaEspelho,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["fichas-espelho", "modelos"] });
    },
  });

  const columns = useMemo<ColumnDef<ModeloFichaEspelho>[]>(
    () => [
      {
        accessorKey: "nome",
        header: "Nome",
        cell: ({ row }) => <span className="font-medium">{row.original.nome}</span>,
      },
      {
        id: "dimensoes",
        header: "Dimensão",
        cell: ({ row }) => `${row.original.largura_cm} x ${row.original.altura_cm} cm`,
      },
      { accessorKey: "tamanho_papel", header: "Papel" },
      { accessorKey: "orientacao", header: "Orientação" },
      {
        accessorKey: "colunas",
        header: "Colunas",
      },
      {
        accessorKey: "ativo",
        header: "Status",
        cell: ({ row }) => (row.original.ativo ? "Ativo" : "Inativo"),
      },
      {
        id: "acoes",
        header: "",
        cell: ({ row }) => (
          <div className="flex justify-end gap-1">
            <Button asChild aria-label="Editar modelo" size="icon" variant="ghost">
              <Link href={`/modelos-ficha-espelho/${row.original.id}/editar`}>
                <Edit className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              aria-label="Excluir modelo"
              size="icon"
              type="button"
              variant="ghost"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (window.confirm("Excluir este modelo de ficha espelho?")) {
                  deleteMutation.mutate(row.original.id);
                }
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteMutation],
  );

  // TanStack Table currently opts this hook out of React Compiler memoization.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar modelo"
            value={draftFilters.q ?? ""}
            onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearch(draftFilters);
              }
            }}
          />
        </div>
        <Button type="button" onClick={() => onSearch(draftFilters)}>
          <Search className="h-4 w-4" />
          Pesquisar
        </Button>
        <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}>
          <Filter className="h-4 w-4" />
          Filtros
        </Button>
      </div>

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-3">
          <FilterField label="Status">
            <select
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              value={draftFilters.ativo === "" || draftFilters.ativo === undefined ? "" : String(draftFilters.ativo)}
              onChange={(event) =>
                setDraftFilters({
                  ...draftFilters,
                  ativo: event.target.value === "" ? "" : event.target.value === "true",
                })
              }
            >
              <option value="">Todos</option>
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </FilterField>
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => onSearch(draftFilters)}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDraftFilters({});
                onSearch({});
              }}
            >
              Limpar filtros
            </Button>
          </div>
        </div>
      ) : null}

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={isLoading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  Nenhum modelo encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={data.length}
        total={total}
        isLoading={isLoading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </div>
  );
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
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
  return (
    <div className="flex flex-col gap-3 rounded-md border px-3 py-2 lg:flex-row lg:items-center lg:justify-between">
      <p className="text-sm text-muted-foreground">
        {displayedCount} registros de {total} | página {currentPage} de {totalPages}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>
          Primeira
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>
          Anterior
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>
          Próxima
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>
          Última
        </Button>
        <select
          className="h-9 rounded-md border bg-background px-2 text-sm"
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
