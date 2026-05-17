"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Edit, Eye, Filter, Loader2, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
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
import {
  deleteEntidadeProdutora,
  getEntidadesProdutorasTree,
  getEntidadeProdutora,
  listEntidadesProdutorasPage,
  type EntidadeProdutoraFilters,
} from "@/lib/api/entidades-produtoras";
import type { EntidadeProdutora, EntidadeProdutoraTree } from "@/types/domain";
import { tipoEntidadeOptions } from "./entidade-produtora-form";

export function EntidadesProdutorasPage() {
  const [filters, setFilters] = useState<EntidadeProdutoraFilters>({});
  const [draftFilters, setDraftFilters] = useState<EntidadeProdutoraFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selected, setSelected] = useState<EntidadeProdutora | null>(null);
  const [selectedTreeId, setSelectedTreeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"lista" | "arvore">("lista");

  const query = useQuery({
    queryKey: ["entidades-produtoras", filters, pageIndex, pageSize],
    queryFn: () =>
      listEntidadesProdutorasPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });
  const selectedTree = useQuery({
    queryKey: ["entidades-produtoras", selectedTreeId],
    queryFn: () => selectedTreeId ? getEntidadeProdutora(selectedTreeId) : Promise.resolve(null),
    enabled: Boolean(selectedTreeId),
  });
  const entidades = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  const applyFilters = (nextFilters: EntidadeProdutoraFilters) => {
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
              placeholder="Buscar entidade produtora"
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
        <div className="flex gap-2">
          <Button type="button" variant={viewMode === "lista" ? "default" : "outline"} onClick={() => setViewMode("lista")}>
            Lista
          </Button>
          <Button type="button" variant={viewMode === "arvore" ? "default" : "outline"} onClick={() => setViewMode("arvore")}>
            Árvore
          </Button>
        </div>
      </div>

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Nome">
            <Input value={draftFilters.nome ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, nome: event.target.value })} />
          </FilterField>
          <FilterField label="Sigla">
            <Input value={draftFilters.sigla ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, sigla: event.target.value })} />
          </FilterField>
          <SelectFilter
            label="Tipo"
            value={draftFilters.tipo_entidade ?? ""}
            onChange={(value) =>
              setDraftFilters({
                ...draftFilters,
                tipo_entidade: (value || undefined) as EntidadeProdutoraFilters["tipo_entidade"],
              })
            }
          >
            <option value="">Todos</option>
            {tipoEntidadeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </SelectFilter>
          <SelectFilter label="Situação" value={draftFilters.entidade_ativa ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, entidade_ativa: value || undefined })}>
            <option value="">Todas</option>
            <option value="true">Ativa</option>
            <option value="false">Inativa</option>
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

      {viewMode === "lista" ? (
        <>
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            displayedCount={entidades.length}
            total={total}
            isLoading={query.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPageIndex(0);
            }}
          />
          <EntidadesTable data={entidades} isLoading={query.isLoading} onSelect={setSelected} />
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            displayedCount={entidades.length}
            total={total}
            isLoading={query.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPageIndex(0);
            }}
          />
        </>
      ) : (
        <EntidadeProdutoraTreePanel
          filters={draftFilters}
          selectedId={selectedTreeId}
          onSelect={(id) => {
            setSelectedTreeId(id);
            setSelected(null);
          }}
        />
      )}

      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
      {selectedTree.error ? <p className="text-sm text-destructive">{selectedTree.error.message}</p> : null}

      <Dialog open={Boolean(selected) || Boolean(selectedTree.data)} onOpenChange={(open) => {
        if (!open) {
          setSelected(null);
          setSelectedTreeId(null);
        }
      }}>
        <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Entidade produtora</DialogTitle>
            <DialogDescription>Visualização completa do cadastro.</DialogDescription>
          </DialogHeader>
          {selected || selectedTree.data ? (
            <EntidadeDetails
              entidade={(selected ?? selectedTree.data) as EntidadeProdutora}
              onClose={() => {
                setSelected(null);
                setSelectedTreeId(null);
              }}
            />
          ) : selectedTree.isLoading ? (
            <LoadingLine />
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function EntidadesTable({
  data,
  isLoading,
  onSelect,
}: {
  data: EntidadeProdutora[];
  isLoading: boolean;
  onSelect: (entidade: EntidadeProdutora) => void;
}) {
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Sigla</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Situação</TableHead>
            <TableHead>Superior</TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((entidade) => (
              <TableRow key={entidade.id}>
                <TableCell>
                  <button type="button" className="font-medium text-primary hover:underline" onClick={() => onSelect(entidade)}>
                    {entidade.nome}
                  </button>
                </TableCell>
                <TableCell>{entidade.sigla || "-"}</TableCell>
                <TableCell>{entidade.tipo_entidade.replaceAll("_", " ")}</TableCell>
                <TableCell>{entidade.entidade_ativa ? "Ativa" : "Inativa"}</TableCell>
                <TableCell>{entidade.nome_entidade_superior || "-"}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    <Button type="button" variant="ghost" size="icon" aria-label="Visualizar entidade" onClick={() => onSelect(entidade)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button asChild variant="ghost" size="icon" aria-label="Editar entidade">
                      <Link href={`/entidades-produtoras/${entidade.id}/editar`}>
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
                {isLoading ? "Carregando entidades..." : "Nenhuma entidade produtora encontrada."}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function EntidadeDetails({ entidade, onClose }: { entidade: EntidadeProdutora; onClose: () => void }) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: () => deleteEntidadeProdutora(entidade.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["entidades-produtoras"] });
      onClose();
    },
  });
  const fields: Array<[string, string | number | boolean | null | undefined]> = [
    ["Nome", entidade.nome],
    ["Sigla", entidade.sigla],
    ["Código de referência", entidade.codigo_referencia],
    ["Tipo", entidade.tipo_entidade.replaceAll("_", " ")],
    ["Natureza jurídica", entidade.natureza_juridica],
    ["Entidade superior", entidade.nome_entidade_superior],
    ["Data de início", entidade.data_inicio],
    ["Data de fim", entidade.data_fim],
    ["Ativa", entidade.entidade_ativa ? "Sim" : "Não"],
    ["E-mail", entidade.email],
    ["Telefone", entidade.telefone],
    ["Site", entidade.site],
    ["Município", entidade.endereco_municipio],
    ["UF", entidade.endereco_uf],
    ["CEP", entidade.endereco_cep],
    ["País", entidade.endereco_pais],
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
            <div className="mt-1 text-sm">{value || "-"}</div>
          </div>
        ))}
      </div>
      <LongText label="Histórico" value={entidade.historico} />
      <LongText label="Competências/Funções" value={entidade.competencias_funcoes} />
      <LongText label="Observações" value={entidade.observacoes} />
      <div className="flex justify-end gap-2">
        <Button asChild variant="outline">
          <Link href={`/entidades-produtoras/${entidade.id}/editar`}>
            <Edit className="h-4 w-4" />
            Editar
          </Link>
        </Button>
        <Button
          type="button"
          variant="destructive"
          disabled={deleteMutation.isPending}
          onClick={() => {
            if (window.confirm("Excluir esta entidade produtora?")) {
              deleteMutation.mutate();
            }
          }}
        >
          <Trash2 className="h-4 w-4" />
          {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
        </Button>
      </div>
      {deleteMutation.error ? <p className="text-sm text-destructive">{deleteMutation.error.message}</p> : null}
    </div>
  );
}

