"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ClipboardList, Edit, FileInput, Filter, Loader2, Plus, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  createInstrumentoCampo,
  createInstrumentoPesquisa,
  deleteInstrumentoCampo,
  deleteInstrumentoPesquisa,
  listInstrumentoCampos,
  listInstrumentosPesquisa,
  reorderInstrumentoCampos,
  updateInstrumentoCampo,
  updateInstrumentoPesquisa,
  type InstrumentoCampoPayload,
  type InstrumentoPesquisaFilters,
  type InstrumentoPesquisaPayload,
} from "@/lib/api/domain";
import type {
  InstrumentoCampo,
  InstrumentoPesquisa,
  StatusInstrumentoPesquisa,
  TipoCampoInstrumento,
  TipoInstrumentoPesquisa,
  VisibilidadeInstrumentoPesquisa,
} from "@/types/domain";

const tipoOptions: Array<[TipoInstrumentoPesquisa, string]> = [
  ["GUIA", "Guia"],
  ["INVENTARIO", "Inventário"],
  ["CATALOGO", "Catálogo"],
  ["INDICE", "Índice"],
  ["BASE_TEMATICA", "Base temática"],
  ["EXPOSICAO", "Exposição"],
  ["OUTRO", "Outro"],
];

const statusOptions: Array<[StatusInstrumentoPesquisa, string]> = [
  ["RASCUNHO", "Rascunho"],
  ["PUBLICADO", "Publicado"],
  ["ARQUIVADO", "Arquivado"],
];

const visibilidadeOptions: Array<[VisibilidadeInstrumentoPesquisa, string]> = [
  ["INTERNO", "Interno"],
  ["PUBLICO", "Público"],
  ["RESTRITO", "Restrito"],
];

const campoTipoOptions: Array<[TipoCampoInstrumento, string]> = [
  ["TEXTO_CURTO", "Texto curto"],
  ["TEXTO_LONGO", "Texto longo"],
  ["NUMERO", "Número"],
  ["DATA", "Data"],
  ["PERIODO", "Período"],
  ["BOOLEANO", "Booleano"],
  ["LISTA_SIMPLES", "Lista simples"],
  ["LISTA_MULTIPLA", "Lista múltipla"],
  ["VOCABULARIO", "Vocabulário"],
  ["UNIDADE_ACONDICIONAMENTO", "Unidade de acondicionamento"],
  ["REGISTRO_DESCRITIVO", "Registro descritivo"],
  ["URL", "URL"],
  ["ARQUIVO", "Arquivo"],
  ["IMAGEM", "Imagem"],
  ["CAMPO_CALCULADO", "Campo calculado"],
];

const DEFAULT_PAGE_SIZE = 20;

