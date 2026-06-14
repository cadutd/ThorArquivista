"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import Link from "next/link";
import { useMemo } from "react";
import { StatusBadge } from "@/components/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { MidiaArmazenamento } from "@/types/domain";

export function MidiasTable({ data }: { data: MidiaArmazenamento[] }) {
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
      { accessorKey: "tipo", header: "Tipo" },
      {
        accessorKey: "ativo",
        header: "Status",
        cell: ({ row }) => <StatusBadge value={row.original.ativo ? "ATIVA" : "INATIVA"} />,
      },
      {
        accessorKey: "descricao",
        header: "Descrição",
        cell: ({ row }) => row.original.descricao ?? "-",
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
              Nenhuma mídia cadastrada.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
