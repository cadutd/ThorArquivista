"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  Eye,
  HelpCircle,
  Loader2,
  MoreHorizontal,
  Pencil,
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
  consultarRegistrosDescricao,
  criarRegistroDescricao,
  criarRegistrosDescricaoLote,
  duplicarRegistroDescricao,
  excluirRegistroDescricao,
  exportarRegistroEAD2002,
  importarEAD2002,
  listarArvoreDescricao,
  listarRegistrosDescricao,
  listarUnidadesAssociadasDescricao,
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
  const [managementOpen, setManagementOpen] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [treeChildren, setTreeChildren] = useState<Record<string, RegistroDescritivoTreeNode[]>>({});
  const [loadingTreeNodes, setLoadingTreeNodes] = useState<Set<string>>(new Set());
  const [batchOpen, setBatchOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const [moreActionsOpen, setMoreActionsOpen] = useState(false);
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
  const isFormMode = draft !== null;
  const current = draft;
  const selectedParent = selected.data ?? null;
  const formParent = current?.parent_id ? flatRecords.data?.find((item) => item.id === current.parent_id) : null;
  const mutation = useMutation({
    mutationFn: (payload: RegistroDescritivoPayload) =>
      selectedId ? atualizarRegistroDescricao(selectedId, payload) : criarRegistroDescricao(payload),
    onSuccess: async (record) => {
      setSelectedId(record.id);
      setDraft(null);
      setManagementOpen(true);
      await invalidateDescricao(queryClient);
    },
  });
  const duplicate = useMutation({
    mutationFn: (id: string) => duplicarRegistroDescricao(id),
    onSuccess: async (record) => {
      setSelectedId(record.id);
      setManagementOpen(true);
      await invalidateDescricao(queryClient);
    },
  });
  const remove = useMutation({
    mutationFn: ({ id, cascade }: { id: string; cascade: boolean }) => excluirRegistroDescricao(id, cascade),
    onSuccess: async () => {
      setSelectedId(null);
      setDraft(null);
      setManagementOpen(false);
      await invalidateDescricao(queryClient);
    },
  });
  const importEad = useMutation({
    mutationFn: (content: string) => importarEAD2002(content),
    onSuccess: async (result) => {
      setEadMessage(`${result.imported} registro(s) importado(s) de EAD2002.`);
      setSelectedId(result.root_ids[0] ?? null);
      setDraft(null);
      setManagementOpen(Boolean(result.root_ids[0]));
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
    setMoreActionsOpen(false);
    setManagementOpen(true);
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
    setMoreActionsOpen(false);
    setManagementOpen(true);
  };

  const openManagement = (id: string) => {
    setSelectedId(id);
    setDraft(null);
    setMoreActionsOpen(false);
    setManagementOpen(true);
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

      {managementOpen ? (
        <div className="space-y-4">
          <div>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="text-xl font-semibold tracking-normal">Gestão de descrição</h2>
                <p className="text-sm text-muted-foreground">Visualize, edite e execute ações sobre o registro descritivo selecionado.</p>
              </div>
              <Button variant="outline" onClick={() => { setManagementOpen(false); setDraft(null); setMoreActionsOpen(false); }}>
                <ArrowLeft className="h-4 w-4" />
                Voltar para consulta
              </Button>
            </div>
          </div>
          <div>
            <Card>
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <CardTitle>{isFormMode ? current?.titulo || "Registro descritivo" : selectedParent?.titulo || "Registro descritivo"}</CardTitle>
                    <CardDescription>
                      {isFormMode && current
                        ? `Modo de edição - Nível ${current.nivel} - ${nivelLabels[current.nivel]}`
                        : selectedParent
                          ? `Visualização - Nível ${selectedParent.nivel} - ${nivelLabels[selectedParent.nivel]}`
                          : "Selecione um registro ou crie um novo."}
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {isFormMode ? (
                      <Button variant="outline" onClick={() => setDraft(null)}>Cancelar</Button>
                    ) : (
                      <>
                        <Button disabled={!selectedParent} onClick={() => selectedParent && setDraft(toPayload(selectedParent))}><Pencil className="h-4 w-4" />Editar</Button>
                        <Button variant="outline" disabled={!selectedParent || !childLevels[selectedParent.nivel].length} onClick={createChild}><Plus className="h-4 w-4" />Novo filho</Button>
                        <Button variant="outline" disabled={!selectedId} onClick={() => setMoreActionsOpen((value) => !value)}><MoreHorizontal className="h-4 w-4" />Mais ações</Button>
                      </>
                    )}
                  </div>
                </div>
                {!isFormMode && moreActionsOpen ? (
                  <div className="mt-3 flex flex-wrap gap-2 rounded-md border bg-muted/40 p-3">
                    <Button variant="outline" size="sm" disabled={!selectedId} onClick={() => selectedId && duplicate.mutate(selectedId)}><Copy className="h-4 w-4" />Duplicar</Button>
                    <Button variant="outline" size="sm" disabled={!selectedId || exportEad.isPending} onClick={() => selectedId && exportEad.mutate(selectedId)}>
                      {exportEad.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      EAD2002
                    </Button>
                    <Button variant="outline" size="sm" disabled={!selectedId} onClick={() => setMoveOpen(true)}>Mover</Button>
                    <Button variant="outline" size="sm" disabled={!selectedId} onClick={() => setBatchOpen(true)}>Lote</Button>
                    <Button variant="destructive" size="sm" disabled={!selectedId || remove.isPending} onClick={() => selectedId && remove.mutate({ id: selectedId, cascade: window.confirm("Excluir também todos os filhos deste registro?") })}><Trash2 className="h-4 w-4" />Excluir</Button>
                  </div>
                ) : null}
              </CardHeader>
              <CardContent>
                {isFormMode && current ? (
                  <DescricaoForm
                    value={current}
                    parent={formParent}
                    isSaving={mutation.isPending}
                    error={mutation.error?.message}
                    onChange={setDraft}
                    onSave={() => mutation.mutate(current)}
                    onSaveAndNewSibling={saveAndNewSibling}
                    onSaveAndNewChild={saveAndNewChild}
                  />
                ) : selected.isLoading ? (
                  <LoadingLine />
                ) : selectedParent ? (
                  <div className="space-y-6">
                    <DescriptionReadOnly record={selectedParent} />
                    <AssociatedUnitsList registroId={selectedParent.id} records={flatRecords.data ?? []} isRecordsLoading={flatRecords.isLoading} />
                  </div>
                ) : (
                  <div className="flex h-96 items-center justify-center rounded-md border text-sm text-muted-foreground">Selecione um registro pela árvore ou pela consulta detalhada.</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}

      <Tabs defaultValue="arvore" className={managementOpen ? "hidden" : ""}>
        <TabsList>
          <TabsTrigger value="arvore">Árvore Descritiva</TabsTrigger>
          <TabsTrigger value="consulta">Consulta Detalhada</TabsTrigger>
        </TabsList>

        <TabsContent value="arvore">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Árvore descritiva</CardTitle>
                <CardDescription>Navegue pela hierarquia descritiva e abra a gestão do registro quando necessário.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <TreeFilters search={search} levelFilter={levelFilter} onSearch={setSearch} onLevelFilter={setLevelFilter} />
                {tree.isLoading ? <LoadingLine /> : null}
                <div className="max-h-[68vh] overflow-y-auto rounded-md border p-2">
                  {treeNodes.map((node) => (
                    <TreeNode
                      key={node.id}
                      node={node}
                      level={0}
                      selectedId={selectedId}
                      expanded={expanded}
                      loadingIds={loadingTreeNodes}
                      onToggle={toggleTreeNode}
                      onSelect={(id) => { setSelectedId(id); setDraft(null); setMoreActionsOpen(false); }}
                      onOpenManagement={openManagement}
                    />
                  ))}
                  {!tree.isLoading && !(tree.data ?? []).length ? <p className="py-6 text-center text-sm text-muted-foreground">Nenhum registro encontrado.</p> : null}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="consulta">
          <DetailedSearchView
            onOpenManagement={openManagement}
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
  const [openSections, setOpenSections] = useState<Set<string>>(() => new Set([sections[0]?.title ?? ""]));
  const setField = (field: keyof RegistroDescritivoPayload, fieldValue: string | null) => {
    onChange({ ...value, [field]: fieldValue });
  };
  const inherited = (field: keyof RegistroDescritivoPayload) =>
    Boolean(parent && ["produtor", "condicoes_acesso", "idioma", "regras_convencoes"].includes(field) && value[field] === parent[field]);
  const toggleSection = (title: string) => {
    setOpenSections((current) => toggleSet(current, title));
  };

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
        <section key={section.title} className="overflow-hidden rounded-md border">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-3 bg-muted/40 px-4 py-3 text-left text-sm font-semibold hover:bg-muted"
            onClick={() => toggleSection(section.title)}
          >
            <span>{section.title}</span>
            {openSections.has(section.title) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
          {openSections.has(section.title) ? (
            <div className="grid gap-3 p-4 md:grid-cols-2">
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
          ) : null}
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

function DetailedSearchView({ onOpenManagement }: { onOpenManagement: (id: string) => void }) {
  const [filters, setFilters] = useState({
    q: "",
    nivel: "",
    norma: "",
    dataInicialDe: "",
    dataInicialAte: "",
    produtor: "",
    assunto: "",
  });
  const [submittedFilters, setSubmittedFilters] = useState<typeof filters | null>(null);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const query = useQuery({
    queryKey: ["descricao-arquivistica", "consulta-detalhada", submittedFilters, pageIndex, pageSize],
    queryFn: () => consultarRegistrosDescricao({
      q: submittedFilters?.q || undefined,
      nivel: submittedFilters?.nivel || undefined,
      norma: submittedFilters?.norma || undefined,
      data_inicial_de: submittedFilters?.dataInicialDe || undefined,
      data_inicial_ate: submittedFilters?.dataInicialAte || undefined,
      produtor: submittedFilters?.produtor || undefined,
      assunto: submittedFilters?.assunto || undefined,
      limit: pageSize,
      offset: pageIndex * pageSize,
    }),
    enabled: submittedFilters !== null,
  });
  const records = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex, totalPages - 1);
  const submitSearch = () => {
    setSubmittedFilters(filters);
    setPageIndex(0);
  };
  const clearFilters = () => {
    const empty = { q: "", nivel: "", norma: "", dataInicialDe: "", dataInicialAte: "", produtor: "", assunto: "" };
    setFilters(empty);
    setSubmittedFilters(null);
    setPageIndex(0);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Consulta detalhada</CardTitle>
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
              onKeyDown={(event) => {
                if (event.key === "Enter") submitSearch();
              }}
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
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="text-muted-foreground">{submittedFilters ? `${total} registros encontrados` : "Informe os filtros e acione a pesquisa para carregar os registros."}</span>
            <div className="flex flex-wrap gap-2">
              <Button type="button" disabled={query.isFetching} onClick={submitSearch}>
                {query.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Pesquisar
              </Button>
              <Button variant="outline" type="button" onClick={clearFilters}>Limpar filtros</Button>
            </div>
          </div>
          {query.isLoading ? <LoadingLine /> : null}
          <div className="max-h-[62vh] overflow-auto rounded-md border">
            <table className="w-full min-w-[760px] text-sm">
              <thead className="sticky top-0 bg-muted text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Título</th>
                  <th className="px-3 py-2 font-medium">Código</th>
                  <th className="px-3 py-2 font-medium">Nível</th>
                  <th className="px-3 py-2 font-medium">Produtor</th>
                  <th className="px-3 py-2 text-right font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id} className="border-t">
                    <td className="max-w-[280px] px-3 py-3">
                      <p className="truncate font-medium">{record.titulo}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{record.ambito_conteudo || "Sem resumo de conteúdo."}</p>
                    </td>
                    <td className="px-3 py-3 text-muted-foreground">{record.codigo_referencia || "-"}</td>
                    <td className="px-3 py-3">Nível {record.nivel}</td>
                    <td className="max-w-[220px] px-3 py-3 text-muted-foreground">
                      <span className="block truncate">{record.produtor || "-"}</span>
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Button variant="outline" size="icon" title="Visualizar descrição" aria-label={`Visualizar ${record.titulo}`} onClick={() => onOpenManagement(record.id)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!submittedFilters ? <p className="py-8 text-center text-sm text-muted-foreground">Nenhuma pesquisa realizada.</p> : null}
            {submittedFilters && !query.isLoading && !records.length ? <p className="py-8 text-center text-sm text-muted-foreground">Nenhum registro encontrado.</p> : null}
          </div>
          {submittedFilters ? (
            <DetailedSearchPagination
              currentPage={currentPage + 1}
              totalPages={totalPages}
              pageSize={pageSize}
              displayedCount={records.length}
              total={total}
              isLoading={query.isFetching}
              onPageChange={setPageIndex}
              onPageSizeChange={(value) => {
                setPageSize(value);
                setPageIndex(0);
              }}
            />
          ) : null}
          {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailedSearchPagination({
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
      <p className="text-sm text-muted-foreground">{displayedCount} registros de {total} | página {currentPage} de {totalPages}</p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button>
        <Label htmlFor="descricao-consulta-page-size" className="text-sm text-muted-foreground">Por página:</Label>
        <select id="descricao-consulta-page-size" className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
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

function AssociatedUnitsList({ registroId, records, isRecordsLoading }: { registroId: string; records: RegistroDescritivo[]; isRecordsLoading: boolean }) {
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [shouldLoad, setShouldLoad] = useState(false);
  const registroIds = useMemo(() => getDescendantRecordIds(records, registroId), [records, registroId]);
  const query = useQuery({
    queryKey: ["descricao-arquivistica", "registro", registroId, "unidades-associadas-recursivas", registroIds],
    queryFn: async () => {
      const results = await Promise.all(registroIds.map((id) => listarUnidadesAssociadasDescricao(id)));
      const unique = new Map<number, UnidadeAcondicionamento>();
      for (const result of results) {
        for (const unidade of result.unidades) {
          unique.set(unidade.id, unidade);
        }
      }
      return Array.from(unique.values());
    },
    enabled: shouldLoad && Boolean(registroId) && !isRecordsLoading,
  });
  const unidades = query.data ?? [];
  const physicalCount = unidades.filter((unidade) => unidade.tipo_suporte === "FISICO" || unidade.tipo_suporte === "HIBRIDO").length;
  const digitalCount = unidades.filter((unidade) => unidade.tipo_suporte === "DIGITAL" || unidade.tipo_suporte === "HIBRIDO").length;
  const total = unidades.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex, totalPages - 1);
  const pageItems: UnidadeAcondicionamento[] = unidades.slice(currentPage * pageSize, currentPage * pageSize + pageSize);

  useEffect(() => {
    setPageIndex(0);
  }, [registroId, pageSize, registroIds.length]);

  useEffect(() => {
    setShouldLoad(false);
  }, [registroId]);

  return (
    <section className="space-y-3">
      <div className="flex flex-col gap-1">
        <h3 className="text-sm font-semibold">Unidades de acondicionamento associadas</h3>
        <p className="text-xs text-muted-foreground">Listagem paginada das unidades vinculadas a esta descrição arquivística e a todas as suas descrições descendentes.</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outline"
          disabled={isRecordsLoading || query.isFetching}
          onClick={() => shouldLoad ? query.refetch() : setShouldLoad(true)}
        >
          {query.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {shouldLoad ? "Atualizar unidades" : "Carregar unidades"}
        </Button>
        {isRecordsLoading ? <span className="text-sm text-muted-foreground">Preparando hierarquia de descrições...</span> : null}
      </div>
      {shouldLoad && (query.isLoading || isRecordsLoading) ? <LoadingLine /> : null}
      {shouldLoad && query.data ? (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <SummaryMetric label="Físicas" value={physicalCount} />
            <SummaryMetric label="Digitais" value={digitalCount} />
            <SummaryMetric label="Total" value={total} />
          </div>
          <div className="overflow-auto rounded-md border">
            <table className="w-full min-w-[760px] text-sm">
              <thead className="bg-muted text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Identificador</th>
                  <th className="px-3 py-2 font-medium">Título</th>
                  <th className="px-3 py-2 font-medium">Tipo</th>
                  <th className="px-3 py-2 font-medium">Suporte</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Acesso</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((unidade) => (
                  <tr key={unidade.id} className="border-t">
                    <td className="px-3 py-3 font-medium">{unidade.identificador}</td>
                    <td className="max-w-[280px] px-3 py-3">
                      <p className="truncate">{unidade.titulo}</p>
                      {unidade.descricao ? <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{unidade.descricao}</p> : null}
                    </td>
                    <td className="px-3 py-3">{formatEnum(unidade.tipo_unidade)}</td>
                    <td className="px-3 py-3">{formatEnum(unidade.tipo_suporte)}</td>
                    <td className="px-3 py-3">{formatEnum(unidade.status)}</td>
                    <td className="px-3 py-3">{formatEnum(unidade.nivel_acesso)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!query.isLoading && !isRecordsLoading && !pageItems.length ? <p className="py-8 text-center text-sm text-muted-foreground">Nenhuma unidade associada nesta descrição ou em suas descendentes.</p> : null}
          </div>
          <AssociatedUnitsPagination
            currentPage={currentPage + 1}
            totalPages={totalPages}
            pageSize={pageSize}
            displayedCount={pageItems.length}
            total={total}
            isLoading={query.isFetching}
            onPageChange={setPageIndex}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPageIndex(0);
            }}
          />
        </>
      ) : null}
      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
    </section>
  );
}

function SummaryMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function AssociatedUnitsPagination({
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
      <p className="text-sm text-muted-foreground">{displayedCount} unidades de {total} | página {currentPage} de {totalPages}</p>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>Primeira</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>Anterior</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>Próxima</Button>
        <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>Última</Button>
        <Label htmlFor="descricao-unidades-associadas-page-size" className="text-sm text-muted-foreground">Por página:</Label>
        <select
          id="descricao-unidades-associadas-page-size"
          className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
      </div>
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

function TreeNode({ node, level, selectedId, expanded, loadingIds, onToggle, onSelect, onOpenManagement }: { node: RegistroDescritivoTreeNode; level: number; selectedId: string | null; expanded: Set<string>; loadingIds: Set<string>; onToggle: (node: RegistroDescritivoTreeNode) => void; onSelect: (id: string) => void; onOpenManagement: (id: string) => void }) {
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
        <Button variant="outline" size="icon" className="h-8 w-8" title="Visualizar descrição" aria-label={`Visualizar ${node.titulo}`} onClick={() => onOpenManagement(node.id)}>
          <Eye className="h-4 w-4" />
        </Button>
      </div>
      {hasChildren && isOpen ? node.children.map((child) => <TreeNode key={child.id} node={child} level={level + 1} selectedId={selectedId} expanded={expanded} loadingIds={loadingIds} onToggle={onToggle} onSelect={onSelect} onOpenManagement={onOpenManagement} />) : null}
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

function getDescendantRecordIds(records: RegistroDescritivo[], rootId: string) {
  const childrenByParent = new Map<string, RegistroDescritivo[]>();
  for (const record of records) {
    if (!record.parent_id) continue;
    const children = childrenByParent.get(record.parent_id) ?? [];
    children.push(record);
    childrenByParent.set(record.parent_id, children);
  }

  const ids: string[] = [];
  const stack = [rootId];
  const visited = new Set<string>();
  while (stack.length) {
    const id = stack.pop();
    if (!id || visited.has(id)) continue;
    visited.add(id);
    ids.push(id);
    for (const child of childrenByParent.get(id) ?? []) {
      stack.push(child.id);
    }
  }
  return ids;
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

function formatEnum(value?: string | null) {
  if (!value) return "-";
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalize(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
