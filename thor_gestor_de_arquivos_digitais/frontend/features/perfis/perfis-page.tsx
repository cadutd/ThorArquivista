"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit, Eye, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { deletePerfil, listPerfisPage, type PerfilFilters } from "@/lib/api/perfis-permissoes";
import type { Perfil } from "@/types/domain";

export function PerfisPage() {
  const [filters, setFilters] = useState<PerfilFilters>({});
  const [draftFilters, setDraftFilters] = useState<PerfilFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [selected, setSelected] = useState<Perfil | null>(null);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["perfis", filters, pageIndex, pageSize],
    queryFn: () => listPerfisPage({ limit: pageSize, offset: pageIndex * pageSize, filters }),
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePerfil(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["perfis"] });
      setSelected(null);
    },
  });
  const perfis = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);
  const applyFilters = (nextFilters: PerfilFilters) => {
    setFilters(nextFilters);
    setPageIndex(0);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Buscar perfil" value={draftFilters.q ?? ""} onChange={(event) => setDraftFilters({ q: event.target.value })} onKeyDown={(event) => event.key === "Enter" && applyFilters(draftFilters)} />
        </div>
        <Button type="button" onClick={() => applyFilters(draftFilters)}><Search className="h-4 w-4" />Pesquisar</Button>
        <Button type="button" variant="outline" onClick={() => { setDraftFilters({}); applyFilters({}); }}>Limpar</Button>
      </div>
      <PaginationControls currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} displayedCount={perfis.length} total={total} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Permissões</TableHead>
              <TableHead>Situação</TableHead>
              <TableHead>Sistema</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {perfis.length ? (
              perfis.map((perfil) => (
                <TableRow key={perfil.id}>
                  <TableCell><button type="button" className="font-medium text-primary hover:underline" onClick={() => setSelected(perfil)}>{perfil.nome}</button></TableCell>
                  <TableCell>{perfil.codigo}</TableCell>
                  <TableCell>{perfil.permissoes.length}</TableCell>
                  <TableCell>{perfil.ativo ? "Ativo" : "Inativo"}</TableCell>
                  <TableCell>{perfil.sistema ? "Sim" : "Não"}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button type="button" variant="ghost" size="icon" aria-label="Visualizar perfil" onClick={() => setSelected(perfil)}><Eye className="h-4 w-4" /></Button>
                      <Button asChild variant="ghost" size="icon" aria-label="Editar perfil"><Link href={`/perfis/${perfil.id}/editar`}><Edit className="h-4 w-4" /></Link></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{query.isLoading ? "Carregando perfis..." : "Nenhum perfil encontrado."}</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <PaginationControls currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} displayedCount={perfis.length} total={total} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Perfil</DialogTitle>
            <DialogDescription>Visualização do perfil e permissões associadas.</DialogDescription>
          </DialogHeader>
          {selected ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <DetailLine label="Nome" value={selected.nome} />
                <DetailLine label="Código" value={selected.codigo} />
                <DetailLine label="Ativo" value={selected.ativo ? "Sim" : "Não"} />
                <DetailLine label="Sistema" value={selected.sistema ? "Sim" : "Não"} />
              </div>
              {selected.descricao ? <p className="whitespace-pre-wrap text-sm text-muted-foreground">{selected.descricao}</p> : null}
              <div className="rounded-md border p-3">
                <p className="text-sm font-semibold">Permissões</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selected.permissoes.map((permissao) => <span key={permissao.id} className="rounded-md border px-2 py-1 text-xs">{permissao.codigo}</span>)}
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button asChild variant="outline"><Link href={`/perfis/${selected.id}/editar`}><Edit className="h-4 w-4" />Editar</Link></Button>
                <Button type="button" variant="destructive" disabled={deleteMutation.isPending} onClick={() => window.confirm("Excluir este perfil?") && deleteMutation.mutate(selected.id)}><Trash2 className="h-4 w-4" />{deleteMutation.isPending ? "Excluindo..." : "Excluir"}</Button>
              </div>
              {deleteMutation.error ? <p className="text-sm text-destructive">{deleteMutation.error.message}</p> : null}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 break-words text-sm">{value}</div></div>;
}

function PaginationControls({ currentPage, totalPages, pageSize, displayedCount, total, isLoading, onPageChange, onPageSizeChange }: { currentPage: number; totalPages: number; pageSize: number; displayedCount: number; total: number; isLoading: boolean; onPageChange: (pageIndex: number) => void; onPageSizeChange: (pageSize: number) => void }) {
  return <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2"><p className="text-sm text-muted-foreground">{displayedCount} registros de {total} | página {currentPage} de {totalPages}</p><div className="flex flex-wrap items-center gap-2"><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button><Label htmlFor="perfis-page-size" className="text-sm text-muted-foreground">Por página:</Label><select id="perfis-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}><option value={20}>20</option><option value={50}>50</option><option value={100}>100</option></select></div></div>;
}
