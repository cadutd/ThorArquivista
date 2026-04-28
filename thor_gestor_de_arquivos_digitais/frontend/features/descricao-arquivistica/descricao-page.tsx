"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  HelpCircle,
  Loader2,
  Plus,
  Save,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  atualizarRegistroDescricao,
  criarRegistroDescricao,
  criarRegistrosDescricaoLote,
  duplicarRegistroDescricao,
  excluirRegistroDescricao,
  exportarRegistroEAD2002,
  importarEAD2002,
  listarArvoreDescricao,
  listarRegistrosDescricao,
  moverRegistroDescricao,
  obterRegistroDescricao,
} from "@/lib/api/descricao-arquivistica";
import { getHelp } from "@/features/descricao-arquivistica/help-texts";
import type {
  NivelDescricao,
  NormaDescricao,
  RegistroDescritivo,
  RegistroDescritivoPayload,
  RegistroDescritivoTreeNode,
} from "@/types/descricao-arquivistica";

const nivelLabels: Record<NivelDescricao, string> = {
  "1": "Fundo / Coleção",
  "2": "Seção",
  "2.5": "Subseção",
  "3": "Série",
  "3.5": "Subsérie",
  "4": "Dossiê / Processo",
  "5": "Item Documental",
};

const childLevels: Record<NivelDescricao, NivelDescricao[]> = {
  "1": ["2"],
  "2": ["2.5", "3"],
  "2.5": ["3"],
  "3": ["3.5", "4"],
  "3.5": ["4"],
  "4": ["5"],
  "5": [],
};

const emptyPayload: RegistroDescritivoPayload = {
  parent_id: null,
  nivel: "1",
  norma: "NOBRADE",
  codigo_referencia: "",
  titulo: "",
  data_inicial: null,
  data_final: null,
  dimensao: "",
  suporte: "",
  produtor: "",
  historia_administrativa: "",
  historia_arquivistica: "",
  procedencia: "",
  ambito_conteudo: "",
  avaliacao_eliminacao: "",
  incorporacoes: "",
  sistema_arranjo: "",
  condicoes_acesso: "",
  condicoes_reproducao: "",
  idioma: "",
  caracteristicas_tecnicas: "",
  originais: "",
  copias: "",
  unidades_relacionadas: "",
  publicacoes: "",
  notas: "",
  arquivista_responsavel: "",
  regras_convencoes: "",
  data_descricao: null,
  assuntos: "",
  pessoas: "",
  locais: "",
  entidades: "",
  eventos: "",
};

const sections: Array<{
  title: string;
  fields: Array<{ key: keyof RegistroDescritivoPayload; label: string; type?: "text" | "textarea" | "date" }>;
}> = [
  {
    title: "Área de Identificação",
    fields: [
      { key: "codigo_referencia", label: "Código de referência" },
      { key: "titulo", label: "Título" },
      { key: "data_inicial", label: "Data inicial", type: "date" },
      { key: "data_final", label: "Data final", type: "date" },
      { key: "dimensao", label: "Dimensão" },
      { key: "suporte", label: "Suporte" },
    ],
  },
  {
    title: "Contextualização",
    fields: [
      { key: "produtor", label: "Produtor" },
      { key: "historia_administrativa", label: "História administrativa", type: "textarea" },
      { key: "historia_arquivistica", label: "História arquivística", type: "textarea" },
      { key: "procedencia", label: "Procedência", type: "textarea" },
    ],
  },
  {
    title: "Conteúdo e Estrutura",
    fields: [
      { key: "ambito_conteudo", label: "Âmbito e conteúdo", type: "textarea" },
      { key: "avaliacao_eliminacao", label: "Avaliação, eliminação e temporalidade", type: "textarea" },
      { key: "incorporacoes", label: "Incorporações", type: "textarea" },
      { key: "sistema_arranjo", label: "Sistema de arranjo", type: "textarea" },
    ],
  },
  {
    title: "Acesso e Uso",
    fields: [
      { key: "condicoes_acesso", label: "Condições de acesso", type: "textarea" },
      { key: "condicoes_reproducao", label: "Condições de reprodução", type: "textarea" },
      { key: "idioma", label: "Idioma" },
      { key: "caracteristicas_tecnicas", label: "Características técnicas", type: "textarea" },
    ],
  },
  {
    title: "Fontes Relacionadas",
    fields: [
      { key: "originais", label: "Originais", type: "textarea" },
      { key: "copias", label: "Cópias", type: "textarea" },
      { key: "unidades_relacionadas", label: "Unidades relacionadas", type: "textarea" },
      { key: "publicacoes", label: "Publicações", type: "textarea" },
    ],
  },
  {
    title: "Notas, Controle e Indexação",
    fields: [
      { key: "notas", label: "Notas", type: "textarea" },
      { key: "arquivista_responsavel", label: "Arquivista responsável" },
      { key: "regras_convencoes", label: "Regras e convenções", type: "textarea" },
      { key: "data_descricao", label: "Data da descrição", type: "date" },
      { key: "assuntos", label: "Assuntos" },
      { key: "pessoas", label: "Pessoas" },
      { key: "locais", label: "Locais" },
      { key: "entidades", label: "Entidades" },
      { key: "eventos", label: "Eventos" },
    ],
  },
];

