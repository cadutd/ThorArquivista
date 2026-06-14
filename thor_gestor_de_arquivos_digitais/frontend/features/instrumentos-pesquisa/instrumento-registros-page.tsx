"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Edit, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  deleteInstrumentoRegistro,
  getInstrumentoPesquisaSchema,
  listInstrumentoRegistros,
  searchInstrumentoRegistros,
} from "@/lib/api/domain";
import type { InstrumentoCampoSchema, InstrumentoRegistro, StatusInstrumentoRegistro } from "@/types/domain";

const PAGE_SIZE = 25;

export function InstrumentoRegistrosPage({ instrumentoId, readOnly = false }: { instrumentoId: string; readOnly?: boolean }) {
  const queryClient = useQueryClient();
  const [cursorStack, setCursorStack] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusInstrumentoRegistro | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const currentCursor = cursorStack.at(-1) ?? null;
  const isSearching = searchTerm.trim().length > 0;
  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });
  const registrosQuery = useQuery({
    queryKey: [
      "instrumentos-pesquisa",
      instrumentoId,
      "registros",
      { pageSize: PAGE_SIZE, cursor: currentCursor, status: statusFilter, q: searchTerm },
    ],
    queryFn: () => {
      if (isSearching) {
        return searchInstrumentoRegistros(instrumentoId, {
          q: searchTerm,
          pageSize: PAGE_SIZE,
          cursor: currentCursor,
        });
      }

      return listInstrumentoRegistros(instrumentoId, {
        pageSize: PAGE_SIZE,
        cursor: currentCursor,
        filters: statusFilter ? { status: statusFilter } : {},
      });
    },
  });
  const remove = useMutation({
    mutationFn: (registroId: string) => deleteInstrumentoRegistro(instrumentoId, registroId),
    onSuccess: async () => {
      setCursorStack([]);
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa", instrumentoId, "registros"] });
    },
  });

  if (schemaQuery.isLoading || registrosQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando registros...</p>;
  }

  if (schemaQuery.error) {
    return <p className="text-sm text-destructive">{schemaQuery.error.message}</p>;
  }

  if (registrosQuery.error) {
    return <p className="text-sm text-destructive">{registrosQuery.error.message}</p>;
  }

  const schema = schemaQuery.data;
  const registroPage = registrosQuery.data;
  const registros = registroPage?.items ?? [];
  if (!schema) {
    return <p className="text-sm text-muted-foreground">Schema não encontrado.</p>;
  }
  const columns = schema.campos.filter((campo) => campo.aparece_listagem);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">{schema.instrumento.nome}</h1>
          <p className="text-sm text-muted-foreground">
            {readOnly ? "Registros dinâmicos disponíveis para pesquisa." : "Registros dinâmicos cadastrados para este instrumento."}
          </p>
        </div>
        {!readOnly ? (
          <Button asChild>
            <Link href={`/instrumentos-pesquisa/${instrumentoId}/registros/novo`}>
              <Plus className="h-4 w-4" />
              Novo registro
            </Link>
          </Button>
        ) : null}
      </div>
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>Registros</CardTitle>
              <CardDescription>
                {registros.length} registros nesta página, conforme campos marcados para listagem.
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              <form
                className="flex w-full gap-2 sm:w-auto"
                onSubmit={(event) => {
                  event.preventDefault();
                  setCursorStack([]);
                  setSearchTerm(searchInput.trim());
                }}
              >
                <Input
                  value={searchInput}
                  placeholder="Buscar registros"
                  className="h-9 sm:w-64"
                  onChange={(event) => setSearchInput(event.target.value)}
                />
                <Button type="submit" size="sm">
                  Buscar
                </Button>
                {isSearching ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCursorStack([]);
                      setSearchInput("");
                      setSearchTerm("");
                    }}
                  >
                    Limpar
                  </Button>
                ) : null}
              </form>
              <label className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Status</span>
              <select
                className="h-9 rounded-md border bg-background px-3 text-sm"
                value={statusFilter}
                disabled={isSearching}
                onChange={(event) => {
                  setCursorStack([]);
                  setStatusFilter(event.target.value as StatusInstrumentoRegistro | "");
                }}
              >
                <option value="">Ativos e inativos</option>
                <option value="ATIVO">Ativo</option>
                <option value="INATIVO">Inativo</option>
                <option value="EXCLUIDO">Excluido</option>
              </select>
              </label>
            </div>
          </div>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((campo) => (
                  <TableHead key={campo.id}>{campo.nome}</TableHead>
                ))}
                <TableHead>Status</TableHead>
                <TableHead>Atualizado em</TableHead>
                {!readOnly ? <TableHead className="text-right">Ações</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {registros.map((registro) => (
                <RegistroRow
                  key={registro.id}
                  instrumentoId={instrumentoId}
                  registro={registro}
                  columns={columns}
                  readOnly={readOnly}
                  isDeleting={remove.isPending}
                  onDelete={() => {
                    if (window.confirm("Excluir logicamente este registro?")) {
                      remove.mutate(registro.id);
                    }
                  }}
                />
              ))}
              {!registros.length ? (
                <TableRow>
                  <TableCell colSpan={columns.length + (readOnly ? 2 : 3)} className="h-24 text-center text-muted-foreground">
                    Nenhum registro encontrado.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
        <div className="flex items-center justify-between border-t px-6 py-4 text-sm text-muted-foreground">
          <span>Página {cursorStack.length + 1}</span>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!cursorStack.length || registrosQuery.isFetching}
              onClick={() => setCursorStack((stack) => stack.slice(0, -1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!registroPage?.has_more || !registroPage.next_cursor || registrosQuery.isFetching}
              onClick={() => {
                if (registroPage?.next_cursor) {
                  setCursorStack((stack) => [...stack, registroPage.next_cursor as string]);
                }
              }}
            >
              Próxima
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function RegistroRow({
  instrumentoId,
  registro,
  columns,
  readOnly,
  isDeleting,
  onDelete,
}: {
  instrumentoId: string;
  registro: InstrumentoRegistro;
  columns: InstrumentoCampoSchema[];
  readOnly: boolean;
  isDeleting: boolean;
  onDelete: () => void;
}) {
  return (
    <TableRow>
      {columns.map((campo) => (
        <TableCell key={campo.id}>{formatCampoValue(campo, registro.dados[campo.chave])}</TableCell>
      ))}
      <TableCell>{registro.status}</TableCell>
      <TableCell>{formatDateTime(registro.atualizado_em)}</TableCell>
      {!readOnly ? (
        <TableCell>
          <div className="flex justify-end gap-1">
            <Button asChild variant="ghost" size="icon" title="Editar registro">
              <Link href={`/instrumentos-pesquisa/${instrumentoId}/registros/${registro.id}/editar`}>
                <Edit className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon" title="Excluir registro" disabled={isDeleting} onClick={onDelete}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </TableCell>
      ) : null}
    </TableRow>
  );
}

function formatValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  const reference = referenceFrom(value);
  if (reference) return reference.rotulo;
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function formatCampoValue(campo: InstrumentoCampoSchema, value: unknown) {
  if (campo.tipo === "UNIDADE_ACONDICIONAMENTO") {
    const reference = referenceFrom(value);
    return reference ? (
      <Link href={`/unidades/${reference.id}`} className="font-medium text-primary hover:underline">
        {reference.rotulo}
      </Link>
    ) : formatValue(value);
  }

  if (campo.tipo === "MIDIA_ARMAZENAMENTO") {
    const reference = referenceFrom(value);
    return reference ? (
      <Link href={`/midias/${reference.id}`} className="font-medium text-primary hover:underline">
        {reference.rotulo}
      </Link>
    ) : formatValue(value);
  }

  return formatValue(value);
}

function referenceFrom(value: unknown): { id: number; rotulo: string } | null {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    const id = Number(record.id);
    const rotulo = String(record.rotulo ?? record.label ?? record.nome ?? record.identificador ?? id);
    if (Number.isFinite(id) && id > 0 && rotulo) return { id, rotulo };
  }
  const id = Number(value);
  if (Number.isFinite(id) && id > 0) return { id, rotulo: String(id) };
  return null;
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