export function InstrumentosPesquisaPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<InstrumentoPesquisa | null>(null);
  const [deleting, setDeleting] = useState<InstrumentoPesquisa | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<InstrumentoPesquisaFilters>({});
  const [filters, setFilters] = useState<InstrumentoPesquisaFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const query = useQuery({
    queryKey: ["instrumentos-pesquisa", filters, pageIndex, pageSize],
    queryFn: () =>
      listInstrumentosPesquisa({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });

  const mutation = useMutation({
    mutationFn: (payload: InstrumentoPesquisaPayload) =>
      editing ? updateInstrumentoPesquisa(editing.id, payload) : createInstrumentoPesquisa(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa"] });
      setOpen(false);
      setEditing(null);
    },
  });

  const remove = useMutation({
    mutationFn: (instrumento: InstrumentoPesquisa) => deleteInstrumentoPesquisa(instrumento.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa"] });
      setDeleting(null);
    },
  });

  const total = query.data?.total ?? 0;
  const data = query.data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  function submitSearch(nextFilters = draftFilters) {
    setPageIndex(0);
    setFilters(cleanInstrumentoFilters(nextFilters));
  }

  function clearFilters() {
    setDraftFilters({});
    setPageIndex(0);
    setFilters({});
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Instrumentos de Pesquisa</h1>
          <p className="text-sm text-muted-foreground">
            Cadastro de guias, inventários, catálogos, índices e bases temáticas.
          </p>
        </div>
        <Button
          onClick={() => {
            mutation.reset();
            setEditing(null);
            setOpen(true);
          }}
        >
          <Plus className="h-4 w-4" />
          Novo instrumento
        </Button>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar instrumento"
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
        <SelectField
          label="Tipo"
          value={draftFilters.tipo ?? ""}
          options={tipoOptions}
          includeEmpty
          onChange={(tipo) => setDraftFilters((current) => ({ ...current, tipo: tipo ? tipo as TipoInstrumentoPesquisa : undefined }))}
        />
        <SelectField
          label="Status"
          value={draftFilters.status ?? ""}
          options={statusOptions}
          includeEmpty
          onChange={(status) => setDraftFilters((current) => ({ ...current, status: status ? status as StatusInstrumentoPesquisa : undefined }))}
        />
        <SelectField
          label="Visibilidade"
          value={draftFilters.visibilidade ?? ""}
          options={visibilidadeOptions}
          includeEmpty
          onChange={(visibilidade) => setDraftFilters((current) => ({ ...current, visibilidade: visibilidade ? visibilidade as VisibilidadeInstrumentoPesquisa : undefined }))}
        />
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

      <div className="overflow-hidden rounded-md border">
          {query.error ? (
            <p className="p-6 text-sm text-destructive">{query.error.message}</p>
          ) : (
            <InstrumentosTable
              data={data}
              onEdit={(instrumento) => {
                mutation.reset();
                setEditing(instrumento);
                setOpen(true);
              }}
              onDelete={(instrumento) => {
                remove.reset();
                setDeleting(instrumento);
              }}
            />
          )}
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

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[90vh] max-w-5xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? "Editar instrumento" : "Novo instrumento"}</DialogTitle>
            <DialogDescription>Informe os metadados básicos do instrumento de pesquisa.</DialogDescription>
          </DialogHeader>
          {editing ? (
            <Tabs defaultValue="dados">
              <TabsList>
                <TabsTrigger value="dados">Dados</TabsTrigger>
                <TabsTrigger value="campos">Campos do Instrumento</TabsTrigger>
              </TabsList>
              <TabsContent value="dados">
                <InstrumentoForm
                  key={editing.id}
                  instrumento={editing}
                  isSaving={mutation.isPending}
                  error={mutation.error?.message}
                  onSubmit={(payload) => mutation.mutate(payload)}
                />
              </TabsContent>
              <TabsContent value="campos">
                <CamposInstrumentoPanel instrumento={editing} />
              </TabsContent>
            </Tabs>
          ) : (
            <InstrumentoForm
              instrumento={editing}
              isSaving={mutation.isPending}
              error={mutation.error?.message}
              onSubmit={(payload) => mutation.mutate(payload)}
            />
          )}
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(deleting)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !remove.isPending) setDeleting(null);
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{remove.isPending ? "Excluindo instrumento" : "Confirmar exclusão"}</DialogTitle>
            <DialogDescription>Esta ação excluirá permanentemente o instrumento de pesquisa.</DialogDescription>
          </DialogHeader>
          {deleting ? (
            <div className="rounded-md border p-3 text-sm">
              <p className="font-medium">{deleting.nome}</p>
              <p className="text-muted-foreground">{labelFor(tipoOptions, deleting.tipo)}</p>
            </div>
          ) : null}
          {remove.error ? <p className="text-sm text-destructive">{remove.error.message}</p> : null}
          <div className="flex justify-end gap-2">
            <Button variant="outline" disabled={remove.isPending} onClick={() => setDeleting(null)}>
              Cancelar
            </Button>
            <Button variant="destructive" disabled={remove.isPending} onClick={() => deleting && remove.mutate(deleting)}>
              {remove.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Excluir
            </Button>
          </div>
        </DialogContent>
      </Dialog>
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
    <div className="flex flex-col gap-3 rounded-md border px-3 py-2">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <p className="text-sm text-muted-foreground">
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
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Label htmlFor="instrumentos-page-size" className="text-sm text-muted-foreground">
          Registros por pagina:
        </Label>
        <select
          id="instrumentos-page-size"
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

function cleanInstrumentoFilters(filters: InstrumentoPesquisaFilters): InstrumentoPesquisaFilters {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ) as InstrumentoPesquisaFilters;
}

function InstrumentosTable({
  data,
  onEdit,
  onDelete,
}: {
  data: InstrumentoPesquisa[];
  onEdit: (instrumento: InstrumentoPesquisa) => void;
  onDelete: (instrumento: InstrumentoPesquisa) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Visibilidade</TableHead>
          <TableHead>Responsável</TableHead>
          <TableHead>Atualizado em</TableHead>
          <TableHead className="text-right">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((instrumento) => (
          <TableRow key={instrumento.id}>
            <TableCell className="font-medium">{instrumento.nome}</TableCell>
            <TableCell>{labelFor(tipoOptions, instrumento.tipo)}</TableCell>
            <TableCell>
              <StatusPill value={instrumento.status} />
            </TableCell>
            <TableCell>{labelFor(visibilidadeOptions, instrumento.visibilidade)}</TableCell>
            <TableCell>{instrumento.responsavel || "-"}</TableCell>
            <TableCell>{formatDateTime(instrumento.atualizado_em)}</TableCell>
            <TableCell>
              <div className="flex justify-end gap-1">
                <Button variant="ghost" size="icon" title="Editar instrumento" onClick={() => onEdit(instrumento)}>
                  <Edit className="h-4 w-4" />
                </Button>
                <Button asChild variant="ghost" size="icon" title="Cadastro dinâmico">
                  <Link href={`/instrumentos-pesquisa/${instrumento.id}/cadastro`}>
                    <FileInput className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="ghost" size="icon" title="Listagem dinâmica de registros">
                  <Link href={`/instrumentos-pesquisa/${instrumento.id}/registros`}>
                    <ClipboardList className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="ghost" size="icon" title="Busca avançada">
                  <Link href={`/instrumentos-pesquisa/${instrumento.id}/busca-avancada`}>
                    <Search className="h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="ghost" size="icon" title="Excluir instrumento" onClick={() => onDelete(instrumento)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
        {!data.length ? (
          <TableRow>
            <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
              Nenhum instrumento cadastrado.
            </TableCell>
          </TableRow>
        ) : null}
      </TableBody>
    </Table>
  );
}

function InstrumentoForm({
  instrumento,
  isSaving,
  error,
  onSubmit,
}: {
  instrumento: InstrumentoPesquisa | null;
  isSaving: boolean;
  error?: string;
  onSubmit: (payload: InstrumentoPesquisaPayload) => void;
}) {
  const [values, setValues] = useState<InstrumentoPesquisaPayload>({
    nome: instrumento?.nome ?? "",
    tipo: instrumento?.tipo ?? "GUIA",
    descricao: instrumento?.descricao ?? "",
    status: instrumento?.status ?? "RASCUNHO",
    visibilidade: instrumento?.visibilidade ?? "INTERNO",
    responsavel: instrumento?.responsavel ?? "",
  });

  return (
    <form
      className="grid gap-4 sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit({
          ...values,
          nome: values.nome.trim(),
          descricao: optionalText(values.descricao),
          responsavel: optionalText(values.responsavel),
        });
      }}
    >
      <Field label="Nome" required>
        <Input value={values.nome} maxLength={255} required onChange={(event) => setValues({ ...values, nome: event.target.value })} />
      </Field>
      <SelectField
        label="Tipo"
        value={values.tipo}
        options={tipoOptions}
        required
        onChange={(tipo) => setValues({ ...values, tipo: tipo as TipoInstrumentoPesquisa })}
      />
      <SelectField
        label="Status"
        value={values.status}
        options={statusOptions}
        required
        onChange={(status) => setValues({ ...values, status: status as StatusInstrumentoPesquisa })}
      />
      <SelectField
        label="Visibilidade"
        value={values.visibilidade}
        options={visibilidadeOptions}
        required
        onChange={(visibilidade) => setValues({ ...values, visibilidade: visibilidade as VisibilidadeInstrumentoPesquisa })}
      />
      <Field label="Responsável">
        <Input value={values.responsavel ?? ""} maxLength={255} onChange={(event) => setValues({ ...values, responsavel: event.target.value })} />
      </Field>
      <Field label="Descrição" className="sm:col-span-2">
        <textarea
          className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={values.descricao ?? ""}
          onChange={(event) => setValues({ ...values, descricao: event.target.value })}
        />
      </Field>
      {error ? <p className="text-sm text-destructive sm:col-span-2">{error}</p> : null}
      <div className="sm:col-span-2">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? "Salvando..." : "Salvar instrumento"}
        </Button>
      </div>
    </form>
  );
}

