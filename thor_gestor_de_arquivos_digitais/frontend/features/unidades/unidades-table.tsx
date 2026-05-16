"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { Edit, Eye, Filter, Printer, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { listarModelosFichaEspelho } from "@/lib/api/ficha-espelho";
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
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [printIds, setPrintIds] = useState<number[]>([]);
  const [printDialogOpen, setPrintDialogOpen] = useState(false);
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

  const openPrintDialog = (ids: number[]) => {
    setPrintIds(ids);
    setPrintDialogOpen(true);
  };

  const columns = useMemo<ColumnDef<UnidadeAcondicionamento>[]>(
    () => [
      {
        id: "selecao",
        header: () => {
          const pageIds = data.map((item) => item.id);
          const allSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id));
          return (
            <input
              aria-label="Selecionar unidades da página"
              type="checkbox"
              checked={allSelected}
              onChange={(event) => {
                setSelectedIds((current) => {
                  const next = new Set(current);
                  pageIds.forEach((id) => {
                    if (event.target.checked) {
                      next.add(id);
                    } else {
                      next.delete(id);
                    }
                  });
                  return next;
                });
              }}
            />
          );
        },
        cell: ({ row }) => (
          <input
            aria-label={`Selecionar ${row.original.identificador}`}
            type="checkbox"
            checked={selectedIds.has(row.original.id)}
            onChange={(event) =>
              setSelectedIds((current) => {
                const next = new Set(current);
                if (event.target.checked) {
                  next.add(row.original.id);
                } else {
                  next.delete(row.original.id);
                }
                return next;
              })
            }
          />
        ),
      },
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
              aria-label="Imprimir ficha espelho"
              size="icon"
              type="button"
              variant="ghost"
              onClick={() => openPrintDialog([row.original.id])}
            >
              <Printer className="h-4 w-4" />
            </Button>
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
    [data, selectedIds],
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
        <Button
          type="button"
          variant="outline"
          disabled={!selectedIds.size}
          onClick={() => openPrintDialog(Array.from(selectedIds))}
        >
          <Printer className="h-4 w-4" />
          Imprimir fichas ({selectedIds.size})
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
          <FilterField label="Produtor">
            <Input
              value={draftFilters.produtor ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, produtor: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Unidade">
            <Input
              value={draftFilters.unidade ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, unidade: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Data-limite">
            <Input
              value={draftFilters.data_limite ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, data_limite: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Código de classificação">
            <Input
              value={draftFilters.codigo_classificacao ?? ""}
              onChange={(event) =>
                setDraftFilters({
                  ...draftFilters,
                  codigo_classificacao: event.target.value,
                })
              }
            />
          </FilterField>
          <FilterField label="Assunto">
            <Input
              value={draftFilters.assunto ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, assunto: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Código de barra">
            <Input
              value={draftFilters.codigo_barra ?? ""}
              onChange={(event) =>
                setDraftFilters({ ...draftFilters, codigo_barra: event.target.value })
              }
            />
          </FilterField>
          <FilterField label="Informações do pacote">
            <Input
              value={draftFilters.informacoes_pacote ?? ""}
              onChange={(event) =>
                setDraftFilters({
                  ...draftFilters,
                  informacoes_pacote: event.target.value,
                })
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
              onPrint={() => openPrintDialog([selected.id])}
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

      <PrintDialog
        open={printDialogOpen}
        unidadeIds={printIds}
        onOpenChange={setPrintDialogOpen}
      />
    </div>
  );
}

function UnidadeDetails({
  unidade,
  onDelete,
  onPrint,
  isDeleting,
}: {
  unidade: UnidadeAcondicionamento;
  onDelete: () => void;
  onPrint: () => void;
  isDeleting: boolean;
}) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", unidade.id],
    ["Identificador", unidade.identificador],
    ["Título", unidade.titulo],
    ["Descrição", unidade.descricao || "-"],
    ["Produtor", unidade.produtor || "-"],
    ["Unidade", unidade.unidade || "-"],
    ["Data-limite", unidade.data_limite || "-"],
    ["Código de classificação", unidade.codigo_classificacao || "-"],
    ["Assunto", unidade.assunto || "-"],
    ["Código de barra", unidade.codigo_barra || "-"],
    ["Informações do pacote", unidade.informacoes_pacote || "-"],
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
        <Button type="button" variant="outline" onClick={onPrint}>
          <Printer className="h-4 w-4" />
          Ficha espelho
        </Button>
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

function PrintDialog({
  open,
  unidadeIds,
  onOpenChange,
}: {
  open: boolean;
  unidadeIds: number[];
  onOpenChange: (open: boolean) => void;
}) {
  const [modeloId, setModeloId] = useState("");
  const modelos = useQuery({
    queryKey: ["fichas-espelho", "modelos", "ativos"],
    queryFn: () => listarModelosFichaEspelho({ ativo: true }),
    enabled: open,
  });
  const selectedModeloId = modeloId || (modelos.data?.items[0] ? String(modelos.data.items[0].id) : "");

  const print = () => {
    if (!selectedModeloId || !unidadeIds.length) {
      return;
    }
    const params = new URLSearchParams({
      modeloId: selectedModeloId,
      unidadeIds: unidadeIds.join(","),
    });
    window.open(`/fichas-espelho/imprimir?${params.toString()}`, "_blank", "noopener,noreferrer");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Gerar fichas espelho</DialogTitle>
          <DialogDescription>Escolha o modelo para imprimir {unidadeIds.length} unidade(s).</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Modelo</Label>
            <select
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              value={selectedModeloId}
              onChange={(event) => setModeloId(event.target.value)}
            >
              <option value="">Selecione</option>
              {(modelos.data?.items ?? []).map((modelo) => (
                <option key={modelo.id} value={modelo.id}>
                  {modelo.nome}
                </option>
              ))}
            </select>
          </div>
          {modelos.error ? <p className="text-sm text-destructive">{modelos.error.message}</p> : null}
          {!modelos.isLoading && !modelos.data?.items.length ? (
            <p className="text-sm text-muted-foreground">Cadastre um modelo ativo em Administração.</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="button" disabled={!selectedModeloId || !unidadeIds.length} onClick={print}>
              <Printer className="h-4 w-4" />
              Gerar para impressão
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
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
