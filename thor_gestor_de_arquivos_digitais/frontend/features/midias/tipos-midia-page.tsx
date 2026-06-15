"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Edit, Eye, Filter, Plus, Power, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  createTipoMidia,
  deleteTipoMidia,
  getTipoMidia,
  listTiposMidiaPage,
  updateTipoMidia,
  type TipoMidiaFilters,
  type TipoMidiaPayload,
} from "@/lib/api/domain";
import type { TipoMidiaArmazenamento } from "@/types/domain";

const DEFAULT_PAGE_SIZE = 20;

const schema = z.object({
  nome: z.string().min(2, "Informe ao menos 2 caracteres.").max(255),
  descricao: z.string().optional(),
  tempo_duracao_anos: z.string().min(1, "Informe a duracao.").refine((value) => Number(value) > 0, "Informe um valor maior que zero."),
  periodicidade_checagem_meses: z.string().min(1, "Informe a periodicidade.").refine((value) => Number(value) > 0, "Informe um valor maior que zero."),
  ativo: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  nome: "",
  descricao: "",
  tempo_duracao_anos: "5",
  periodicidade_checagem_meses: "6",
  ativo: true,
};

export function TiposMidiaPage() {
  const queryClient = useQueryClient();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<TipoMidiaFilters>({});
  const [filters, setFilters] = useState<TipoMidiaFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const query = useQuery({
    queryKey: ["tipos-midia", filters, pageIndex, pageSize],
    queryFn: () =>
      listTiposMidiaPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTipoMidia,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tipos-midia"] }),
  });

  const data = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  function submitSearch(nextFilters = draftFilters) {
    setPageIndex(0);
    setFilters(cleanFilters(nextFilters));
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
          <h1 className="text-2xl font-semibold tracking-normal">Tipos de Mídia</h1>
          <p className="text-sm text-muted-foreground">
            Parametros de vida util e periodicidade de checagem das midias.
          </p>
        </div>
        <Button asChild>
          <Link href="/admin/tipos-midia/novo">
            <Plus className="h-4 w-4" />
            Novo tipo
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cadastro</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${total} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative w-full lg:w-80">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Buscar por nome ou descricao"
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

          {showAdvanced ? (
            <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
              <SelectFilter
                label="Status"
                value={draftFilters.ativo === undefined ? "" : String(draftFilters.ativo)}
                onChange={(ativo) =>
                  setDraftFilters((current) => ({ ...current, ativo: ativo === "" ? undefined : ativo === "true" }))
                }
              >
                <option value="">Todos</option>
                <option value="true">Ativo</option>
                <option value="false">Inativo</option>
              </SelectFilter>
              <div className="flex items-end gap-2">
                <Button type="button" onClick={() => submitSearch()}>
                  <Search className="h-4 w-4" />
                  Pesquisar
                </Button>
                <Button type="button" variant="outline" onClick={clearFilters}>
                  Limpar
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
            isLoading={query.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(nextPageSize) => {
              setPageSize(nextPageSize);
              setPageIndex(0);
            }}
          />

          {query.error ? (
            <p className="rounded-md border border-destructive/30 p-4 text-sm text-destructive">
              {query.error.message}
            </p>
          ) : (
            <div className="overflow-hidden rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Duracao</TableHead>
                    <TableHead>Checagem</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Atualizado em</TableHead>
                    <TableHead className="w-40 text-right">Acoes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.length ? (
                    data.map((tipo) => (
                      <TableRow key={tipo.id}>
                        <TableCell>
                          <div className="font-medium">{tipo.nome}</div>
                          <div className="text-xs text-muted-foreground">{tipo.descricao || "-"}</div>
                        </TableCell>
                        <TableCell>{tipo.tempo_duracao_anos} anos</TableCell>
                        <TableCell>{tipo.periodicidade_checagem_meses} meses</TableCell>
                        <TableCell>
                          <StatusBadge value={tipo.ativo ? "ATIVA" : "INATIVA"} />
                        </TableCell>
                        <TableCell>{formatDateTime(tipo.atualizado_em)}</TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-2">
                            <Button asChild variant="outline" size="icon" title="Visualizar tipo de midia" aria-label="Visualizar tipo de midia">
                              <Link href={`/admin/tipos-midia/${tipo.id}`}>
                                <Eye className="h-4 w-4" />
                              </Link>
                            </Button>
                            <Button asChild variant="outline" size="icon" title="Editar tipo de midia" aria-label="Editar tipo de midia">
                              <Link href={`/admin/tipos-midia/${tipo.id}/editar`}>
                                <Edit className="h-4 w-4" />
                              </Link>
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              title="Desativar tipo de midia"
                              aria-label="Desativar tipo de midia"
                              disabled={deleteMutation.isPending}
                              onClick={() => {
                                if (window.confirm("Desativar este tipo de midia?")) {
                                  deleteMutation.mutate(tipo.id);
                                }
                              }}
                            >
                              <Power className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                        Nenhum tipo de midia cadastrado.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
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
        </CardContent>
      </Card>
    </div>
  );
}

export function TipoMidiaNewPage() {
  const router = useRouter();

  return (
    <TipoMidiaFormShell
      title="Novo tipo de midia"
      description="Preencha os parametros usados no ciclo de vida das midias."
    >
      <TipoMidiaForm onSaved={() => router.push("/admin/tipos-midia")} />
    </TipoMidiaFormShell>
  );
}

export function TipoMidiaEditPage({ tipoId }: { tipoId: string }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["tipos-midia", tipoId],
    queryFn: () => getTipoMidia(tipoId),
    enabled: Boolean(tipoId),
  });

  return (
    <TipoMidiaFormShell
      title="Editar tipo de midia"
      description="Atualize os parametros de duracao, checagem e status."
    >
      {query.isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando tipo de midia...</p>
      ) : query.error ? (
        <p className="text-sm text-destructive">{query.error.message}</p>
      ) : query.data ? (
        <TipoMidiaForm tipo={query.data} onSaved={() => router.push("/admin/tipos-midia")} />
      ) : (
        <p className="text-sm text-muted-foreground">Tipo de midia nao encontrado.</p>
      )}
    </TipoMidiaFormShell>
  );
}

export function TipoMidiaViewPage({ tipoId }: { tipoId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["tipos-midia", tipoId],
    queryFn: () => getTipoMidia(tipoId),
    enabled: Boolean(tipoId),
  });
  const tipo = query.data;
  const toggleMutation = useMutation({
    mutationFn: async () => {
      if (!tipo) return null;
      return tipo.ativo ? deleteTipoMidia(tipo.id) : updateTipoMidia(tipo.id, { ativo: true });
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["tipos-midia"] }),
        queryClient.invalidateQueries({ queryKey: ["tipos-midia", tipoId] }),
        queryClient.invalidateQueries({ queryKey: ["midias"] }),
      ]);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar tipo de midia</h1>
          <p className="text-sm text-muted-foreground">Consulta dos parametros de ciclo de vida do tipo.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {tipo ? (
            <>
              <Button
                type="button"
                variant="outline"
                disabled={toggleMutation.isPending}
                title={tipo.ativo ? "Desativar tipo de midia" : "Ativar tipo de midia"}
                aria-label={tipo.ativo ? "Desativar tipo de midia" : "Ativar tipo de midia"}
                onClick={() => {
                  const acao = tipo.ativo ? "desativar" : "ativar";
                  if (window.confirm(`Deseja ${acao} este tipo de midia?`)) {
                    toggleMutation.mutate();
                  }
                }}
              >
                <Power className="h-4 w-4" />
                {toggleMutation.isPending ? "Salvando..." : tipo.ativo ? "Desativar" : "Ativar"}
              </Button>
              <Button asChild variant="outline">
                <Link href={`/admin/tipos-midia/${tipo.id}/editar`}>
                  <Edit className="h-4 w-4" />
                  Editar
                </Link>
              </Button>
            </>
          ) : null}
          <Button asChild variant="outline">
            <Link href="/admin/tipos-midia">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{tipo?.nome ?? "Tipo de midia"}</CardTitle>
          <CardDescription>
            {query.isLoading
              ? "Carregando tipo de midia."
              : tipo
                ? "Parametros cadastrados para validade e checagem."
                : "Tipo de midia nao encontrado."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando tipo de midia...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : tipo ? (
            <div className="space-y-3">
              {toggleMutation.error ? (
                <p className="rounded-md border border-destructive/30 p-3 text-sm text-destructive">
                  {toggleMutation.error.message}
                </p>
              ) : null}
              <section className="grid gap-3 md:grid-cols-2">
                <DetailLine label="Nome" value={tipo.nome} />
                <DetailLine label="Status" value={<StatusBadge value={tipo.ativo ? "ATIVA" : "INATIVA"} />} />
                <DetailLine label="Duracao" value={`${tipo.tempo_duracao_anos} anos`} />
                <DetailLine label="Periodicidade de checagem" value={`${tipo.periodicidade_checagem_meses} meses`} />
                <DetailLine label="Criado em" value={formatDateTime(tipo.criado_em)} />
                <DetailLine label="Atualizado em" value={formatDateTime(tipo.atualizado_em)} />
                <div className="rounded-md border p-3 md:col-span-2">
                  <p className="text-xs font-medium uppercase text-muted-foreground">Descricao</p>
                  <div className="mt-1 text-sm">{tipo.descricao || "-"}</div>
                </div>
              </section>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Tipo de midia nao encontrado.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TipoMidiaFormShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/admin/tipos-midia">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados do tipo</CardTitle>
          <CardDescription>Campos obrigatorios sao marcados com asterisco.</CardDescription>
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </div>
  );
}

function TipoMidiaForm({
  tipo,
  onSaved,
}: {
  tipo?: TipoMidiaArmazenamento;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    form.reset(tipo ? defaultValuesFrom(tipo) : defaultValues);
  }, [form, tipo]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload: TipoMidiaPayload = {
        nome: values.nome.trim(),
        descricao: values.descricao?.trim() || null,
        tempo_duracao_anos: Number(values.tempo_duracao_anos),
        periodicidade_checagem_meses: Number(values.periodicidade_checagem_meses),
        ativo: values.ativo,
      };
      return tipo ? updateTipoMidia(tipo.id, payload) : createTipoMidia(payload);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["tipos-midia"] }),
        queryClient.invalidateQueries({ queryKey: ["midias"] }),
      ]);
      if (!tipo) {
        form.reset(defaultValues);
      }
      onSaved?.();
    },
  });

  return (
    <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nome" error={form.formState.errors.nome?.message} required>
          <Input {...form.register("nome")} placeholder="LTO-9" required />
        </Field>
        <Field label="Status">
          <label className="flex h-10 items-center gap-3 rounded-md border px-3 text-sm">
            <input type="checkbox" className="h-4 w-4" {...form.register("ativo")} />
            Tipo ativo
          </label>
        </Field>
      </div>

      <Field label="Descricao" error={form.formState.errors.descricao?.message}>
        <textarea
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("descricao")}
          placeholder="Caracteristicas ou politica de uso"
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Duracao em anos" error={form.formState.errors.tempo_duracao_anos?.message} required>
          <Input type="number" min={1} {...form.register("tempo_duracao_anos")} required />
        </Field>
        <Field
          label="Periodicidade de checagem em meses"
          error={form.formState.errors.periodicidade_checagem_meses?.message}
          required
        >
          <Input type="number" min={1} {...form.register("periodicidade_checagem_meses")} required />
        </Field>
      </div>

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : tipo ? "Salvar alteracoes" : "Salvar tipo"}
      </Button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
  required,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  required?: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label>
        {label}
        {required ? (
          <span className="ml-1 text-destructive" aria-label="obrigatorio">
            *
          </span>
        ) : null}
      </Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
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

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
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
        <Label htmlFor="tipos-midia-page-size" className="text-sm text-muted-foreground">
          Por pagina:
        </Label>
        <select
          id="tipos-midia-page-size"
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

function cleanFilters(filters: TipoMidiaFilters): TipoMidiaFilters {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ) as TipoMidiaFilters;
}

function defaultValuesFrom(tipo: TipoMidiaArmazenamento): FormValues {
  return {
    nome: tipo.nome,
    descricao: tipo.descricao ?? "",
    tempo_duracao_anos: String(tipo.tempo_duracao_anos),
    periodicidade_checagem_meses: String(tipo.periodicidade_checagem_meses),
    ativo: tipo.ativo,
  };
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
