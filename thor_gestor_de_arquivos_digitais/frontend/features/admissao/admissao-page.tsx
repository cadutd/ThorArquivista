"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit, Eye, Filter, Plus, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { deleteProcessoAdmissao, listProcessosAdmissao, type ProcessoAdmissao, type ProcessoAdmissaoFilters } from "@/lib/api/admissao";

export function AdmissaoPage() {
  const [filters, setFilters] = useState<ProcessoAdmissaoFilters>({});
  const [draftFilters, setDraftFilters] = useState<ProcessoAdmissaoFilters>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const query = useQuery({
    queryKey: ["admissao", "processos", filters, pageIndex, pageSize],
    queryFn: () => listProcessosAdmissao({ limit: pageSize, offset: pageIndex * pageSize, filters }),
  });
  const processos = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  const applyFilters = (next: ProcessoAdmissaoFilters) => {
    setFilters(next);
    setPageIndex(0);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Admissão</h1>
          <p className="text-sm text-muted-foreground">Processos de admissão OAIS, acordos, submissões, SIPs e eventos.</p>
        </div>
        <Button asChild><Link href="/admissao/novo"><Plus className="h-4 w-4" />Novo processo</Link></Button>
      </div>

      <div className="space-y-3 rounded-md border p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative w-full lg:w-96">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Buscar por número ou título"
                value={draftFilters.q ?? ""}
                onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
                onKeyDown={(event) => event.key === "Enter" && applyFilters(draftFilters)}
              />
            </div>
            <Button type="button" onClick={() => applyFilters(draftFilters)}><Search className="h-4 w-4" />Pesquisar</Button>
            <Button type="button" variant="outline" onClick={() => setShowAdvanced((value) => !value)}><Filter className="h-4 w-4" />Filtros</Button>
          </div>
          <p className="text-sm text-muted-foreground">{query.isLoading ? "Carregando..." : `${total} registros`}</p>
        </div>

        {showAdvanced ? (
          <div className="grid gap-3 border-t pt-4 md:grid-cols-2 xl:grid-cols-4">
            <FilterField label="Número"><Input value={draftFilters.numero_processo ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, numero_processo: event.target.value })} /></FilterField>
            <FilterField label="Título"><Input value={draftFilters.titulo ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, titulo: event.target.value })} /></FilterField>
            <SelectFilter label="Status" value={draftFilters.status ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, status: value as ProcessoAdmissaoFilters["status"] })}>
              <option value="">Todos</option>{["ABERTO","EM_NEGOCIACAO","EM_RECEBIMENTO","EM_QUARENTENA","EM_VALIDACAO","PENDENTE_COMPLEMENTACAO","EM_GERACAO_AIP","CONCLUIDO","CANCELADO","REJEITADO"].map((value) => <option key={value} value={value}>{label(value)}</option>)}
            </SelectFilter>
            <SelectFilter label="Suporte" value={draftFilters.tipo_suporte ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, tipo_suporte: value as ProcessoAdmissaoFilters["tipo_suporte"] })}>
              <option value="">Todos</option><option value="DIGITAL">Digital</option><option value="FISICO">Físico</option><option value="HIBRIDO">Híbrido</option>
            </SelectFilter>
            <div className="flex items-end gap-2">
              <Button type="button" onClick={() => applyFilters(draftFilters)}>Aplicar</Button>
              <Button type="button" variant="outline" onClick={() => { setDraftFilters({}); applyFilters({}); }}>Limpar</Button>
            </div>
          </div>
        ) : null}
      </div>

      <Pagination currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} total={total} displayedCount={processos.length} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      <ProcessosTable processos={processos} isLoading={query.isLoading} />
      <Pagination currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} total={total} displayedCount={processos.length} isLoading={query.isFetching} onPageChange={setPageIndex} onPageSizeChange={(value) => { setPageSize(value); setPageIndex(0); }} />
      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
    </div>
  );
}

function ProcessosTable({ processos, isLoading }: { processos: ProcessoAdmissao[]; isLoading: boolean }) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: deleteProcessoAdmissao,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admissao"] }),
  });
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader><TableRow><TableHead>Processo</TableHead><TableHead>Produtor</TableHead><TableHead>Ingresso</TableHead><TableHead>Suporte</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader>
        <TableBody>
          {processos.length ? processos.map((processo) => (
            <TableRow key={processo.id}>
              <TableCell><Link className="font-medium text-primary hover:underline" href={`/admissao/${processo.id}`}>{processo.numero_processo}</Link><p className="text-xs text-muted-foreground">{processo.titulo}</p></TableCell>
              <TableCell>{processo.nome_entidade_produtora || "-"}</TableCell>
              <TableCell>{label(processo.tipo_ingresso)}</TableCell>
              <TableCell>{label(processo.tipo_suporte)}</TableCell>
              <TableCell>{label(processo.status)}</TableCell>
              <TableCell><div className="flex justify-end gap-1">
                <Button asChild variant="ghost" size="icon" aria-label="Visualizar"><Link href={`/admissao/${processo.id}`}><Eye className="h-4 w-4" /></Link></Button>
                <Button asChild variant="ghost" size="icon" aria-label="Editar"><Link href={`/admissao/${processo.id}/editar`}><Edit className="h-4 w-4" /></Link></Button>
                <Button type="button" variant="ghost" size="icon" aria-label="Cancelar" disabled={deleteMutation.isPending} onClick={() => window.confirm("Cancelar este processo de admissão?") && deleteMutation.mutate(processo.id)}><Trash2 className="h-4 w-4" /></Button>
              </div></TableCell>
            </TableRow>
          )) : (
            <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{isLoading ? "Carregando processos..." : "Nenhum processo de admissão encontrado."}</TableCell></TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function Pagination({ currentPage, totalPages, pageSize, displayedCount, total, isLoading, onPageChange, onPageSizeChange }: { currentPage: number; totalPages: number; pageSize: number; displayedCount: number; total: number; isLoading: boolean; onPageChange: (pageIndex: number) => void; onPageSizeChange: (pageSize: number) => void }) {
  return <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2"><p className="text-sm text-muted-foreground">{displayedCount} registros de {total} | página {currentPage} de {totalPages}</p><div className="flex flex-wrap items-center gap-2"><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button><Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button><Label htmlFor="admissao-page-size" className="text-sm text-muted-foreground">Por página:</Label><select id="admissao-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}><option value={20}>20</option><option value={50}>50</option><option value={100}>100</option></select></div></div>;
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}

function SelectFilter({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return <FilterField label={label}><select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={value} onChange={(event) => onChange(event.target.value)}>{children}</select></FilterField>;
}

function label(value?: string | null) { return value ? value.replaceAll("_", " ") : "-"; }
