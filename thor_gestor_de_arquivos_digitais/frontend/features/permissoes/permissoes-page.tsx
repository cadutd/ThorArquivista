"use client";

import { useQuery } from "@tanstack/react-query";
import { Eye, Filter, Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listPermissoesPage, type PermissaoFilters } from "@/lib/api/perfis-permissoes";
import type { Permissao } from "@/types/domain";

export function PermissoesPage() {
  const [filters, setFilters] = useState<PermissaoFilters>({});
  const [draftFilters, setDraftFilters] = useState<PermissaoFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selected, setSelected] = useState<Permissao | null>(null);

  const query = useQuery({
    queryKey: ["permissoes", filters, pageIndex, pageSize],
    queryFn: () => listPermissoesPage({ limit: pageSize, offset: pageIndex * pageSize, filters }),
  });

  const permissoes = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);
  const applyFilters = (nextFilters: PermissaoFilters) => {
    setFilters(nextFilters);
    setPageIndex(0);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar permissão"
            value={draftFilters.q ?? ""}
            onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
            onKeyDown={(event) => event.key === "Enter" && applyFilters(draftFilters)}
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
      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Módulo">
            <Input value={draftFilters.modulo ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, modulo: event.target.value })} />
          </FilterField>
          <FilterField label="Função">
            <Input value={draftFilters.funcao ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, funcao: event.target.value })} />
          </FilterField>
          <SelectFilter label="Ação" value={draftFilters.acao ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, acao: (value || undefined) as PermissaoFilters["acao"] })}>
            <option value="">Todas</option>
            <option value="CRIAR">Criar</option>
            <option value="EDITAR">Editar</option>
            <option value="CONSULTAR">Consultar</option>
            <option value="EXCLUIR">Excluir</option>
          </SelectFilter>
          <SelectFilter label="Situação" value={draftFilters.ativo ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, ativo: value || undefined })}>
            <option value="">Todas</option>
            <option value="true">Ativa</option>
            <option value="false">Inativa</option>
          </SelectFilter>
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => applyFilters(draftFilters)}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button type="button" variant="outline" onClick={() => { setDraftFilters({}); applyFilters({}); }}>
              Limpar
            </Button>
          </div>
        </div>
      ) : null}

      <PaginationControls currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} displayedCount={permissoes.length} total={total} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Módulo</TableHead>
              <TableHead>Função</TableHead>
              <TableHead>Ação</TableHead>
              <TableHead>Situação</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {permissoes.length ? (
              permissoes.map((permissao) => (
                <TableRow key={permissao.id}>
                  <TableCell><button type="button" className="font-medium text-primary hover:underline" onClick={() => setSelected(permissao)}>{permissao.nome}</button></TableCell>
                  <TableCell>{permissao.codigo}</TableCell>
                  <TableCell>{permissao.modulo}</TableCell>
                  <TableCell>{permissao.funcao}</TableCell>
                  <TableCell>{labelAcao(permissao.acao)}</TableCell>
                  <TableCell>{permissao.ativo ? "Ativa" : "Inativa"}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button type="button" variant="ghost" size="icon" aria-label="Visualizar permissão" onClick={() => setSelected(permissao)}><Eye className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow><TableCell colSpan={7} className="h-24 text-center text-muted-foreground">{query.isLoading ? "Carregando permissões..." : "Nenhuma permissão encontrada."}</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <PaginationControls currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} displayedCount={permissoes.length} total={total} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Permissão</DialogTitle>
            <DialogDescription>Visualização da permissão cadastrada.</DialogDescription>
          </DialogHeader>
          {selected ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ["Nome", selected.nome],
                  ["Código", selected.codigo],
                  ["Módulo", selected.modulo],
                  ["Função", selected.funcao],
                  ["Ação", labelAcao(selected.acao)],
                  ["Ativa", selected.ativo ? "Sim" : "Não"],
                ].map(([label, value]) => <DetailLine key={label} label={label} value={value} />)}
              </div>
              {selected.descricao ? <p className="whitespace-pre-wrap text-sm text-muted-foreground">{selected.descricao}</p> : null}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function labelAcao(value: string) {
  return { CRIAR: "Criar", EDITAR: "Editar", CONSULTAR: "Consultar", EXCLUIR: "Excluir" }[value] ?? value;
}

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 break-words text-sm">{value}</div></div>;
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}

function SelectFilter({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return <FilterField label={label}><select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={value} onChange={(event) => onChange(event.target.value)}>{children}</select></FilterField>;
}

function PaginationControls({ currentPage, totalPages, pageSize, displayedCount, total, isLoading, onPageChange, onPageSizeChange }: { currentPage: number; totalPages: number; pageSize: number; displayedCount: number; total: number; isLoading: boolean; onPageChange: (pageIndex: number) => void; onPageSizeChange: (pageSize: number) => void }) {
  return <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2"><p className="text-sm text-muted-foreground">{displayedCount} registros de {total} | página {currentPage} de {totalPages}</p><div className="flex flex-wrap items-center gap-2"><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button><Label htmlFor="permissoes-page-size" className="text-sm text-muted-foreground">Por página:</Label><select id="permissoes-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}><option value={20}>20</option><option value={50}>50</option><option value={100}>100</option></select></div></div>;
}
