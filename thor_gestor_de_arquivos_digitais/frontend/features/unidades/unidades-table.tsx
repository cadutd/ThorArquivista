"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { Edit, Eye, Filter, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { StatusBadge } from "@/components/status-badge";
import { deleteUnidade, type UnidadeFilters } from "@/lib/api/domain";
import type { CopiaDigital, UnidadeAcondicionamento } from "@/types/domain";

type Props = {
  data: UnidadeAcondicionamento[];
  filters: UnidadeFilters;
  onSearch: (filters: UnidadeFilters) => void;
  pageIndex: number;
  pageSize: number;
  total: number;
  isLoading: boolean;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

export function UnidadesTable({
  data,
  filters,
  onSearch,
  pageIndex,
  pageSize,
  total,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const queryClient = useQueryClient();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<UnidadeFilters>(filters);
  const [selected, setSelected] = useState<UnidadeAcondicionamento | null>(null);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  useEffect(() => {
    setDraftFilters(filters);
  }, [filters]);

  const deleteMutation = useMutation({
    mutationFn: deleteUnidade,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["unidades"] });
      setSelected(null);
    },
  });

  const columns = useMemo<ColumnDef<UnidadeAcondicionamento>[]>(
    () => [
      {
        accessorKey: "identificador",
        header: "Identificador",
        cell: ({ row }) => (
          <button
            className="font-medium text-primary hover:underline"
            onClick={() => setSelected(row.original)}
            type="button"
          >
            {row.original.identificador}
          </button>
        ),
      },
      { accessorKey: "titulo", header: "Título" },
      { accessorKey: "tipo_suporte", header: "Suporte" },
      { accessorKey: "tipo_unidade", header: "Tipo" },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusBadge value={row.original.status} />,
      },
      {
        accessorKey: "nivel_acesso",
        header: "Acesso",
        cell: ({ row }) => <StatusBadge value={row.original.nivel_acesso} />,
      },
      {
        id: "acoes",
        header: "",
        cell: ({ row }) => (
          <div className="flex justify-end gap-1">
            <Button
              aria-label="Visualizar unidade"
              size="icon"
              type="button"
              variant="ghost"
              onClick={() => setSelected(row.original)}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              asChild
              aria-label="Editar unidade"
              size="icon"
              variant="ghost"
            >
              <Link href={`/unidades/${row.original.id}/editar`}>
                <Edit className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        ),
      },
    ],
    [],
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
            placeholder="Buscar unidade"
            value={draftFilters.q ?? ""}
            onChange={(event) =>
              setDraftFilters({ ...draftFilters, q: event.target.value })
            }
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
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowAdvanced((value) => !value)}
        >
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
        isLoading={isLoading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Identificador">
            <Input
              value={draftFilters.identificador ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, identificador: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Título">
            <Input
              value={draftFilters.titulo ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, titulo: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Descrição">
            <Input
              value={draftFilters.descricao ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, descricao: event.target.value })
              }
            />
          </FilterField>
          <SelectFilter
            label="Suporte"
            value={draftFilters.tipo_suporte ?? ""}
            onChange={(value) => setDraftFilters({ ...draftFilters, tipo_suporte: value })}
          >
            <option value="">Todos</option>
            <option value="FISICO">Físico</option>
            <option value="DIGITAL">Digital</option>
            <option value="HIBRIDO">Híbrido</option>
          </SelectFilter>
          <SelectFilter
            label="Tipo"
            value={draftFilters.tipo_unidade ?? ""}
            onChange={(value) => setDraftFilters({ ...draftFilters, tipo_unidade: value })}
          >
            <option value="">Todos</option>
            <option value="CAIXA">Caixa</option>
            <option value="PASTA">Pasta</option>
            <option value="VOLUME">Volume</option>
            <option value="AIP">AIP</option>
            <option value="SIP">SIP</option>
            <option value="DIP">DIP</option>
          </SelectFilter>
          <SelectFilter
            label="Acesso"
            value={draftFilters.nivel_acesso ?? ""}
            onChange={(value) => setDraftFilters({ ...draftFilters, nivel_acesso: value })}
          >
            <option value="">Todos</option>
            <option value="PUBLICO">Público</option>
            <option value="RESTRITO">Restrito</option>
            <option value="CONFIDENCIAL">Confidencial</option>
          </SelectFilter>
          <SelectFilter
            label="Status"
            value={draftFilters.status ?? ""}
            onChange={(value) => setDraftFilters({ ...draftFilters, status: value })}
          >
            <option value="">Todos</option>
            <option value="ATIVA">Ativa</option>
            <option value="INATIVA">Inativa</option>
            <option value="TRANSFERIDA">Transferida</option>
            <option value="ELIMINADA">Eliminada</option>
          </SelectFilter>
          <DateRangeFilter
            label="Criação"
            from={draftFilters.criado_em_de}
            to={draftFilters.criado_em_ate}
            onChange={(from, to) =>
              setDraftFilters({
                ...draftFilters,
                criado_em_de: from,
                criado_em_ate: to,
              })
            }
          />
          <DateRangeFilter
            label="Atualização"
            from={draftFilters.atualizado_em_de}
            to={draftFilters.atualizado_em_ate}
            onChange={(from, to) =>
              setDraftFilters({
                ...draftFilters,
                atualizado_em_de: from,
                atualizado_em_ate: to,
              })
            }
          />
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

      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  Nenhuma unidade encontrada.
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

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Metadados da unidade</DialogTitle>
            <DialogDescription>
              Visualização completa dos campos registrados.
            </DialogDescription>
          </DialogHeader>
          {selected ? (
            <UnidadeDetails
              unidade={selected}
              onDelete={() => {
                if (window.confirm("Excluir esta unidade de acondicionamento?")) {
                  deleteMutation.mutate(selected.id);
                }
              }}
              isDeleting={deleteMutation.isPending}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function UnidadeDetails({
  unidade,
  onDelete,
  isDeleting,
}: {
  unidade: UnidadeAcondicionamento;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", unidade.id],
    ["Identificador", unidade.identificador],
    ["Título", unidade.titulo],
    ["Descrição", unidade.descricao || "-"],
    ["Suporte", unidade.tipo_suporte],
    ["Tipo", unidade.tipo_unidade],
    ["Nível de acesso", unidade.nivel_acesso],
    ["Status", unidade.status],
    ["Unidade pai", unidade.id_unidade_pai ?? "-"],
    ["Representa", unidade.id_representa ?? "-"],
    ["Criado em", formatDateTime(unidade.criado_em)],
    ["Atualizado em", formatDateTime(unidade.atualizado_em)],
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
            <div className="mt-1 text-sm">{value}</div>
          </div>
        ))}
      </div>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold">Metadados digitais</h3>
        {unidade.digital ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border p-3">
              <p className="text-xs font-medium uppercase text-muted-foreground">Tamanho</p>
              <div className="mt-1 text-sm">{unidade.digital.tamanho_bytes ?? "-"}</div>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs font-medium uppercase text-muted-foreground">Status de fixidez</p>
              <div className="mt-1 text-sm">{unidade.digital.status_fixidez ?? "-"}</div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhum metadado digital registrado.</p>
        )}
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold">Cópias digitais</h3>
        {unidade.copias_digitais?.length ? (
          <div className="space-y-2">
            {unidade.copias_digitais.map((copia) => (
              <CopiaDetails key={copia.id} copia={copia} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma cópia digital vinculada.</p>
        )}
      </section>

      <div className="flex justify-end gap-2">
        <Button asChild variant="outline">
          <Link href={`/unidades/${unidade.id}/editar`}>
            <Edit className="h-4 w-4" />
            Editar
          </Link>
        </Button>
        <Button
          type="button"
          variant="destructive"
          disabled={isDeleting}
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
          {isDeleting ? "Excluindo..." : "Excluir"}
        </Button>
      </div>
    </div>
  );
}

function CopiaDetails({ copia }: { copia: CopiaDigital }) {
  return (
    <div className="grid gap-2 rounded-md border p-3 text-sm md:grid-cols-2">
      <DetailLine label="Mídia" value={copia.id_midia_armazenamento} />
      <DetailLine label="URI" value={copia.uri_copia} />
      <DetailLine label="Função" value={copia.funcao_copia} />
      <DetailLine label="Status" value={copia.status_copia} />
      <DetailLine label="Algoritmo" value={copia.algoritmo_fixidez ?? "-"} />
      <DetailLine label="Hash" value={copia.hash_fixidez ?? "-"} />
      <DetailLine label="Última verificação" value={formatDateTime(copia.ultima_verificacao_em)} />
      <DetailLine label="Criada em" value={formatDateTime(copia.criada_em)} />
    </div>
  );
}

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <span className="text-muted-foreground">{label}: </span>
      <span>{value}</span>
    </div>
  );
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
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
  children: React.ReactNode;
}) {
  return (
    <FilterField label={label}>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
    </FilterField>
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
    <div className="flex flex-col gap-3 rounded-md border px-3 py-2">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <p className="text-sm text-muted-foreground">
          {displayedCount} registros de {total} | página {currentPage} de {totalPages}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isLoading || currentPage <= 1}
            onClick={() => onPageChange(0)}
          >
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
              <span
                key={`ellipsis-${index}`}
                className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground"
              >
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
            Próxima
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isLoading || currentPage >= totalPages}
            onClick={() => onPageChange(totalPages - 1)}
          >
            Última
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Label htmlFor="unidades-page-size" className="text-sm text-muted-foreground">
          Registros por página:
        </Label>
        <select
          id="unidades-page-size"
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
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  return sortedPages.flatMap((page, index) => {
    const previousPage = sortedPages[index - 1];

    if (previousPage && page - previousPage > 1) {
      return ["ellipsis" as const, page];
    }

    return [page];
  });
}

function DateRangeFilter({
  label,
  from,
  to,
  onChange,
}: {
  label: string;
  from?: string;
  to?: string;
  onChange: (from: string, to: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="grid gap-2 sm:grid-cols-2">
        <Input
          aria-label={`${label} de`}
          type="date"
          value={toDateInputValue(from)}
          onChange={(event) => onChange(startOfDay(event.target.value), to ?? "")}
        />
        <Input
          aria-label={`${label} até`}
          type="date"
          value={toDateInputValue(to)}
          onChange={(event) => onChange(from ?? "", endOfDay(event.target.value))}
        />
      </div>
    </div>
  );
}

function startOfDay(value: string) {
  return value ? `${value}T00:00:00` : "";
}

function endOfDay(value: string) {
  return value ? `${value}T23:59:59` : "";
}

function toDateInputValue(value?: string) {
  return value?.slice(0, 10) ?? "";
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}
