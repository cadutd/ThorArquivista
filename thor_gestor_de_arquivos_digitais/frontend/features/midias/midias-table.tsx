"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Edit, Eye, Power } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { updateMidia } from "@/lib/api/domain";
import type { MidiaArmazenamento } from "@/types/domain";

export function MidiasTable({ data }: { data: MidiaArmazenamento[] }) {
  const queryClient = useQueryClient();
  const toggleMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) => updateMidia(id, { ativo }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["midias"] });
    },
  });

  const columns = useMemo<ColumnDef<MidiaArmazenamento>[]>(
    () => [
      {
        accessorKey: "nome",
        header: "Nome",
        cell: ({ row }) => (
          <Link href={`/midias/${row.original.id}`} className="font-medium text-primary hover:underline">
            {row.original.nome}
          </Link>
        ),
      },
      {
        accessorKey: "tipo_midia.nome",
        header: "Tipo",
        cell: ({ row }) => row.original.tipo_midia?.nome ?? "-",
      },
      {
        accessorKey: "data_validade",
        header: "Validade",
        cell: ({ row }) => formatDate(row.original.data_validade),
      },
      {
        accessorKey: "proxima_checagem_integridade",
        header: "Proxima checagem",
        cell: ({ row }) => formatDate(row.original.proxima_checagem_integridade),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusBadge value={row.original.status ?? (row.original.ativo ? "ATIVA" : "DESATIVADA")} />,
      },
      {
        accessorKey: "descricao",
        header: "Descricao",
        cell: ({ row }) => row.original.descricao ?? "-",
      },
      {
        id: "acoes",
        header: () => <span className="block text-right">Acoes</span>,
        cell: ({ row }) => {
          const midia = row.original;
          const toggleLabel = midia.ativo ? "Desativar midia" : "Ativar midia";

          return (
            <div className="flex justify-end gap-2">
              <Button asChild variant="outline" size="icon" title="Visualizar midia" aria-label="Visualizar midia">
                <Link href={`/midias/${midia.id}`}>
                  <Eye className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="icon" title="Editar midia" aria-label="Editar midia">
                <Link href={`/midias/${midia.id}/editar`}>
                  <Edit className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="icon"
                title={toggleLabel}
                aria-label={toggleLabel}
                disabled={toggleMutation.isPending}
                onClick={() => {
                  const acao = midia.ativo ? "desativar" : "ativar";
                  if (window.confirm(`Deseja ${acao} esta midia?`)) {
                    toggleMutation.mutate({ id: midia.id, ativo: !midia.ativo });
                  }
                }}
              >
                <Power className="h-4 w-4" />
              </Button>
            </div>
          );
        },
      },
    ],
    [toggleMutation],
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
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
                  <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                Nenhuma midia cadastrada.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(value));
}