function CamposInstrumentoPanel({ instrumento }: { instrumento: InstrumentoPesquisa }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<InstrumentoCampo | null>(null);
  const camposQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumento.id, "campos"],
    queryFn: () => listInstrumentoCampos(instrumento.id),
  });
  const campos = camposQuery.data ?? [];

  const mutation = useMutation({
    mutationFn: (payload: InstrumentoCampoPayload) =>
      editing
        ? updateInstrumentoCampo(instrumento.id, editing.id, payload)
        : createInstrumentoCampo(instrumento.id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa", instrumento.id, "campos"] });
      setOpen(false);
      setEditing(null);
    },
  });

  const remove = useMutation({
    mutationFn: (campo: InstrumentoCampo) => deleteInstrumentoCampo(instrumento.id, campo.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa", instrumento.id, "campos"] });
    },
  });

  const reorder = useMutation({
    mutationFn: (ordered: InstrumentoCampo[]) =>
      reorderInstrumentoCampos(
        instrumento.id,
        ordered.map((campo, index) => ({ id: campo.id, ordem: index })),
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["instrumentos-pesquisa", instrumento.id, "campos"] });
    },
  });

  function moveCampo(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= campos.length) return;
    const ordered = [...campos];
    [ordered[index], ordered[target]] = [ordered[target], ordered[index]];
    reorder.mutate(ordered);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Campos configuráveis</h3>
          <p className="text-sm text-muted-foreground">{campos.length} campos configurados para este instrumento.</p>
        </div>
        <Button
          onClick={() => {
            mutation.reset();
            setEditing(null);
            setOpen(true);
          }}
        >
          <Plus className="h-4 w-4" />
          Adicionar campo
        </Button>
      </div>

      {camposQuery.error ? <p className="text-sm text-destructive">{camposQuery.error.message}</p> : null}
      <Card>
        <CardContent className="overflow-x-auto p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ordem</TableHead>
                <TableHead>Nome</TableHead>
                <TableHead>Chave</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Obrigatório</TableHead>
                <TableHead>Exibição</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campos.map((campo, index) => (
                <TableRow key={campo.id}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell className="font-medium">{campo.nome}</TableCell>
                  <TableCell>{campo.chave}</TableCell>
                  <TableCell>{labelFor(campoTipoOptions, campo.tipo)}</TableCell>
                  <TableCell>{campo.obrigatorio ? "Sim" : "Não"}</TableCell>
                  <TableCell>{formatVisibilityFlags(campo)}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" title="Subir campo" disabled={index === 0 || reorder.isPending} onClick={() => moveCampo(index, -1)}>
                        <ArrowUp className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Descer campo" disabled={index === campos.length - 1 || reorder.isPending} onClick={() => moveCampo(index, 1)}>
                        <ArrowDown className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Editar campo" onClick={() => { mutation.reset(); setEditing(campo); setOpen(true); }}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Excluir campo" disabled={remove.isPending} onClick={() => remove.mutate(campo)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {!campos.length ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                    Nenhum campo configurado.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? "Editar campo" : "Novo campo"}</DialogTitle>
            <DialogDescription>Configure como o campo aparece no cadastro, listagem e busca.</DialogDescription>
          </DialogHeader>
          <CampoForm
            key={editing?.id ?? "novo"}
            campo={editing}
            nextOrder={campos.length}
            isSaving={mutation.isPending}
            error={mutation.error?.message}
            onSubmit={(payload) => mutation.mutate(payload)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

function CampoForm({
  campo,
  nextOrder,
  isSaving,
  error,
  onSubmit,
}: {
  campo: InstrumentoCampo | null;
  nextOrder: number;
  isSaving: boolean;
  error?: string;
  onSubmit: (payload: InstrumentoCampoPayload) => void;
}) {
  const [values, setValues] = useState<InstrumentoCampoPayload>({
    nome: campo?.nome ?? "",
    chave: campo?.chave ?? "",
    tipo: campo?.tipo ?? "TEXTO_CURTO",
    ordem: campo?.ordem ?? nextOrder,
    obrigatorio: campo?.obrigatorio ?? false,
    multiplo: campo?.multiplo ?? false,
    valor_padrao: campo?.valor_padrao ?? "",
    placeholder: campo?.placeholder ?? "",
    ajuda: campo?.ajuda ?? "",
    aparece_cadastro: campo?.aparece_cadastro ?? true,
    aparece_listagem: campo?.aparece_listagem ?? true,
    aparece_busca: campo?.aparece_busca ?? true,
    filtro_avancado: campo?.filtro_avancado ?? false,
    facetavel: campo?.facetavel ?? false,
    ordenavel: campo?.ordenavel ?? false,
    opcoes: campo?.opcoes ?? null,
    validacoes: campo?.validacoes ?? null,
  });

  return (
    <form
      className="grid gap-4 sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit({
          ...values,
          nome: values.nome.trim(),
          chave: values.chave.trim(),
          valor_padrao: optionalText(values.valor_padrao),
          placeholder: optionalText(values.placeholder),
          ajuda: optionalText(values.ajuda),
        });
      }}
    >
      <Field label="Nome" required>
        <Input value={values.nome} maxLength={255} required onChange={(event) => setValues({ ...values, nome: event.target.value })} />
      </Field>
      <Field label="Chave" required>
        <Input value={values.chave} maxLength={100} required placeholder="titulo_principal" onChange={(event) => setValues({ ...values, chave: event.target.value })} />
      </Field>
      <SelectField label="Tipo" value={values.tipo} options={campoTipoOptions} required onChange={(tipo) => setValues({ ...values, tipo: tipo as TipoCampoInstrumento })} />
      <Field label="Ordem">
        <Input type="number" min={0} value={values.ordem} onChange={(event) => setValues({ ...values, ordem: Number(event.target.value) })} />
      </Field>
      <Field label="Placeholder">
        <Input value={values.placeholder ?? ""} onChange={(event) => setValues({ ...values, placeholder: event.target.value })} />
      </Field>
      <Field label="Valor padrão">
        <Input value={values.valor_padrao ?? ""} onChange={(event) => setValues({ ...values, valor_padrao: event.target.value })} />
      </Field>
      <Field label="Texto de ajuda" className="sm:col-span-2">
        <textarea
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={values.ajuda ?? ""}
          onChange={(event) => setValues({ ...values, ajuda: event.target.value })}
        />
      </Field>
      <div className="grid gap-2 sm:col-span-2 sm:grid-cols-4">
        <CheckField label="Obrigatório" checked={values.obrigatorio} onChange={(obrigatorio) => setValues({ ...values, obrigatorio })} />
        <CheckField label="Múltiplo" checked={values.multiplo} onChange={(multiplo) => setValues({ ...values, multiplo })} />
        <CheckField label="Aparece no cadastro" checked={values.aparece_cadastro} onChange={(aparece_cadastro) => setValues({ ...values, aparece_cadastro })} />
        <CheckField label="Aparece na listagem" checked={values.aparece_listagem} onChange={(aparece_listagem) => setValues({ ...values, aparece_listagem })} />
        <CheckField label="Aparece na busca" checked={values.aparece_busca} onChange={(aparece_busca) => setValues({ ...values, aparece_busca })} />
        <CheckField label="Filtro avançado" checked={values.filtro_avancado} onChange={(filtro_avancado) => setValues({ ...values, filtro_avancado })} />
        <CheckField label="Facetável" checked={values.facetavel} onChange={(facetavel) => setValues({ ...values, facetavel })} />
        <CheckField label="Ordenável" checked={values.ordenavel} onChange={(ordenavel) => setValues({ ...values, ordenavel })} />
      </div>
      {error ? <p className="text-sm text-destructive sm:col-span-2">{error}</p> : null}
      <div className="sm:col-span-2">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? "Salvando..." : "Salvar campo"}
        </Button>
      </div>
    </form>
  );
}