export function DescricaoArquivisticaPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<RegistroDescritivoPayload | null>(null);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [detailSelectionId, setDetailSelectionId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [treeChildren, setTreeChildren] = useState<Record<string, RegistroDescritivoTreeNode[]>>({});
  const [loadingTreeNodes, setLoadingTreeNodes] = useState<Set<string>>(new Set());
  const [batchOpen, setBatchOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const [eadMessage, setEadMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const tree = useQuery({
    queryKey: ["descricao-arquivistica", "arvore", search, levelFilter],
    queryFn: () => listarArvoreDescricao({ q: search, nivel: levelFilter }),
  });
  const treeNodes = useMemo(
    () => hydrateTreeNodes(tree.data ?? [], treeChildren),
    [tree.data, treeChildren],
  );
  const flatRecords = useQuery({
    queryKey: ["descricao-arquivistica", "registros"],
    queryFn: () => listarRegistrosDescricao(),
  });
  const selected = useQuery({
    queryKey: ["descricao-arquivistica", "registro", selectedId],
    queryFn: () => selectedId ? obterRegistroDescricao(selectedId) : Promise.resolve(null),
    enabled: Boolean(selectedId),
  });
  const current = draft ?? (selected.data ? toPayload(selected.data) : null);
  const selectedParent = selected.data ?? null;
  const mutation = useMutation({
    mutationFn: (payload: RegistroDescritivoPayload) =>
      selectedId ? atualizarRegistroDescricao(selectedId, payload) : criarRegistroDescricao(payload),
    onSuccess: async (record) => {
      setSelectedId(record.id);
      setDraft(null);
      await invalidateDescricao(queryClient);
    },
  });
  const duplicate = useMutation({
    mutationFn: (id: string) => duplicarRegistroDescricao(id),
    onSuccess: async (record) => {
      setSelectedId(record.id);
      await invalidateDescricao(queryClient);
    },
  });
  const remove = useMutation({
    mutationFn: ({ id, cascade }: { id: string; cascade: boolean }) => excluirRegistroDescricao(id, cascade),
    onSuccess: async () => {
      setSelectedId(null);
      setDraft(null);
      await invalidateDescricao(queryClient);
    },
  });
  const importEad = useMutation({
    mutationFn: (content: string) => importarEAD2002(content),
    onSuccess: async (result) => {
      setEadMessage(`${result.imported} registro(s) importado(s) de EAD2002.`);
      setSelectedId(result.root_ids[0] ?? null);
      setDraft(null);
      await invalidateDescricao(queryClient);
    },
  });
  const exportEad = useMutation({
    mutationFn: async (id: string) => {
      const blob = await exportarRegistroEAD2002(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ead2002-${id}.xml`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
    onSuccess: () => setEadMessage("Arquivo EAD2002 exportado."),
  });

  const createRoot = () => {
    setSelectedId(null);
    setDraft({ ...emptyPayload, nivel: "1", parent_id: null, norma: "NOBRADE" });
  };

  const createChild = () => {
    if (!selectedParent) return;
    const nextLevel = childLevels[selectedParent.nivel][0];
    if (!nextLevel) return;
    setSelectedId(null);
    setDraft({
      ...emptyPayload,
      parent_id: selectedParent.id,
      nivel: nextLevel,
      norma: selectedParent.norma,
      produtor: selectedParent.produtor ?? "",
      condicoes_acesso: selectedParent.condicoes_acesso ?? "",
      idioma: selectedParent.idioma ?? "",
      regras_convencoes: selectedParent.regras_convencoes ?? "",
    });
  };

  const saveAndNewSibling = async () => {
    if (!current) return;
    const record = await mutation.mutateAsync(current);
    setSelectedId(null);
    setDraft({ ...emptyPayload, parent_id: record.parent_id ?? null, nivel: record.nivel, norma: record.norma });
  };

  const saveAndNewChild = async () => {
    if (!current) return;
    const record = await mutation.mutateAsync(current);
    const nextLevel = childLevels[record.nivel][0];
    if (nextLevel) {
      setSelectedId(null);
      setDraft({ ...emptyPayload, parent_id: record.id, nivel: nextLevel, norma: record.norma });
    }
  };

  const handleEadFile = async (file?: File) => {
    if (!file) return;
    setEadMessage(null);
    importEad.mutate(await file.text());
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  useEffect(() => {
    setExpanded(new Set());
    setTreeChildren({});
    setLoadingTreeNodes(new Set());
  }, [search, levelFilter]);

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
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Descrição Arquivística</h1>
          <p className="text-sm text-muted-foreground">Registros descritivos multinível aderentes à NOBRADE, ISAD(G) e EAD2002.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".xml,application/xml,text/xml"
            className="hidden"
            onChange={(event) => handleEadFile(event.target.files?.[0])}
          />
          <Button variant="outline" disabled={importEad.isPending} onClick={() => fileInputRef.current?.click()}>
            {importEad.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Importar EAD2002
          </Button>
          <Button onClick={createRoot}><Plus className="h-4 w-4" />Novo Fundo/Coleção</Button>
        </div>
      </div>
      {eadMessage || importEad.error || exportEad.error ? (
        <p className={importEad.error || exportEad.error ? "text-sm text-destructive" : "text-sm text-muted-foreground"}>
          {importEad.error?.message || exportEad.error?.message || eadMessage}
        </p>
      ) : null}

      <Tabs defaultValue="edicao">
        <TabsList>
          <TabsTrigger value="edicao">Edição</TabsTrigger>
          <TabsTrigger value="consulta">Consulta detalhada</TabsTrigger>
        </TabsList>

        <TabsContent value="edicao">
          <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle>Árvore descritiva</CardTitle>
                <CardDescription>Navegue, filtre e selecione registros.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <TreeFilters search={search} levelFilter={levelFilter} onSearch={setSearch} onLevelFilter={setLevelFilter} />
                {tree.isLoading ? <LoadingLine /> : null}
                <div className="max-h-[68vh] overflow-y-auto pr-1">
                  {treeNodes.map((node) => (
                    <TreeNode
                      key={node.id}
                      node={node}
                      level={0}
                      selectedId={selectedId}
                      expanded={expanded}
                      loadingIds={loadingTreeNodes}
                      onToggle={toggleTreeNode}
                      onSelect={(id) => { setSelectedId(id); setDraft(null); }}
                    />
                  ))}
                  {!tree.isLoading && !(tree.data ?? []).length ? <p className="py-6 text-center text-sm text-muted-foreground">Nenhum registro encontrado.</p> : null}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <CardTitle>{current?.titulo || "Registro descritivo"}</CardTitle>
                    <CardDescription>{current ? `Nível ${current.nivel} - ${nivelLabels[current.nivel]}` : "Selecione um registro ou crie um novo."}</CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" disabled={!selectedParent || !childLevels[selectedParent.nivel].length} onClick={createChild}><Plus className="h-4 w-4" />Filho</Button>
                    <Button variant="outline" disabled={!selectedId} onClick={() => selectedId && duplicate.mutate(selectedId)}><Copy className="h-4 w-4" />Duplicar</Button>
                    <Button variant="outline" disabled={!selectedId || exportEad.isPending} onClick={() => selectedId && exportEad.mutate(selectedId)}>
                      {exportEad.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      EAD2002
                    </Button>
                    <Button variant="outline" disabled={!selectedId} onClick={() => setMoveOpen(true)}>Mover</Button>
                    <Button variant="outline" disabled={!selectedId} onClick={() => setBatchOpen(true)}>Lote</Button>
                    <Button variant="destructive" disabled={!selectedId || remove.isPending} onClick={() => selectedId && remove.mutate({ id: selectedId, cascade: window.confirm("Excluir também todos os filhos deste registro?") })}><Trash2 className="h-4 w-4" />Excluir</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {current ? (
                  <DescricaoForm
                    value={current}
                    parent={selectedParent?.parent_id ? flatRecords.data?.find((item) => item.id === selectedParent.parent_id) : null}
                    isSaving={mutation.isPending}
                    error={mutation.error?.message}
                    onChange={setDraft}
                    onSave={() => mutation.mutate(current)}
                    onSaveAndNewSibling={saveAndNewSibling}
                    onSaveAndNewChild={saveAndNewChild}
                  />
                ) : (
                  <div className="flex h-96 items-center justify-center rounded-md border text-sm text-muted-foreground">Selecione um nó na árvore para editar.</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="consulta">
          <DetailedSearchView
            records={flatRecords.data ?? []}
            isLoading={flatRecords.isLoading}
            selectedId={detailSelectionId}
            onSelect={setDetailSelectionId}
          />
        </TabsContent>
      </Tabs>

      <BatchDialog
        open={batchOpen}
        onOpenChange={setBatchOpen}
        parent={selectedParent}
        onDone={async () => {
          setBatchOpen(false);
          await invalidateDescricao(queryClient);
        }}
      />
      <MoveDialog
        open={moveOpen}
        onOpenChange={setMoveOpen}
        record={selectedParent}
        records={flatRecords.data ?? []}
        onMove={async (parentId) => {
          if (!selectedParent) return;
          await moverRegistroDescricao(selectedParent.id, parentId);
          setMoveOpen(false);
          await invalidateDescricao(queryClient);
        }}
      />
    </div>
  );
}

function DescricaoForm({
  value,
  parent,
  isSaving,
  error,
  onChange,
  onSave,
  onSaveAndNewSibling,
  onSaveAndNewChild,
}: {
  value: RegistroDescritivoPayload;
  parent?: RegistroDescritivo | null;
  isSaving: boolean;
  error?: string;
  onChange: (value: RegistroDescritivoPayload) => void;
  onSave: () => void;
  onSaveAndNewSibling: () => void;
  onSaveAndNewChild: () => void;
}) {
  const setField = (field: keyof RegistroDescritivoPayload, fieldValue: string | null) => {
    onChange({ ...value, [field]: fieldValue });
  };
  const inherited = (field: keyof RegistroDescritivoPayload) =>
    Boolean(parent && ["produtor", "condicoes_acesso", "idioma", "regras_convencoes"].includes(field) && value[field] === parent[field]);

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-3">
        <FieldShell field="norma" label="Norma" norma={value.norma}>
          <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={value.norma} onChange={(event) => setField("norma", event.target.value as NormaDescricao)}>
            <option value="NOBRADE">NOBRADE</option>
            <option value="ISAD_G">ISAD(G)</option>
            <option value="EAD2002">EAD2002</option>
          </select>
        </FieldShell>
        <FieldShell field="nivel" label="Nível de descrição" norma={value.norma}>
          <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={value.nivel} onChange={(event) => setField("nivel", event.target.value as NivelDescricao)}>
            {Object.entries(nivelLabels).map(([nivel, label]) => <option key={nivel} value={nivel}>Nível {nivel} - {label}</option>)}
          </select>
        </FieldShell>
        <div className="rounded-md border p-3 text-sm">
          <p className="font-medium">Não repetição</p>
          <p className="mt-1 text-xs text-muted-foreground">Campos herdados são preenchidos para facilitar, mas podem ser personalizados.</p>
        </div>
      </div>

      {sections.map((section) => (
        <section key={section.title} className="space-y-3">
          <h3 className="border-b pb-2 text-sm font-semibold">{section.title}</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {section.fields.map((field) => (
              <FieldShell key={field.key} field={field.key} label={field.label} norma={value.norma} inherited={inherited(field.key)}>
                {field.type === "textarea" ? (
                  <textarea
                    className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={String(value[field.key] ?? "")}
                    onChange={(event) => setField(field.key, event.target.value)}
                  />
                ) : (
                  <Input
                    type={field.type ?? "text"}
                    value={dateInputValue(value[field.key])}
                    onChange={(event) => setField(field.key, event.target.value || null)}
                  />
                )}
              </FieldShell>
            ))}
          </div>
        </section>
      ))}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <div className="flex flex-wrap gap-2">
        <Button disabled={isSaving} onClick={onSave}>{isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}Salvar</Button>
        <Button variant="outline" disabled={isSaving} onClick={onSaveAndNewSibling}>Salvar e novo irmão</Button>
        <Button variant="outline" disabled={isSaving || !childLevels[value.nivel].length} onClick={onSaveAndNewChild}>Salvar e novo filho</Button>
      </div>
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
        {Object.entries(nivelLabels).map(([value, label]) => <option key={value} value={value}>Nível {value} - {label}</option>)}
      </select>
    </>
  );
}

function DetailedSearchView({
  records,
  isLoading,
  selectedId,
  onSelect,
}: {
  records: RegistroDescritivo[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [filters, setFilters] = useState({
    q: "",
    nivel: "",
    norma: "",
    dataInicialDe: "",
    dataInicialAte: "",
    produtor: "",
    assunto: "",
  });
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
        (!filters.dataInicialDe || (record.data_inicial ?? "") >= filters.dataInicialDe) &&
        (!filters.dataInicialAte || (record.data_inicial ?? "") <= filters.dataInicialAte) &&
        (!produtor || normalize(record.produtor ?? "").includes(produtor)) &&
        (!assunto || normalize(record.assuntos ?? "").includes(assunto))
      );
    });
  }, [records, filters]);
  const selected = filtered.find((record) => record.id === selectedId) ?? filtered[0] ?? null;

  return (
    <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Consulta</CardTitle>
          <CardDescription>Pesquise registros por elementos descritivos e filtros normativos.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Buscar por título, código, conteúdo, índice..."
              value={filters.q}
              onChange={(event) => setFilters({ ...filters, q: event.target.value })}
            />
          </div>
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
            <Input type="date" value={filters.dataInicialDe} onChange={(event) => setFilters({ ...filters, dataInicialDe: event.target.value })} />
            <Input type="date" value={filters.dataInicialAte} onChange={(event) => setFilters({ ...filters, dataInicialAte: event.target.value })} />
            <Input placeholder="Produtor" value={filters.produtor} onChange={(event) => setFilters({ ...filters, produtor: event.target.value })} />
            <Input placeholder="Assunto" value={filters.assunto} onChange={(event) => setFilters({ ...filters, assunto: event.target.value })} />
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{filtered.length} registros encontrados</span>
            <Button variant="outline" size="sm" onClick={() => setFilters({ q: "", nivel: "", norma: "", dataInicialDe: "", dataInicialAte: "", produtor: "", assunto: "" })}>Limpar filtros</Button>
          </div>
          {isLoading ? <LoadingLine /> : null}
          <div className="max-h-[56vh] space-y-2 overflow-y-auto pr-1">
            {filtered.map((record) => (
              <button
                key={record.id}
                type="button"
                className={`w-full rounded-md border p-3 text-left transition-colors hover:bg-muted ${selected?.id === record.id ? "border-primary bg-secondary/60" : "bg-background"}`}
                onClick={() => onSelect(record.id)}
              >
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
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{selected?.titulo ?? "Ficha descritiva"}</CardTitle>
          <CardDescription>{selected ? `${selected.codigo_referencia} - Nível ${selected.nivel} - ${nivelLabels[selected.nivel]}` : "Selecione um resultado para consultar."}</CardDescription>
        </CardHeader>
        <CardContent>
          {selected ? <DescriptionReadOnly record={selected} /> : <div className="flex h-96 items-center justify-center rounded-md border text-sm text-muted-foreground">Nenhum registro selecionado.</div>}
        </CardContent>
      </Card>
    </div>
  );
}

function DescriptionReadOnly({ record }: { record: RegistroDescritivo }) {
  return (
    <div className="space-y-5">
      <section className="grid gap-3 md:grid-cols-4">
        <ReadOnlyField label="Norma" value={record.norma === "ISAD_G" ? "ISAD(G)" : record.norma} />
        <ReadOnlyField label="Nível" value={`Nível ${record.nivel} - ${nivelLabels[record.nivel]}`} />
        <ReadOnlyField label="Data inicial" value={formatDate(record.data_inicial)} />
        <ReadOnlyField label="Data final" value={formatDate(record.data_final)} />
      </section>
      {sections.map((section) => (
        <section key={section.title} className="space-y-3">
          <h3 className="border-b pb-2 text-sm font-semibold">{section.title}</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {section.fields.map((field) => (
              <ReadOnlyField key={field.key} label={field.label} value={readRecordValue(record, field.key)} multiline={field.type === "textarea"} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function ReadOnlyField({ label, value, multiline }: { label: string; value?: string | null; multiline?: boolean }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className={`mt-1 text-sm ${multiline ? "whitespace-pre-wrap" : ""}`}>{value || "-"}</p>
    </div>
  );
}

function FieldShell({ field, label, norma, inherited, children }: { field: string; label: string; norma: NormaDescricao; inherited?: boolean; children: React.ReactNode }) {
  const help = getHelp(norma, field);
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label>{label}</Label>
        <span className="group relative inline-flex">
          <HelpCircle className="h-4 w-4 text-muted-foreground" />
          <span className="pointer-events-none absolute left-0 top-5 z-20 hidden w-80 rounded-md border bg-background p-3 text-xs shadow-lg group-hover:block">
            <span className="block font-semibold">{help.oficial}</span>
            <span className="mt-1 block">{help.finalidade}</span>
            <span className="mt-1 block text-muted-foreground">{help.regra}</span>
            <span className="mt-1 block italic">Exemplo: {help.exemplo}</span>
          </span>
        </span>
        {inherited ? <span className="rounded-md bg-secondary px-2 py-1 text-xs text-secondary-foreground">herdado do nível superior</span> : null}
      </div>
      {children}
    </div>
  );
}

function TreeNode({ node, level, selectedId, expanded, loadingIds, onToggle, onSelect }: { node: RegistroDescritivoTreeNode; level: number; selectedId: string | null; expanded: Set<string>; loadingIds: Set<string>; onToggle: (node: RegistroDescritivoTreeNode) => void; onSelect: (id: string) => void }) {
  const hasChildren = node.has_children;
  const isOpen = expanded.has(node.id) || level < 1;
  const isLoading = loadingIds.has(node.id);
  return (
    <div>
      <div className="flex items-center gap-1" style={{ paddingLeft: level * 12 }}>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => hasChildren && onToggle(node)}>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : hasChildren ? (isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />) : <span className="h-4 w-4" />}
        </Button>
        <button type="button" className={`min-w-0 flex-1 rounded-md px-2 py-1 text-left text-sm hover:bg-muted ${selectedId === node.id ? "bg-secondary text-secondary-foreground" : ""}`} onClick={() => onSelect(node.id)}>
          <span className="block truncate font-medium">{node.titulo}</span>
          <span className="block truncate text-xs text-muted-foreground">Nível {node.nivel} - {node.codigo_referencia}</span>
        </button>
      </div>
      {hasChildren && isOpen ? node.children.map((child) => <TreeNode key={child.id} node={child} level={level + 1} selectedId={selectedId} expanded={expanded} loadingIds={loadingIds} onToggle={onToggle} onSelect={onSelect} />) : null}
    </div>
  );
}

function BatchDialog({ open, onOpenChange, parent, onDone }: { open: boolean; onOpenChange: (open: boolean) => void; parent: RegistroDescritivo | null; onDone: () => void }) {
  const [rows, setRows] = useState([{ titulo: "", data_inicial: "", data_final: "", codigo_referencia: "" }]);
  const mutation = useMutation({
    mutationFn: () => {
      if (!parent) throw new Error("Selecione um registro pai.");
      const nivel = childLevels[parent.nivel][0];
      if (!nivel) throw new Error("Este nível não permite filhos.");
      return criarRegistrosDescricaoLote(parent.id, rows.filter((row) => row.titulo || row.codigo_referencia).map((row) => ({
        ...emptyPayload,
        parent_id: parent.id,
        nivel,
        norma: parent.norma,
        titulo: row.titulo,
        codigo_referencia: row.codigo_referencia,
        data_inicial: row.data_inicial || null,
        data_final: row.data_final || null,
      })));
    },
    onSuccess: onDone,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle>Adição rápida em lote</DialogTitle>
          <DialogDescription>Crie múltiplos filhos do registro selecionado sem trocar de tela.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {rows.map((row, index) => (
            <div key={index} className="grid gap-2 md:grid-cols-[1fr_140px_140px_180px]">
              <Input placeholder="Título" value={row.titulo} onChange={(event) => setRows(updateRow(rows, index, "titulo", event.target.value))} />
              <Input type="date" value={row.data_inicial} onChange={(event) => setRows(updateRow(rows, index, "data_inicial", event.target.value))} />
              <Input type="date" value={row.data_final} onChange={(event) => setRows(updateRow(rows, index, "data_final", event.target.value))} />
              <Input placeholder="Código Ref." value={row.codigo_referencia} onChange={(event) => setRows(updateRow(rows, index, "codigo_referencia", event.target.value))} />
            </div>
          ))}
          {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setRows([...rows, { titulo: "", data_inicial: "", data_final: "", codigo_referencia: "" }])}>Adicionar linha</Button>
            <Button disabled={mutation.isPending || !parent} onClick={() => mutation.mutate()}>Salvar todos</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function MoveDialog({ open, onOpenChange, record, records, onMove }: { open: boolean; onOpenChange: (open: boolean) => void; record: RegistroDescritivo | null; records: RegistroDescritivo[]; onMove: (parentId: string) => void }) {
  const [parentId, setParentId] = useState("");
  const candidates = useMemo(() => records.filter((item) => item.id !== record?.id && record && childLevels[item.nivel].includes(record.nivel)), [records, record]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Mover registro</DialogTitle>
          <DialogDescription>Selecione um novo pai compatível com o nível do registro.</DialogDescription>
        </DialogHeader>
        <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={parentId} onChange={(event) => setParentId(event.target.value)}>
          <option value="">Selecione o novo pai</option>
          {candidates.map((item) => <option key={item.id} value={item.id}>Nível {item.nivel} - {item.titulo}</option>)}
        </select>
        <Button disabled={!parentId} onClick={() => onMove(parentId)}>Mover</Button>
      </DialogContent>
    </Dialog>
  );
}

function LoadingLine() {
  return <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Carregando...</div>;
}

function toPayload(record: RegistroDescritivo): RegistroDescritivoPayload {
  const { id: _id, has_children: _hasChildren, created_at: _created, updated_at: _updated, ...payload } = record;
  return payload;
}

function toggleSet(set: Set<string>, id: string) {
  const next = new Set(set);
  if (next.has(id)) next.delete(id);
  else next.add(id);
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

async function invalidateDescricao(queryClient: ReturnType<typeof useQueryClient>) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["descricao-arquivistica", "arvore"] }),
    queryClient.invalidateQueries({ queryKey: ["descricao-arquivistica", "registros"] }),
  ]);
}

function updateRow<T extends Record<string, string>>(rows: T[], index: number, field: keyof T, value: string) {
  return rows.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: value } : row);
}

function dateInputValue(value: unknown) {
  if (!value) return "";
  return String(value).slice(0, 10);
}

function readRecordValue(record: RegistroDescritivo, field: keyof RegistroDescritivoPayload) {
  const value = record[field];
  if (!value) return "";
  if (field === "data_inicial" || field === "data_final" || field === "data_descricao") {
    return formatDate(String(value));
  }
  return String(value);
}

function formatDate(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR").format(date);
}

function normalize(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
