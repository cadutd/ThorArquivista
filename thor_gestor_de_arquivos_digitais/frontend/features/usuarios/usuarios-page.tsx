"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit, Eye, Filter, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
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
import { createIdentityAccount, deleteUsuario, listUsuariosPage, type IdentityAccount, type UsuarioFilters } from "@/lib/api/usuarios";
import type { Usuario } from "@/types/domain";
import { papelUsuarioOptions } from "./usuario-form";

export function UsuariosPage() {
  const [filters, setFilters] = useState<UsuarioFilters>({});
  const [draftFilters, setDraftFilters] = useState<UsuarioFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selected, setSelected] = useState<Usuario | null>(null);

  const query = useQuery({
    queryKey: ["usuarios", filters, pageIndex, pageSize],
    queryFn: () =>
      listUsuariosPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });

  const usuarios = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  const applyFilters = (nextFilters: UsuarioFilters) => {
    setFilters(nextFilters);
    setPageIndex(0);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative w-full lg:w-80">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Buscar usuário"
              value={draftFilters.q ?? ""}
              onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  applyFilters(draftFilters);
                }
              }}
            />
          </div>
          <Button type="button" onClick={() => applyFilters(draftFilters)}>
            <Search className="h-4 w-4" />
            Pesquisar
          </Button>
          <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}>
            <Filter className="h-4 w-4" />
            Filtros
          </Button>
        </div>
      </div>

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Nome">
            <Input value={draftFilters.nome ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, nome: event.target.value })} />
          </FilterField>
          <FilterField label="Usuário">
            <Input value={draftFilters.username ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, username: event.target.value })} />
          </FilterField>
          <FilterField label="E-mail">
            <Input value={draftFilters.email ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, email: event.target.value })} />
          </FilterField>
          <SelectFilter
            label="Papel"
            value={draftFilters.papel ?? ""}
            onChange={(value) =>
              setDraftFilters({
                ...draftFilters,
                papel: (value || undefined) as UsuarioFilters["papel"],
              })
            }
          >
            <option value="">Todos</option>
            {papelUsuarioOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </SelectFilter>
          <SelectFilter label="Situação" value={draftFilters.ativo ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, ativo: value || undefined })}>
            <option value="">Todas</option>
            <option value="true">Ativo</option>
            <option value="false">Inativo</option>
          </SelectFilter>
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => applyFilters(draftFilters)}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDraftFilters({});
                applyFilters({});
              }}
            >
              Limpar
            </Button>
          </div>
        </div>
      ) : null}

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={usuarios.length}
        total={total}
        isLoading={query.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(value) => {
          setPageSize(value);
          setPageIndex(0);
        }}
      />
      <UsuariosTable data={usuarios} isLoading={query.isLoading} onSelect={setSelected} />
      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={usuarios.length}
        total={total}
        isLoading={query.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(value) => {
          setPageSize(value);
          setPageIndex(0);
        }}
      />

      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Usuário</DialogTitle>
            <DialogDescription>Visualização do perfil local.</DialogDescription>
          </DialogHeader>
          {selected ? <UsuarioDetails usuario={selected} onClose={() => setSelected(null)} /> : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function UsuariosTable({
  data,
  isLoading,
  onSelect,
}: {
  data: Usuario[];
  isLoading: boolean;
  onSelect: (usuario: Usuario) => void;
}) {
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Usuário</TableHead>
            <TableHead>E-mail</TableHead>
            <TableHead>Papel</TableHead>
            <TableHead>Situação</TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((usuario) => (
              <TableRow key={usuario.id}>
                <TableCell>
                  <button type="button" className="font-medium text-primary hover:underline" onClick={() => onSelect(usuario)}>
                    {usuario.nome}
                  </button>
                </TableCell>
                <TableCell>{usuario.username}</TableCell>
                <TableCell>{usuario.email}</TableCell>
                <TableCell>{labelPapel(usuario.papel)}</TableCell>
                <TableCell>{usuario.ativo ? "Ativo" : "Inativo"}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    <Button type="button" variant="ghost" size="icon" aria-label="Visualizar usuário" onClick={() => onSelect(usuario)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button asChild variant="ghost" size="icon" aria-label="Editar usuário">
                      <Link href={`/usuarios/${usuario.id}/editar`}>
                        <Edit className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                {isLoading ? "Carregando usuários..." : "Nenhum usuário encontrado."}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function UsuarioDetails({ usuario, onClose }: { usuario: Usuario; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [identityAccount, setIdentityAccount] = useState<IdentityAccount | null>(null);
  const deleteMutation = useMutation({
    mutationFn: () => deleteUsuario(usuario.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      onClose();
    },
  });
  const identityMutation = useMutation({
    mutationFn: () => createIdentityAccount(usuario.id, "KEYCLOAK"),
    onSuccess: async (data) => {
      setIdentityAccount(data);
      await queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
  const fields: Array<[string, string | boolean | null | undefined]> = [
    ["Nome", usuario.nome],
    ["Usuário", usuario.username],
    ["E-mail", usuario.email],
    ["Papel", labelPapel(usuario.papel)],
    ["Ativo", usuario.ativo ? "Sim" : "Não"],
    ["Sub Keycloak", usuario.keycloak_sub],
    ["Criado em", formatDate(usuario.criado_em)],
    ["Atualizado em", formatDate(usuario.atualizado_em)],
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
            <div className="mt-1 break-words text-sm">{value || "-"}</div>
          </div>
        ))}
      </div>
      {usuario.observacoes ? (
        <section className="space-y-1">
          <h3 className="text-sm font-semibold">Observações</h3>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{usuario.observacoes}</p>
        </section>
      ) : null}
      <div className="flex justify-end gap-2">
        {!usuario.keycloak_sub ? (
          <Button type="button" variant="outline" disabled={identityMutation.isPending} onClick={() => identityMutation.mutate()}>
            {identityMutation.isPending ? "Criando..." : "Criar no Keycloak"}
          </Button>
        ) : null}
        <Button asChild variant="outline">
          <Link href={`/usuarios/${usuario.id}/editar`}>
            <Edit className="h-4 w-4" />
            Editar
          </Link>
        </Button>
        <Button
          type="button"
          variant="destructive"
          disabled={deleteMutation.isPending}
          onClick={() => {
            if (window.confirm("Excluir este usuário?")) {
              deleteMutation.mutate();
            }
          }}
        >
          <Trash2 className="h-4 w-4" />
          {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
        </Button>
      </div>
      {identityMutation.error ? <p className="text-sm text-destructive">{identityMutation.error.message}</p> : null}
      {identityAccount ? (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
          <p className="font-medium">Conta criada no Keycloak.</p>
          <p>Usuário: {identityAccount.username}</p>
          <p>Senha temporária: <code className="rounded bg-white px-1">{identityAccount.temporary_password}</code></p>
          <p>O Keycloak exigirá troca de senha no primeiro acesso.</p>
        </div>
      ) : null}
      {deleteMutation.error ? <p className="text-sm text-destructive">{deleteMutation.error.message}</p> : null}
    </div>
  );
}

function labelPapel(value: string) {
  return papelUsuarioOptions.find((option) => option.value === value)?.label ?? value;
}

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString("pt-BR") : "-";
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
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
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={value} onChange={(event) => onChange(event.target.value)}>
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
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2">
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
        <Label htmlFor="usuarios-page-size" className="text-sm text-muted-foreground">
          Por página:
        </Label>
        <select id="usuarios-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}