function Field({
  label,
  children,
  className = "",
  required,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
  required?: boolean;
}) {
  return (
    <div className={`space-y-2 ${className}`}>
      <Label>
        {label}
        {required ? <span className="ml-1 text-destructive">*</span> : null}
      </Label>
      {children}
    </div>
  );
}

function SelectField({
  label,
  value,
  options,
  includeEmpty,
  required,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<[string, string]>;
  includeEmpty?: boolean;
  required?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>
        {label}
        {required ? <span className="ml-1 text-destructive">*</span> : null}
      </Label>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      >
        {includeEmpty ? <option value="">Todos</option> : null}
        {options.map(([optionValue, labelText]) => (
          <option key={optionValue} value={optionValue}>
            {labelText}
          </option>
        ))}
      </select>
    </div>
  );
}

function CheckField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex min-h-10 items-center gap-3 rounded-md border px-3 py-2 text-sm">
      <input type="checkbox" className="h-4 w-4" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      {label}
    </label>
  );
}

function StatusPill({ value }: { value: StatusInstrumentoPesquisa }) {
  const classes = {
    RASCUNHO: "bg-slate-100 text-slate-700",
    PUBLICADO: "bg-emerald-50 text-emerald-800",
    ARQUIVADO: "bg-amber-50 text-amber-800",
  }[value];

  return (
    <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ${classes}`}>
      {labelFor(statusOptions, value)}
    </span>
  );
}

function labelFor(options: Array<[string, string]>, value: string) {
  return options.find(([optionValue]) => optionValue === value)?.[1] ?? value;
}

function optionalText(value: string | null | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatVisibilityFlags(campo: InstrumentoCampo) {
  const flags = [
    campo.aparece_cadastro ? "cadastro" : null,
    campo.aparece_listagem ? "listagem" : null,
    campo.aparece_busca ? "busca" : null,
  ].filter(Boolean);

  return flags.length ? flags.join(", ") : "-";
}