function EntidadeProdutoraTreePanel({
  filters,
  selectedId,
  onSelect,
}: {
  filters: EntidadeProdutoraFilters;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [treeChildren, setTreeChildren] = useState<Record<string, EntidadeProdutoraTree[]>>({});
  const [loadingTreeNodes, setLoadingTreeNodes] = useState<Set<string>>(new Set());
  const treeParams = useMemo(
    () => ({
      q: filters.q,
      nome: filters.nome,
      sigla: filters.sigla,
      tipo_entidade: filters.tipo_entidade,
      entidade_ativa: filters.entidade_ativa,
    }),
    [filters],
  );
  const tree = useQuery({
    queryKey: ["entidades-produtoras", "arvore", treeParams],
    queryFn: () => getEntidadesProdutorasTree(treeParams),
  });
  const treeNodes = useMemo(
    () => hydrateTreeNodes(tree.data ?? [], treeChildren),
    [tree.data, treeChildren],
  );

  const toggleTreeNode = async (node: EntidadeProdutoraTree) => {
    setExpanded((currentSet) => toggleSet(currentSet, node.id));
    if (!node.has_children || treeChildren[node.id]) {
      return;
    }

    setLoadingTreeNodes((currentSet) => new Set(currentSet).add(node.id));
    try {
      const children = await queryClient.fetchQuery({
        queryKey: ["entidades-produtoras", "arvore", "children", node.id],
        queryFn: () => getEntidadesProdutorasTree({ parent_id: node.id }),
      });
      setTreeChildren((current) => ({ ...current, [node.id]: children }));
    } finally {
      setLoadingTreeNodes((currentSet) => {
        const next = new Set(currentSet);
        next.delete(node.id);
        return next;
      });
    }
  };

  if (tree.isLoading) {
    return <LoadingLine />;
  }
  if (tree.error) {
    return <p className="rounded-md border p-4 text-sm text-destructive">{tree.error.message}</p>;
  }
  if (!treeNodes.length) {
    return <p className="rounded-md border p-4 text-sm text-muted-foreground">Nenhuma hierarquia cadastrada.</p>;
  }

  return (
    <div className="max-h-[68vh] overflow-y-auto rounded-md border p-3 pr-1">
      {treeNodes.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          level={0}
          selectedId={selectedId}
          expanded={expanded}
          loadingIds={loadingTreeNodes}
          onToggle={toggleTreeNode}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function TreeNode({
  node,
  level,
  selectedId,
  expanded,
  loadingIds,
  onToggle,
  onSelect,
}: {
  node: EntidadeProdutoraTree;
  level: number;
  selectedId: string | null;
  expanded: Set<string>;
  loadingIds: Set<string>;
  onToggle: (node: EntidadeProdutoraTree) => void;
  onSelect: (id: string) => void;
}) {
  const hasChildren = node.has_children;
  const isOpen = expanded.has(node.id) || level < 1;
  const isLoading = loadingIds.has(node.id);

  return (
    <div>
      <div className="flex items-center gap-1" style={{ paddingLeft: level * 12 }}>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={() => hasChildren && onToggle(node)}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : hasChildren ? (
            isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
          ) : (
            <span className="h-4 w-4" />
          )}
        </Button>
      <button
        type="button"
          className={`min-w-0 flex-1 rounded-md px-2 py-1 text-left text-sm hover:bg-muted ${selectedId === node.id ? "bg-secondary text-secondary-foreground" : ""}`}
          onClick={() => onSelect(node.id)}
      >
          <span className="block truncate font-medium">{node.nome}</span>
          <span className="block truncate text-xs text-muted-foreground">
            {node.sigla ? `${node.sigla} - ` : ""}
            {node.tipo_entidade.replaceAll("_", " ")}
            {node.codigo_referencia ? ` - ${node.codigo_referencia}` : ""}
          </span>
      </button>
      </div>
      {hasChildren && isOpen
        ? node.filhos.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedId={selectedId}
              expanded={expanded}
              loadingIds={loadingIds}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))
        : null}
    </div>
  );
}

function LoadingLine() {
  return (
    <div className="flex items-center gap-2 rounded-md border p-4 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      Carregando...
    </div>
  );
}

function toggleSet(set: Set<string>, id: string) {
  const next = new Set(set);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  return next;
}

function hydrateTreeNodes(
  nodes: EntidadeProdutoraTree[],
  childrenByParent: Record<string, EntidadeProdutoraTree[]>,
): EntidadeProdutoraTree[] {
  return nodes.map((node) => ({
    ...node,
    filhos: hydrateTreeNodes(childrenByParent[node.id] ?? node.filhos, childrenByParent),
  }));
}

function LongText({ label, value }: { label: string; value?: string | null }) {
  return value ? (
    <section className="space-y-1">
      <h3 className="text-sm font-semibold">{label}</h3>
      <p className="whitespace-pre-wrap text-sm text-muted-foreground">{value}</p>
    </section>
  ) : null;
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
        <Label htmlFor="entidades-page-size" className="text-sm text-muted-foreground">
          Por página:
        </Label>
        <select id="entidades-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}
