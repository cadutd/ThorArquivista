"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ChevronDown, ChevronRight, Filter, Link2, Loader2, Save, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  atualizarUnidadesAssociadasDescricao,
  listarArvoreDescricao,
  listarRegistrosDescricao,
  listarUnidadesAssociadasDescricao,
} from "@/lib/api/descricao-arquivistica";
import { listUnidadesPage, type UnidadeFilters } from "@/lib/api/domain";
import type {
  NivelDescricao,
  RegistroDescritivo,
  RegistroDescritivoTreeNode,
} from "@/types/descricao-arquivistica";
import type { UnidadeAcondicionamento } from "@/types/domain";

const nivelLabels: Record<NivelDescricao, string> = {
  "1": "Fundo / Coleção",
  "2": "Seção",
  "2.5": "Subseção",
  "3": "Série",
  "3.5": "Subsérie",
  "4": "Dossiê / Processo",
  "5": "Item Documental",
};

export function DescricaoUnidadesPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const initialRegistroId = searchParams.get("registroId");
  const [selectedRegistroId, setSelectedRegistroId] = useState<string | null>(null);
  const [unidadeFilters, setUnidadeFilters] = useState<UnidadeFilters>({});
  const [unidadePageIndex, setUnidadePageIndex] = useState(0);
  const [unidadePageSize, setUnidadePageSize] = useState(20);
  const [selectedUnidades, setSelectedUnidades] = useState<Set<number>>(new Set());
  const [showSuccessAlert, setShowSuccessAlert] = useState(false);
  const registros = useQuery({
    queryKey: ["descricao-arquivistica", "registros"],
    queryFn: () => listarRegistrosDescricao(),
  });
  const unidades = useQuery({
    queryKey: ["unidades", "associacao-descricao", unidadeFilters, unidadePageIndex, unidadePageSize],
    queryFn: () =>
      listUnidadesPage({
        limit: unidadePageSize,
        offset: unidadePageIndex * unidadePageSize,
        filters: unidadeFilters,
      }),
  });
  const associadas = useQuery({
    queryKey: ["descricao-arquivistica", "registro-unidades", selectedRegistroId],
    queryFn: () =>
      selectedRegistroId
        ? listarUnidadesAssociadasDescricao(selectedRegistroId)
        : Promise.resolve({ id_registro_descritivo: "", unidades: [] }),
    enabled: Boolean(selectedRegistroId),
  });
  const mutation = useMutation({
    mutationFn: () => {
      if (!selectedRegistroId) {
        throw new Error("Selecione uma descrição arquivística.");
      }
      return atualizarUnidadesAssociadasDescricao(
        selectedRegistroId,
        Array.from(selectedUnidades),
      );
    },
    onSuccess: async (result) => {
      setSelectedUnidades(new Set(result.unidades.map((unidade) => unidade.id)));
      setShowSuccessAlert(true);
      await queryClient.invalidateQueries({
        queryKey: ["descricao-arquivistica", "registro-unidades", selectedRegistroId],
      });
    },
  });
  const selectedRegistro = (registros.data ?? []).find(
    (registro) => registro.id === selectedRegistroId,
  );

  const selectRegistro = (id: string) => {
    setSelectedRegistroId(id);
    setSelectedUnidades(new Set());
    setShowSuccessAlert(false);
    mutation.reset();
    listarUnidadesAssociadasDescricao(id)
      .then((result) => {
        setSelectedUnidades(new Set(result.unidades.map((unidade) => unidade.id)));
      })
      .catch(() => {
        setSelectedUnidades(new Set());
      });
  };

  useEffect(() => {
    if (initialRegistroId && initialRegistroId !== selectedRegistroId) {
      selectRegistro(initialRegistroId);
    }
  }, [initialRegistroId, selectedRegistroId]);

  useEffect(() => {
    if (!showSuccessAlert) {
      return;
    }

    const timeout = window.setTimeout(() => setShowSuccessAlert(false), 5000);
    return () => window.clearTimeout(timeout);
  }, [showSuccessAlert]);

  const toggleUnidade = (id: number) => {
    setSelectedUnidades((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (!initialRegistroId) {
    return (
      <div className="space-y-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Associar unidades à descrição arquivística</h1>
            <p className="text-sm text-muted-foreground">
              Abra uma descrição pela tela de edição e consulta para gerenciar suas unidades de acondicionamento.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/descricao-arquivistica">
              <ArrowLeft className="h-4 w-4" />
              Voltar para edição e consulta
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {showSuccessAlert ? (
        <div className="fixed left-1/2 top-4 z-50 flex w-[calc(100%-2rem)] max-w-md -translate-x-1/2 items-start gap-3 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm font-medium text-green-800 shadow-lg" role="alert">
          <span className="min-w-0 flex-1">Associação gravada com sucesso.</span>
          <button
            type="button"
            className="shrink-0 rounded-sm px-2 text-base leading-none text-green-900 hover:bg-green-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-700"
            aria-label="Fechar alerta"
            onClick={() => setShowSuccessAlert(false)}
          >
            x
          </button>
        </div>
      ) : null}
      <div>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">
              Associar unidades à descrição arquivística
            </h1>
            <p className="mt-1 text-lg font-semibold">{selectedRegistro?.titulo ?? "Carregando descrição..."}</p>
          </div>
          <Button asChild variant="outline">
            <Link href="/descricao-arquivistica">
              <ArrowLeft className="h-4 w-4" />
              Voltar para edição e consulta
            </Link>
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          Selecione as unidades de acondicionamento que devem ficar vinculadas a esta descrição.
        </p>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <CardTitle>{selectedRegistro?.titulo ?? "Unidades de acondicionamento"}</CardTitle>
                <CardDescription>
                  {selectedRegistro
                    ? `${selectedUnidades.size} unidade(s) selecionada(s) para este registro.`
                    : "Selecione uma descrição para gerenciar os vínculos."}
                </CardDescription>
              </div>
              <Button
                disabled={!selectedRegistroId || mutation.isPending || associadas.isLoading}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Salvar associações
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <UnidadeSearchControls
              dataCount={unidades.data?.items.length ?? 0}
              filters={unidadeFilters}
              isLoading={unidades.isFetching}
              pageIndex={unidadePageIndex}
              pageSize={unidadePageSize}
              total={unidades.data?.total ?? 0}
              onPageChange={setUnidadePageIndex}
              onPageSizeChange={(nextPageSize) => {
                setUnidadePageSize(nextPageSize);
                setUnidadePageIndex(0);
              }}
              onSearch={(nextFilters) => {
                setUnidadeFilters(nextFilters);
                setUnidadePageIndex(0);
              }}
            />
            {associadas.isLoading || unidades.isLoading ? <LoadingLine /> : null}
            {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
            <div className="max-h-[52vh] space-y-2 overflow-y-auto pr-1">
              {(unidades.data?.items ?? []).map((unidade) => (
                <UnidadeAssociationRow
                  key={unidade.id}
                  unidade={unidade}
                  checked={selectedUnidades.has(unidade.id)}
                  disabled={!selectedRegistroId}
                  onToggle={() => toggleUnidade(unidade.id)}
                />
              ))}
              {!unidades.isLoading && !(unidades.data?.items ?? []).length ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  Nenhuma unidade encontrada.
                </p>
              ) : null}
            </div>
            <PaginationControls
              currentPage={Math.min(unidadePageIndex + 1, Math.max(1, Math.ceil((unidades.data?.total ?? 0) / unidadePageSize)))}
              displayedCount={unidades.data?.items.length ?? 0}
              isLoading={unidades.isFetching}
              pageSize={unidadePageSize}
              total={unidades.data?.total ?? 0}
              totalPages={Math.max(1, Math.ceil((unidades.data?.total ?? 0) / unidadePageSize))}
              onPageChange={setUnidadePageIndex}
              onPageSizeChange={(nextPageSize) => {
                setUnidadePageSize(nextPageSize);
                setUnidadePageIndex(0);
              }}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DescricaoRegistroSelector({
  records,
  recordsLoading,
  selectedId,
  onSelect,
}: {
  records: RegistroDescritivo[];
  recordsLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const queryClient = useQueryClient();
  const [treeSearch, setTreeSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [treeChildren, setTreeChildren] = useState<Record<string, RegistroDescritivoTreeNode[]>>({});
  const [loadingTreeNodes, setLoadingTreeNodes] = useState<Set<string>>(new Set());
  const tree = useQuery({
    queryKey: ["descricao-arquivistica", "arvore", treeSearch, levelFilter],
    queryFn: () => listarArvoreDescricao({ q: treeSearch, nivel: levelFilter }),
  });
  const treeNodes = useMemo(
    () => hydrateTreeNodes(tree.data ?? [], treeChildren),
    [tree.data, treeChildren],
  );

  useEffect(() => {
    setExpanded(new Set());
    setTreeChildren({});
    setLoadingTreeNodes(new Set());
  }, [treeSearch, levelFilter]);

  const toggleTreeNode = async (node: RegistroDescritivoTreeNode) => {
    setExpanded((currentSet) => toggleSet(currentSet, node.id));
    if (!node.has_children || treeChildren[node.id]) {
      return;
    }

    setLoadingTreeNodes((currentSet) => new Set(currentSet).add(node.id));
    try {
      const children = await queryClient.fetchQuery({
        queryKey: ["descricao-arquivistica", "arvore", "children", node.id],
        queryFn: () => listarArvoreDescricao({ parent_id: node.id }),
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Árvore descritiva</CardTitle>
        <CardDescription>Navegue, filtre e selecione registros.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="arvore">
          <TabsList className="mb-3">
            <TabsTrigger value="arvore">Árvore</TabsTrigger>
            <TabsTrigger value="consulta">Consulta detalhada</TabsTrigger>
          </TabsList>
          <TabsContent value="arvore" className="space-y-3">
            <TreeFilters search={treeSearch} levelFilter={levelFilter} onSearch={setTreeSearch} onLevelFilter={setLevelFilter} />
            {tree.isLoading ? <LoadingLine /> : null}
            <div className="max-h-[62vh] overflow-y-auto pr-1">
              {treeNodes.map((node) => (
                <DescricaoTreeNode
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
              {!tree.isLoading && !(tree.data ?? []).length ? (
                <p className="py-6 text-center text-sm text-muted-foreground">Nenhum registro encontrado.</p>
              ) : null}
            </div>
          </TabsContent>
          <TabsContent value="consulta">
            <DetailedRegistroSearch records={records} isLoading={recordsLoading} selectedId={selectedId} onSelect={onSelect} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function UnidadeSearchControls({
  dataCount,
  filters,
  isLoading,
  pageIndex,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  onSearch,
}: {
  dataCount: number;
  filters: UnidadeFilters;
  isLoading: boolean;
  pageIndex: number;
  pageSize: number;
  total: number;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSearch: (filters: UnidadeFilters) => void;
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftFilters, setDraftFilters] = useState<UnidadeFilters>(filters);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);

  useEffect(() => {
    setDraftFilters(filters);
  }, [filters]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar unidade"
            value={draftFilters.q ?? ""}
            onChange={(event) => setDraftFilters({ ...draftFilters, q: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearch(draftFilters);
              }
            }}
          />
        </div>
        <Button type="button" onClick={() => onSearch(draftFilters)}>
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
        displayedCount={dataCount}
        isLoading={isLoading}
        pageSize={pageSize}
        total={total}
        totalPages={totalPages}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterField label="Identificador">
            <Input value={draftFilters.identificador ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, identificador: event.target.value })} />
          </FilterField>
          <FilterField label="Título">
            <Input value={draftFilters.titulo ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, titulo: event.target.value })} />
          </FilterField>
          <FilterField label="Descrição">
            <Input value={draftFilters.descricao ?? ""} onChange={(event) => setDraftFilters({ ...draftFilters, descricao: event.target.value })} />
          </FilterField>
          <SelectFilter label="Suporte" value={draftFilters.tipo_suporte ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, tipo_suporte: value })}>
            <option value="">Todos</option>
            <option value="FISICO">Físico</option>
            <option value="DIGITAL">Digital</option>
            <option value="HIBRIDO">Híbrido</option>
          </SelectFilter>
          <SelectFilter label="Tipo" value={draftFilters.tipo_unidade ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, tipo_unidade: value })}>
            <option value="">Todos</option>
            <option value="CAIXA">Caixa</option>
            <option value="PASTA">Pasta</option>
            <option value="VOLUME">Volume</option>
            <option value="AIP">AIP</option>
            <option value="SIP">SIP</option>
            <option value="DIP">DIP</option>
          </SelectFilter>
          <SelectFilter label="Acesso" value={draftFilters.nivel_acesso ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, nivel_acesso: value })}>
            <option value="">Todos</option>
            <option value="PUBLICO">Público</option>
            <option value="RESTRITO">Restrito</option>
            <option value="CONFIDENCIAL">Confidencial</option>
          </SelectFilter>
          <SelectFilter label="Status" value={draftFilters.status ?? ""} onChange={(value) => setDraftFilters({ ...draftFilters, status: value })}>
            <option value="">Todos</option>
            <option value="ATIVA">Ativa</option>
            <option value="INATIVA">Inativa</option>
            <option value="TRANSFERIDA">Transferida</option>
            <option value="ELIMINADA">Eliminada</option>
          </SelectFilter>
          <DateRangeFilter
            label="Criação"
            from={draftFilters.criado_em_de}
            to={draftFilters.criado_em_ate}
            onChange={(from, to) => setDraftFilters({ ...draftFilters, criado_em_de: from, criado_em_ate: to })}
          />
          <DateRangeFilter
            label="Atualização"
            from={draftFilters.atualizado_em_de}
            to={draftFilters.atualizado_em_ate}
            onChange={(from, to) => setDraftFilters({ ...draftFilters, atualizado_em_de: from, atualizado_em_ate: to })}
          />
          <div className="flex items-end gap-2">
            <Button type="button" onClick={() => onSearch(draftFilters)}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDraftFilters({});
                onSearch({});
              }}
            >
              Limpar filtros
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function TreeFilters({
  search,
  levelFilter,
  onSearch,
  onLevelFilter,
}: {
  search: string;
  levelFilter: string;
  onSearch: (value: string) => void;
  onLevelFilter: (value: string) => void;
}) {
  return (
    <>
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input className="pl-9" placeholder="Buscar na árvore" value={search} onChange={(event) => onSearch(event.target.value)} />
      </div>
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={levelFilter} onChange={(event) => onLevelFilter(event.target.value)}>
        <option value="">Todos os níveis</option>
        {Object.entries(nivelLabels).map(([value, label]) => (
          <option key={value} value={value}>Nível {value} - {label}</option>
        ))}
      </select>
    </>
  );
}

function DescricaoTreeNode({ node, level, selectedId, expanded, loadingIds, onToggle, onSelect }: { node: RegistroDescritivoTreeNode; level: number; selectedId: string | null; expanded: Set<string>; loadingIds: Set<string>; onToggle: (node: RegistroDescritivoTreeNode) => void; onSelect: (id: string) => void }) {
  const hasChildren = node.has_children;
  const isOpen = expanded.has(node.id) || level < 1;
  const isLoading = loadingIds.has(node.id);
  return (
    <div>
      <div className="flex items-center gap-1" style={{ paddingLeft: level * 12 }}>
        <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => hasChildren && onToggle(node)}>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : hasChildren ? (isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />) : <span className="h-4 w-4" />}
        </Button>
        <button type="button" className={`min-w-0 flex-1 rounded-md px-2 py-1 text-left text-sm hover:bg-muted ${selectedId === node.id ? "bg-secondary text-secondary-foreground" : ""}`} onClick={() => onSelect(node.id)}>
          <span className="block truncate font-medium">{node.titulo}</span>
          <span className="block truncate text-xs text-muted-foreground">Nível {node.nivel} - {node.codigo_referencia}</span>
        </button>
      </div>
      {hasChildren && isOpen ? node.children.map((child) => <DescricaoTreeNode key={child.id} node={child} level={level + 1} selectedId={selectedId} expanded={expanded} loadingIds={loadingIds} onToggle={onToggle} onSelect={onSelect} />) : null}
    </div>
  );
}

function DetailedRegistroSearch({ records, isLoading, selectedId, onSelect }: { records: RegistroDescritivo[]; isLoading: boolean; selectedId: string | null; onSelect: (id: string) => void }) {
  const [filters, setFilters] = useState({ q: "", nivel: "", norma: "", produtor: "", assunto: "" });
  const filtered = useMemo(() => {
    const q = normalize(filters.q);
    const produtor = normalize(filters.produtor);
    const assunto = normalize(filters.assunto);

    return records.filter((record) => {
      const searchable = normalize([
        record.codigo_referencia,
        record.titulo,
        record.produtor,
        record.ambito_conteudo,
        record.assuntos,
        record.pessoas,
        record.locais,
        record.entidades,
        record.eventos,
      ].filter(Boolean).join(" "));
      return (
        (!q || searchable.includes(q)) &&
        (!filters.nivel || record.nivel === filters.nivel) &&
        (!filters.norma || record.norma === filters.norma) &&
        (!produtor || normalize(record.produtor ?? "").includes(produtor)) &&
        (!assunto || normalize(record.assuntos ?? "").includes(assunto))
      );
    });
  }, [records, filters]);

  return (
    <div className="space-y-3">
      <SearchInput value={filters.q} onChange={(q) => setFilters({ ...filters, q })} placeholder="Buscar por título, código, conteúdo, índice..." />
      <div className="grid gap-3 sm:grid-cols-2">
        <select className="h-10 rounded-md border bg-background px-3 text-sm" value={filters.nivel} onChange={(event) => setFilters({ ...filters, nivel: event.target.value })}>
          <option value="">Todos os níveis</option>
          {Object.entries(nivelLabels).map(([value, label]) => <option key={value} value={value}>Nível {value} - {label}</option>)}
        </select>
        <select className="h-10 rounded-md border bg-background px-3 text-sm" value={filters.norma} onChange={(event) => setFilters({ ...filters, norma: event.target.value })}>
          <option value="">Todas as normas</option>
          <option value="NOBRADE">NOBRADE</option>
          <option value="ISAD_G">ISAD(G)</option>
          <option value="EAD2002">EAD2002</option>
        </select>
        <Input placeholder="Produtor" value={filters.produtor} onChange={(event) => setFilters({ ...filters, produtor: event.target.value })} />
        <Input placeholder="Assunto" value={filters.assunto} onChange={(event) => setFilters({ ...filters, assunto: event.target.value })} />
      </div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-muted-foreground">{filtered.length} registros encontrados</span>
        <Button variant="outline" size="sm" onClick={() => setFilters({ q: "", nivel: "", norma: "", produtor: "", assunto: "" })}>Limpar filtros</Button>
      </div>
      {isLoading ? <LoadingLine /> : null}
      <div className="max-h-[44vh] space-y-2 overflow-y-auto pr-1">
        {filtered.map((record) => (
          <button key={record.id} type="button" className={`w-full rounded-md border p-3 text-left transition-colors hover:bg-muted ${selectedId === record.id ? "border-primary bg-secondary/60" : "bg-background"}`} onClick={() => onSelect(record.id)}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{record.titulo}</p>
                <p className="mt-1 truncate text-xs text-muted-foreground">{record.codigo_referencia}</p>
              </div>
              <span className="shrink-0 rounded-md bg-muted px-2 py-1 text-xs">Nível {record.nivel}</span>
            </div>
            <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{record.ambito_conteudo || record.produtor || "Sem resumo de conteúdo."}</p>
          </button>
        ))}
        {!isLoading && !filtered.length ? <p className="py-8 text-center text-sm text-muted-foreground">Nenhum registro encontrado.</p> : null}
      </div>
    </div>
  );
}

function UnidadeAssociationRow({ unidade, checked, disabled, onToggle }: { unidade: UnidadeAcondicionamento; checked: boolean; disabled: boolean; onToggle: () => void }) {
  return (
    <label className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 transition-colors ${checked ? "border-primary bg-secondary/50" : "bg-background hover:bg-muted"} ${disabled ? "cursor-not-allowed opacity-60" : ""}`}>
      <input type="checkbox" className="mt-1" checked={checked} disabled={disabled} onChange={onToggle} />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <Link2 className="h-4 w-4 text-muted-foreground" />
          {unidade.identificador}
        </span>
        <span className="mt-1 block truncate text-sm">{unidade.titulo}</span>
        <span className="mt-1 block text-xs text-muted-foreground">{unidade.tipo_suporte} - {unidade.tipo_unidade} - {unidade.status}</span>
      </span>
    </label>
  );
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function SelectFilter({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <FilterField label={label}>
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </FilterField>
  );
}

function DateRangeFilter({ label, from, to, onChange }: { label: string; from?: string; to?: string; onChange: (from: string, to: string) => void }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="grid gap-2 sm:grid-cols-2">
        <Input aria-label={`${label} de`} type="date" value={toDateInputValue(from)} onChange={(event) => onChange(startOfDay(event.target.value), to ?? "")} />
        <Input aria-label={`${label} até`} type="date" value={toDateInputValue(to)} onChange={(event) => onChange(from ?? "", endOfDay(event.target.value))} />
      </div>
    </div>
  );
}

function PaginationControls({ currentPage, totalPages, pageSize, displayedCount, total, isLoading, onPageChange, onPageSizeChange }: { currentPage: number; totalPages: number; pageSize: number; displayedCount: number; total: number; isLoading: boolean; onPageChange: (pageIndex: number) => void; onPageSizeChange: (pageSize: number) => void }) {
  const pages = getPaginationItems(currentPage, totalPages);

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2">
      <p className="whitespace-nowrap text-sm text-muted-foreground">
        {displayedCount} registros de {total} | página {currentPage} de {totalPages}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button>
        {pages.map((page, index) =>
          page === "ellipsis" ? (
            <span key={`ellipsis-${index}`} className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground">...</span>
          ) : (
            <Button key={page} type="button" variant={page === currentPage ? "default" : "outline"} size="sm" className="min-w-9 px-2" disabled={isLoading || page === currentPage} onClick={() => onPageChange(page - 1)}>
              {page}
            </Button>
          ),
        )}
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button>
        <Label htmlFor="descricao-unidades-page-size" className="text-sm text-muted-foreground">Por página:</Label>
        <select id="descricao-unidades-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}

function SearchInput({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
      <Input className="pl-9" placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function LoadingLine() {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      Carregando...
    </div>
  );
}

function getPaginationItems(currentPage: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  return sortedPages.flatMap((page, index) => {
    const previousPage = sortedPages[index - 1];

    if (previousPage && page - previousPage > 1) {
      return ["ellipsis" as const, page];
    }

    return [page];
  });
}

function startOfDay(value: string) {
  return value ? `${value}T00:00:00` : "";
}

function endOfDay(value: string) {
  return value ? `${value}T23:59:59` : "";
}

function toDateInputValue(value?: string) {
  return value?.slice(0, 10) ?? "";
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
  nodes: RegistroDescritivoTreeNode[],
  childrenByParent: Record<string, RegistroDescritivoTreeNode[]>,
): RegistroDescritivoTreeNode[] {
  return nodes.map((node) => ({
    ...node,
    children: hydrateTreeNodes(childrenByParent[node.id] ?? node.children, childrenByParent),
  }));
}

function normalize(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
