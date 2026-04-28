"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit, Eye, GitBranch, Loader2, Map as MapIcon, Plus, RefreshCw, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  EmptyState,
  MovementTimeline,
  OccupancyCard,
  OccupancyProgressBar,
  StoragePageHeader,
  StorageStatusBadge,
} from "@/features/armazenamento/storage-components";
import {
  storageLabel,
  tipoCompartimentoOptions,
  tipoEstruturaOptions,
  tipoLocalOptions,
  tipoPosicaoOptions,
  tipoZonaOptions,
} from "@/features/armazenamento/storage-labels";
import {
  atualizarCompartimento,
  atualizarEstrutura,
  atualizarLocalGuarda,
  atualizarPosicao,
  atualizarZonaGuarda,
  criarCompartimento,
  criarEstrutura,
  criarLocalGuarda,
  criarPosicao,
  criarZonaGuarda,
  excluirCompartimento,
  excluirEstrutura,
  excluirLocalGuarda,
  excluirPosicao,
  excluirZonaGuarda,
  gerarTopografiaZona,
  listarCompartimentos,
  listarEstruturas,
  listarLocaisGuarda,
  listarMovimentacoes,
  listarPosicoes,
  listarPosicoesLivres,
  listarPosicoesOcupadas,
  listarZonasGuarda,
  obterOcupacaoLocal,
  obterOcupacaoZona,
  type CompartimentoPayload,
  type EstruturaPayload,
  type LocalGuardaPayload,
  type PosicaoPayload,
  type ZonaGuardaPayload,
} from "@/lib/api/storage-addressing";
import type {
  CompartimentoArmazenamento,
  EstruturaArmazenamento,
  LocalGuarda,
  PosicaoArmazenamento,
  ZonaGuarda,
} from "@/types/storage";

type Option = readonly [string, string];

export function LocaisGuardaPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<LocalGuarda | null>(null);
  const [deletingLocal, setDeletingLocal] = useState<LocalGuarda | null>(null);
  const [filters, setFilters] = useState({ q: "", tipo: "", ativo: "" });
  const locais = useQuery({ queryKey: ["locais-guarda"], queryFn: () => listarLocaisGuarda() });
  const mutation = useMutation({
    mutationFn: (payload: LocalGuardaPayload) =>
      editing ? atualizarLocalGuarda(editing.id, payload) : criarLocalGuarda(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["locais-guarda"] });
      setOpen(false);
      setEditing(null);
    },
  });
  const remove = useMutation({
    mutationFn: (local: LocalGuarda) => excluirLocalGuarda(local.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["locais-guarda"] });
      setDeletingLocal(null);
    },
  });
  const data = (locais.data ?? []).filter((item) => {
    const q = filters.q.toLowerCase();
    return (
      (!q ||
        item.codigo.toLowerCase().includes(q) ||
        item.nome.toLowerCase().includes(q) ||
        (item.municipio ?? "").toLowerCase().includes(q) ||
        (item.uf ?? "").toLowerCase().includes(q)) &&
      (!filters.tipo || item.tipo_local === filters.tipo) &&
      (!filters.ativo || String(item.ativo) === filters.ativo)
    );
  });

  return (
    <div className="space-y-5">
      <StoragePageHeader
        title="Locais de Guarda"
        description="Cadastro de depósitos, salas-cofre, data centers, mapotecas e ambientes lógicos."
        action={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button onClick={() => setEditing(null)}>
                <Plus className="h-4 w-4" />
                Novo Local de Guarda
              </Button>
            </DialogTrigger>
            <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editing ? "Editar local" : "Novo local"}</DialogTitle>
                <DialogDescription>Informe os dados de identificação e endereço.</DialogDescription>
              </DialogHeader>
              <LocalForm
                local={editing}
                isSaving={mutation.isPending}
                error={mutation.error?.message}
                onSubmit={(payload) => mutation.mutate(payload)}
              />
            </DialogContent>
          </Dialog>
        }
      />
      <FilterBar
        search={filters.q}
        onSearch={(q) => setFilters({ ...filters, q })}
        selects={[
          { label: "Tipo", value: filters.tipo, options: tipoLocalOptions, onChange: (tipo) => setFilters({ ...filters, tipo }) },
          { label: "Ativo", value: filters.ativo, options: [["true", "Ativo"], ["false", "Inativo"]], onChange: (ativo) => setFilters({ ...filters, ativo }) },
        ]}
      />
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código</TableHead>
                <TableHead>Nome</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Município</TableHead>
                <TableHead>UF</TableHead>
                <TableHead>Ativo</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((local) => (
                <TableRow key={local.id}>
                  <TableCell className="font-medium">{local.codigo}</TableCell>
                  <TableCell>{local.nome}</TableCell>
                  <TableCell>{storageLabel(local.tipo_local)}</TableCell>
                  <TableCell>{local.municipio ?? "-"}</TableCell>
                  <TableCell>{local.uf ?? "-"}</TableCell>
                  <TableCell><StorageStatusBadge ativo={local.ativo} /></TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button asChild variant="ghost" size="icon" title="Abrir zonas">
                        <Link href={`/enderecamento/zonas?id_local_guarda=${local.id}`}>
                          <GitBranch className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => { setEditing(local); setOpen(true); }}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Excluir local"
                        disabled={remove.isPending}
                        onClick={() => {
                          remove.reset();
                          setDeletingLocal(local);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {!data.length ? <EmptyTable colSpan={7} message="Nenhum local encontrado." /> : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Dialog
        open={Boolean(deletingLocal)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !remove.isPending) {
            setDeletingLocal(null);
          }
        }}
      >
        <DialogContent
          className="max-w-md"
          onInteractOutside={(event) => {
            if (remove.isPending) {
              event.preventDefault();
            }
          }}
          onEscapeKeyDown={(event) => {
            if (remove.isPending) {
              event.preventDefault();
            }
          }}
        >
          <DialogHeader>
            <DialogTitle>{remove.isPending ? "Excluindo local" : "Confirmar exclusão"}</DialogTitle>
            <DialogDescription>
              {remove.isPending
                ? "Aguarde enquanto o local de guarda e todos os endereçamentos vinculados são excluídos."
                : "Esta ação excluirá permanentemente o local de guarda e todos os endereçamentos vinculados a ele."}
            </DialogDescription>
          </DialogHeader>
          {deletingLocal ? (
            <div className="rounded-md border p-3 text-sm">
              <p className="font-medium">{deletingLocal.nome}</p>
              <p className="text-muted-foreground">{deletingLocal.codigo}</p>
            </div>
          ) : null}
          {remove.error ? <p className="text-sm text-destructive">{remove.error.message}</p> : null}
          {remove.isPending ? (
            <div className="flex items-center gap-3 rounded-md bg-muted p-3 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              Processando exclusão em cascata...
            </div>
          ) : (
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeletingLocal(null)}>
                Cancelar
              </Button>
              <Button
                variant="destructive"
                onClick={() => deletingLocal && remove.mutate(deletingLocal)}
              >
                Excluir
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function ZonasGuardaPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ZonaGuarda | null>(null);
  const [filters, setFilters] = useState({ local: "", tipo: "", ativo: "" });
  const locais = useQuery({ queryKey: ["locais-guarda"], queryFn: () => listarLocaisGuarda() });
  const zonas = useQuery({ queryKey: ["zonas-guarda"], queryFn: () => listarZonasGuarda() });
  const mutation = useMutation({
    mutationFn: (payload: ZonaGuardaPayload) =>
      editing ? atualizarZonaGuarda(editing.id, payload) : criarZonaGuarda(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["zonas-guarda"] });
      setOpen(false);
      setEditing(null);
    },
  });
  const topo = useMutation({
    mutationFn: gerarTopografiaZona,
    onSuccess: async (result) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["zonas-guarda"] }),
        queryClient.invalidateQueries({ queryKey: ["estruturas"] }),
        queryClient.invalidateQueries({ queryKey: ["compartimentos"] }),
        queryClient.invalidateQueries({ queryKey: ["posicoes"] }),
      ]);
      window.alert(
        `Topografia gerada: ${result.estruturas_criadas} estruturas, ${result.compartimentos_criados} compartimentos e ${result.posicoes_criadas} posições.`,
      );
    },
  });
  const data = (zonas.data ?? []).filter((item) =>
    (!filters.local || String(item.id_local_guarda) === filters.local) &&
    (!filters.tipo || item.tipo_zona === filters.tipo) &&
    (!filters.ativo || String(item.ativo) === filters.ativo),
  );

  return (
    <div className="space-y-5">
      <StoragePageHeader
        title="Zonas de Guarda"
        description="Parâmetros de organização e geração automática da topografia."
        action={<Button onClick={() => { setEditing(null); setOpen(true); }}><Plus className="h-4 w-4" />Nova Zona</Button>}
      />
      <StorageDialog open={open} onOpenChange={setOpen} title={editing ? "Editar zona" : "Nova zona"}>
        <ZonaForm zona={editing} locais={locais.data ?? []} isSaving={mutation.isPending} error={mutation.error?.message} onSubmit={(payload) => mutation.mutate(payload)} />
      </StorageDialog>
      <FilterBar
        selects={[
          { label: "Local", value: filters.local, options: (locais.data ?? []).map((item) => [String(item.id), item.nome] as const), onChange: (local) => setFilters({ ...filters, local }) },
          { label: "Tipo", value: filters.tipo, options: tipoZonaOptions, onChange: (tipo) => setFilters({ ...filters, tipo }) },
          { label: "Ativo", value: filters.ativo, options: [["true", "Ativo"], ["false", "Inativo"]], onChange: (ativo) => setFilters({ ...filters, ativo }) },
        ]}
      />
      <EntityTable
        columns={["Código", "Nome", "Local", "Tipo", "Capacidade estimada", "Ativo", "Ações"]}
        rows={data.map((zona) => [
          zona.codigo,
          zona.nome,
          localName(locais.data, zona.id_local_guarda),
          storageLabel(zona.tipo_zona),
          capacidadeZona(zona).toLocaleString("pt-BR"),
          <StorageStatusBadge key="status" ativo={zona.ativo} />,
          <RowActions key="actions" onEdit={() => { setEditing(zona); setOpen(true); }} onToggle={() => atualizarZonaGuarda(zona.id, { ativo: !zona.ativo }).then(() => queryClient.invalidateQueries({ queryKey: ["zonas-guarda"] }))}>
            <Button
              variant="ghost"
              size="icon"
              title={zona.topografia_gerada ? "Topografia já gerada" : "Gerar topografia"}
              disabled={zona.topografia_gerada || topo.isPending}
              onClick={() => {
                if (window.confirm("Esta ação criará automaticamente estruturas, compartimentos e posições para esta zona. Deseja continuar?")) {
                  topo.mutate(zona.id);
                }
              }}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button asChild variant="ghost" size="icon" title="Abrir posições">
              <Link href={`/enderecamento/posicoes?id_zona_guarda=${zona.id}`}>
                <MapIcon className="h-4 w-4" />
              </Link>
            </Button>
          </RowActions>,
        ])}
      />
      {topo.error ? <p className="text-sm text-destructive">{topo.error.message}</p> : null}
    </div>
  );
}

export function EstruturasPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<EstruturaArmazenamento | null>(null);
  const zonas = useQuery({ queryKey: ["zonas-guarda"], queryFn: () => listarZonasGuarda() });
  const estruturas = useQuery({ queryKey: ["estruturas"], queryFn: () => listarEstruturas() });
  const mutation = useMutation({
    mutationFn: (payload: EstruturaPayload) =>
      editing ? atualizarEstrutura(editing.id, payload) : criarEstrutura(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["estruturas"] });
      setOpen(false);
      setEditing(null);
    },
  });

  return (
    <CrudPage
      title="Estruturas"
      description="Estantes, racks, servidores, NAS, buckets e demais estruturas."
      actionLabel="Nova Estrutura"
      open={open}
      setOpen={setOpen}
      onNew={() => setEditing(null)}
      dialogTitle={editing ? "Editar estrutura" : "Nova estrutura"}
      form={<EstruturaForm estrutura={editing} zonas={zonas.data ?? []} isSaving={mutation.isPending} error={mutation.error?.message} onSubmit={(payload) => mutation.mutate(payload)} />}
      table={<EntityTable columns={["Código", "Nome", "Zona", "Tipo", "Ordem", "Capacidade", "Ativo", "Ações"]} rows={(estruturas.data ?? []).map((item) => [item.codigo, item.nome, zonaName(zonas.data, item.id_zona_guarda), storageLabel(item.tipo_estrutura), item.ordem ?? "-", item.capacidade_total ?? "-", <StorageStatusBadge key="s" ativo={item.ativo} />, <RowActions key="a" onEdit={() => { setEditing(item); setOpen(true); }} onToggle={() => atualizarEstrutura(item.id, { ativo: !item.ativo }).then(() => queryClient.invalidateQueries({ queryKey: ["estruturas"] }))} />])} />}
    />
  );
}

export function CompartimentosPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<CompartimentoArmazenamento | null>(null);
  const estruturas = useQuery({ queryKey: ["estruturas"], queryFn: () => listarEstruturas() });
  const compartimentos = useQuery({ queryKey: ["compartimentos"], queryFn: () => listarCompartimentos() });
  const mutation = useMutation({
    mutationFn: (payload: CompartimentoPayload) =>
      editing ? atualizarCompartimento(editing.id, payload) : criarCompartimento(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["compartimentos"] });
      setOpen(false);
      setEditing(null);
    },
  });

  return (
    <CrudPage
      title="Compartimentos"
      description="Prateleiras, gavetas, slots, diretórios, buckets e partições."
      actionLabel="Novo Compartimento"
      open={open}
      setOpen={setOpen}
      onNew={() => setEditing(null)}
      dialogTitle={editing ? "Editar compartimento" : "Novo compartimento"}
      form={<CompartimentoForm compartimento={editing} estruturas={estruturas.data ?? []} isSaving={mutation.isPending} error={mutation.error?.message} onSubmit={(payload) => mutation.mutate(payload)} />}
      table={<EntityTable columns={["Código", "Nome", "Estrutura", "Tipo", "Ordem", "Capacidade", "Ativo", "Ações"]} rows={(compartimentos.data ?? []).map((item) => [item.codigo, item.nome, estruturaName(estruturas.data, item.id_estrutura_armazenamento), storageLabel(item.tipo_compartimento), item.ordem ?? "-", item.capacidade_posicoes ?? "-", <StorageStatusBadge key="s" ativo={item.ativo} />, <RowActions key="a" onEdit={() => { setEditing(item); setOpen(true); }} onToggle={() => atualizarCompartimento(item.id, { ativo: !item.ativo }).then(() => queryClient.invalidateQueries({ queryKey: ["compartimentos"] }))} />])} />}
    />
  );
}

export function PosicoesPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<PosicaoArmazenamento | null>(null);
  const [filters, setFilters] = useState({ q: "", ocupada: "", ativo: "", tipo: "" });
  const compartimentos = useQuery({ queryKey: ["compartimentos"], queryFn: () => listarCompartimentos() });
  const posicoes = useQuery({ queryKey: ["posicoes"], queryFn: () => listarPosicoes() });
  const mutation = useMutation({
    mutationFn: (payload: PosicaoPayload) =>
      editing ? atualizarPosicao(editing.id, payload) : criarPosicao(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["posicoes"] });
      setOpen(false);
      setEditing(null);
    },
  });
  const data = (posicoes.data ?? []).filter((item) => {
    const q = filters.q.toLowerCase();
    return (
      (!q || item.codigo_completo.toLowerCase().includes(q) || item.codigo.toLowerCase().includes(q)) &&
      (!filters.ocupada || String(item.ocupada) === filters.ocupada) &&
      (!filters.ativo || String(item.ativo) === filters.ativo) &&
      (!filters.tipo || item.tipo_posicao === filters.tipo)
    );
  });
  const total = data.length;
  const ocupadas = data.filter((item) => item.ocupada).length;
  const livres = data.filter((item) => !item.ocupada && item.ativo).length;
  const taxa = total ? (ocupadas / total) * 100 : 0;

  return (
    <div className="space-y-5">
      <StoragePageHeader title="Posições de Armazenamento" description="Consulta central de posições livres, ocupadas e inativas." action={<Button onClick={() => { setEditing(null); setOpen(true); }}><Plus className="h-4 w-4" />Nova Posição</Button>} />
      <StorageDialog open={open} onOpenChange={setOpen} title={editing ? "Editar posição" : "Nova posição"}>
        <PosicaoForm posicao={editing} compartimentos={compartimentos.data ?? []} isSaving={mutation.isPending} error={mutation.error?.message} onSubmit={(payload) => mutation.mutate(payload)} />
      </StorageDialog>
      <section className="grid gap-4 md:grid-cols-4">
        <OccupancyCard title="Total" value={total} />
        <OccupancyCard title="Livres" value={livres} />
        <OccupancyCard title="Ocupadas" value={ocupadas} />
        <OccupancyCard title="Ocupação" value={`${taxa.toFixed(2)}%`} />
      </section>
      <FilterBar search={filters.q} onSearch={(q) => setFilters({ ...filters, q })} selects={[{ label: "Tipo", value: filters.tipo, options: tipoPosicaoOptions, onChange: (tipo) => setFilters({ ...filters, tipo }) }, { label: "Ocupada", value: filters.ocupada, options: [["true", "Ocupada"], ["false", "Livre"]], onChange: (ocupada) => setFilters({ ...filters, ocupada }) }, { label: "Ativo", value: filters.ativo, options: [["true", "Ativa"], ["false", "Inativa"]], onChange: (ativo) => setFilters({ ...filters, ativo }) }]} />
      <EntityTable columns={["Código completo", "Local", "Zona", "Tipo", "Ocupada", "Ativo", "Ações"]} rows={data.map((item) => [item.codigo_completo, item.local_guarda ?? "-", item.zona ?? "-", storageLabel(item.tipo_posicao), item.ocupada ? "Sim" : "Não", <StorageStatusBadge key="s" ativo={item.ativo} ocupada={item.ocupada} />, <RowActions key="a" onEdit={() => { setEditing(item); setOpen(true); }} onToggle={() => excluirPosicao(item.id).then(() => queryClient.invalidateQueries({ queryKey: ["posicoes"] }))}><Button variant="ghost" size="icon" title="Detalhes" onClick={() => window.alert(item.localizacao_completa ?? item.codigo_completo)}><Eye className="h-4 w-4" /></Button></RowActions>])} />
    </div>
  );
}

export function MapaTopograficoPage() {
  const [selectedNode, setSelectedNode] = useState<TopographicSelection | null>(null);
  const [selected, setSelected] = useState<PosicaoArmazenamento | null>(null);
  const zonas = useQuery({ queryKey: ["zonas-guarda"], queryFn: () => listarZonasGuarda() });
  const estruturas = useQuery({ queryKey: ["estruturas"], queryFn: () => listarEstruturas() });
  const compartimentos = useQuery({ queryKey: ["compartimentos"], queryFn: () => listarCompartimentos() });
  const posicoes = useQuery({
    queryKey: ["posicoes"],
    queryFn: () => listarPosicoes(),
  });
  const firstZona = zonas.data?.[0] ?? null;
  const activeNode = selectedNode ?? (firstZona ? { type: "zona" as const, id: firstZona.id } : null);
  const activeZona =
    activeNode?.type === "zona"
      ? zonas.data?.find((zona) => zona.id === activeNode.id) ?? null
      : null;
  const activeEstrutura =
    activeNode?.type === "estrutura"
      ? estruturas.data?.find((estrutura) => estrutura.id === activeNode.id) ?? null
      : null;
  const activeEstruturaZona = activeEstrutura
    ? zonas.data?.find((zona) => zona.id === activeEstrutura.id_zona_guarda) ?? null
    : null;

  return (
    <div className="space-y-5">
      <StoragePageHeader title="Mapa Topográfico" description="Navegação por zona e estante com visualização topográfica." />
      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Endereçamento</CardTitle>
            <CardDescription>Zonas e estantes geradas na topografia.</CardDescription>
          </CardHeader>
          <CardContent>
            <TopographicAddressTree
              zonas={zonas.data ?? []}
              estruturas={estruturas.data ?? []}
              compartimentos={compartimentos.data ?? []}
              posicoes={posicoes.data ?? []}
              selected={activeNode}
              onSelect={setSelectedNode}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{activeEstrutura?.nome ?? activeZona?.nome ?? "Topografia"}</CardTitle>
            <CardDescription>
              {activeEstrutura
                ? `${activeEstrutura.codigo} - posições por prateleira.`
                : activeZona
                  ? `${activeZona.codigo} - estantes por corredor e módulo.`
                  : "Selecione uma zona ou estante."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {activeEstrutura ? (
              <EstruturaTopografica
                estrutura={activeEstrutura}
                compartimentos={compartimentos.data ?? []}
                posicoes={posicoes.data ?? []}
                onSelectPosicao={setSelected}
              />
            ) : activeZona ? (
              <ZonaTopografica
                zona={activeZona}
                estruturas={estruturas.data ?? []}
                compartimentos={compartimentos.data ?? []}
                posicoes={posicoes.data ?? []}
                selectedEstruturaId={activeNode?.type === "estrutura" ? activeNode.id : null}
                onSelectEstrutura={(estrutura) => setSelectedNode({ type: "estrutura", id: estrutura.id })}
              />
            ) : <EmptyState message="Nenhuma zona selecionada." />}
          </CardContent>
        </Card>
      </div>
      <StorageDialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} title="Detalhes da posição">
        {selected ? <PositionDetails posicao={selected} /> : null}
      </StorageDialog>
    </div>
  );
}

type TopographicSelection =
  | { type: "zona"; id: number }
  | { type: "estrutura"; id: number };

function TopographicAddressTree({
  zonas,
  estruturas,
  compartimentos,
  posicoes,
  selected,
  onSelect,
}: {
  zonas: ZonaGuarda[];
  estruturas: EstruturaArmazenamento[];
  compartimentos: CompartimentoArmazenamento[];
  posicoes: PosicaoArmazenamento[];
  selected: TopographicSelection | null;
  onSelect: (selection: TopographicSelection) => void;
}) {
  if (!zonas.length) {
    return <EmptyState message="Nenhuma zona cadastrada." />;
  }

  return (
    <div className="max-h-[70vh] space-y-3 overflow-y-auto pr-1">
      {zonas.map((zona) => {
        const zonaEstruturas = estruturas
          .filter((estrutura) => estrutura.id_zona_guarda === zona.id)
          .sort(compareStructureCodes);
        const zonaResumo = countPositionStatusForStructures(zonaEstruturas, compartimentos, posicoes);
        const zonaSelected = selected?.type === "zona" && selected.id === zona.id;

        return (
          <div key={zona.id} className="space-y-1">
            <Button
              type="button"
              variant={zonaSelected ? "secondary" : "ghost"}
              className="h-auto w-full justify-start px-3 py-2 text-left"
              onClick={() => onSelect({ type: "zona", id: zona.id })}
            >
              <span className="min-w-0">
                <span className="block truncate font-medium">{zona.codigo} - {zona.nome}</span>
                <span className="block text-xs text-muted-foreground">
                  {zonaEstruturas.length} estantes - {formatPositionStatus(zonaResumo)}
                </span>
              </span>
            </Button>
            <div className="ml-4 space-y-1 border-l pl-2">
              {zonaEstruturas.map((estrutura) => {
                const estruturaSelected = selected?.type === "estrutura" && selected.id === estrutura.id;
                const estruturaResumo = countPositionStatusForStructures([estrutura], compartimentos, posicoes);

                return (
                  <Button
                    key={estrutura.id}
                    type="button"
                    variant={estruturaSelected ? "secondary" : "ghost"}
                    className="h-8 w-full justify-start px-2 text-left text-xs"
                    onClick={() => onSelect({ type: "estrutura", id: estrutura.id })}
                  >
                    <span className="min-w-0">
                      <span className="block truncate">{estrutura.codigo} - {estrutura.nome}</span>
                      <span className="block text-[11px] text-muted-foreground">{formatPositionStatus(estruturaResumo)}</span>
                    </span>
                  </Button>
                );
              })}
              {!zonaEstruturas.length ? (
                <p className="px-2 py-1 text-xs text-muted-foreground">Sem estantes geradas.</p>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ZonaTopografica({
  zona,
  estruturas,
  compartimentos,
  posicoes,
  selectedEstruturaId,
  onSelectEstrutura,
}: {
  zona: ZonaGuarda;
  estruturas: EstruturaArmazenamento[];
  compartimentos: CompartimentoArmazenamento[];
  posicoes: PosicaoArmazenamento[];
  selectedEstruturaId: number | null;
  onSelectEstrutura: (estrutura: EstruturaArmazenamento) => void;
}) {
  const zonaEstruturas = estruturas
    .filter((estrutura) => estrutura.id_zona_guarda === zona.id)
    .sort(compareStructureCodes);
  const corredores = groupStructuresByCorridor(zonaEstruturas);
  const zonaResumo = countPositionStatusForStructures(zonaEstruturas, compartimentos, posicoes);

  if (!zonaEstruturas.length) {
    return <EmptyState message="Nenhuma estante gerada para esta zona." />;
  }

  return (
    <div className="overflow-x-auto pb-2">
      <div className="min-w-max space-y-4">
        <div className="flex w-fit items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm">
          <span className="font-medium">{zona.codigo}</span>
          <PositionStatusPills summary={zonaResumo} />
        </div>
        {corredores.map(([corredor, corredorEstruturas]) => {
          const modulos = groupStructuresByModule(corredorEstruturas);
          const corredorResumo = countPositionStatusForStructures(corredorEstruturas, compartimentos, posicoes);

          return (
            <section key={corredor} className="space-y-2">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold">{corredor}</h3>
                <PositionStatusPills summary={corredorResumo} />
                <div className="h-px flex-1 bg-border" />
              </div>
              <div className="flex gap-4">
                {modulos.map(([modulo, moduloEstruturas]) => {
                  const moduloResumo = countPositionStatusForStructures(moduloEstruturas, compartimentos, posicoes);

                  return (
                  <div key={`${corredor}-${modulo}`} className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-medium text-muted-foreground">{modulo}</p>
                      <PositionStatusPills summary={moduloResumo} />
                    </div>
                    <div
                      className="grid gap-2"
                      style={{ gridTemplateColumns: `repeat(${moduloEstruturas.length}, minmax(150px, 1fr))` }}
                    >
                      {moduloEstruturas.map((estrutura) => {
                        const estruturaResumo = countPositionStatusForStructures([estrutura], compartimentos, posicoes);

                        return (
                          <button
                            key={estrutura.id}
                            type="button"
                            className={[
                              "h-40 rounded-md border bg-background p-3 text-left shadow-sm transition-colors hover:bg-muted",
                              selectedEstruturaId === estrutura.id ? "border-primary ring-2 ring-ring" : "",
                            ].join(" ")}
                            onClick={() => onSelectEstrutura(estrutura)}
                          >
                            <div className="flex h-full flex-col justify-between">
                              <div>
                                <p className="text-sm font-semibold">{estrutura.codigo}</p>
                                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{estrutura.nome}</p>
                                <div className="mt-2">
                                  <PositionStatusPills summary={estruturaResumo} />
                                </div>
                              </div>
                              <div className="space-y-1">
                                {Array.from({ length: 4 }).map((_, index) => (
                                  <div key={index} className="h-2 rounded-sm bg-muted" />
                                ))}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function EstruturaTopografica({
  estrutura,
  compartimentos,
  posicoes,
  onSelectPosicao,
}: {
  estrutura: EstruturaArmazenamento;
  compartimentos: CompartimentoArmazenamento[];
  posicoes: PosicaoArmazenamento[];
  onSelectPosicao: (posicao: PosicaoArmazenamento) => void;
}) {
  const estruturaCompartimentos = compartimentos
    .filter((compartimento) => compartimento.id_estrutura_armazenamento === estrutura.id)
    .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0));
  const positionsByCompartment = new Map<number, PosicaoArmazenamento[]>();

  for (const posicao of posicoes) {
    const current = positionsByCompartment.get(posicao.id_compartimento_armazenamento) ?? [];
    current.push(posicao);
    positionsByCompartment.set(posicao.id_compartimento_armazenamento, current);
  }

  if (!estruturaCompartimentos.length) {
    return <EmptyState message="Nenhuma prateleira encontrada para esta estante." />;
  }

  const estruturaResumo = countPositionStatusInCompartments(estruturaCompartimentos, posicoes);

  return (
    <div className="overflow-x-auto pb-2">
      <div className="min-w-[720px] rounded-md border bg-muted/40 p-4">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">{estrutura.codigo}</p>
            <p className="text-xs text-muted-foreground">{storageLabel(estrutura.tipo_estrutura)}</p>
          </div>
          <div className="flex items-center gap-2">
            <PositionStatusPills summary={estruturaResumo} />
            <StorageStatusBadge ativo={estrutura.ativo} />
          </div>
        </div>
        <div className="space-y-3">
          {estruturaCompartimentos.map((compartimento) => {
            const compartimentoPosicoes = (positionsByCompartment.get(compartimento.id) ?? [])
              .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0));

            return (
              <div key={compartimento.id} className="rounded-md border bg-background p-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-sm font-medium">{compartimento.nome}</p>
                  <p className="text-xs text-muted-foreground">{compartimento.codigo}</p>
                </div>
                <div
                  className="grid gap-2"
                  style={{ gridTemplateColumns: `repeat(${Math.max(compartimentoPosicoes.length, 1)}, minmax(92px, 1fr))` }}
                >
                  {compartimentoPosicoes.map((posicao) => (
                    <button
                      key={posicao.id}
                      type="button"
                      className={[
                        "h-16 rounded-md border p-2 text-left text-xs transition-colors hover:bg-muted",
                        posicao.ocupada ? "bg-amber-50" : "bg-emerald-50",
                        posicao.ativo ? "" : "opacity-60",
                      ].join(" ")}
                      onClick={() => onSelectPosicao(posicao)}
                    >
                      <span className="block font-semibold">{posicao.codigo}</span>
                      <span className="mt-1 block truncate text-muted-foreground">
                        {posicao.ocupada ? "Ocupada" : "Livre"}
                      </span>
                    </button>
                  ))}
                  {!compartimentoPosicoes.length ? (
                    <div className="h-16 rounded-md border border-dashed p-2 text-xs text-muted-foreground">
                      Sem posições
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function MovimentacoesPage() {
  const movimentacoes = useQuery({ queryKey: ["movimentacoes"], queryFn: () => listarMovimentacoes() });
  return (
    <div className="space-y-5">
      <StoragePageHeader title="Movimentações" description="Histórico de atribuições e mudanças de posição." />
      <EntityTable columns={["Data", "Tipo de objeto", "Objeto", "Origem", "Destino", "Responsável", "Motivo"]} rows={(movimentacoes.data ?? []).map((item) => [formatDateTime(item.data_movimentacao), tipoObjeto(item), objetoId(item), item.id_posicao_origem ?? "-", item.id_posicao_destino ?? "-", item.responsavel ?? "-", item.motivo ?? "-"])} />
    </div>
  );
}

export function OcupacaoPage() {
  const locais = useQuery({ queryKey: ["locais-guarda"], queryFn: () => listarLocaisGuarda() });
  const zonas = useQuery({ queryKey: ["zonas-guarda"], queryFn: () => listarZonasGuarda() });
  const posicoes = useQuery({ queryKey: ["posicoes"], queryFn: () => listarPosicoes() });
  const ocupadas = (posicoes.data ?? []).filter((item) => item.ocupada).length;
  const total = posicoes.data?.length ?? 0;
  const taxa = total ? (ocupadas / total) * 100 : 0;

  return (
    <div className="space-y-5">
      <StoragePageHeader title="Ocupação" description="Indicadores operacionais da capacidade de armazenamento." />
      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <OccupancyCard title="Locais" value={locais.data?.length ?? 0} />
        <OccupancyCard title="Zonas" value={zonas.data?.length ?? 0} />
        <OccupancyCard title="Posições" value={total} />
        <OccupancyCard title="Livres" value={total - ocupadas} />
        <OccupancyCard title="Ocupadas" value={ocupadas} />
        <OccupancyCard title="Taxa geral" value={`${taxa.toFixed(2)}%`} />
      </section>
      <Card>
        <CardHeader><CardTitle>Ocupação por zona</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {(zonas.data ?? []).map((zona) => {
            const zonaPosicoes = (posicoes.data ?? []).filter((item) => item.zona === zona.nome);
            const zonaOcupadas = zonaPosicoes.filter((item) => item.ocupada).length;
            const zonaTaxa = zonaPosicoes.length ? (zonaOcupadas / zonaPosicoes.length) * 100 : 0;
            return (
              <div key={zona.id} className="space-y-2 rounded-md border p-3">
                <div className="flex justify-between text-sm"><span>{zona.nome}</span><span>{zonaTaxa.toFixed(2)}%</span></div>
                <OccupancyProgressBar value={zonaTaxa} />
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}

function CrudPage({ title, description, actionLabel, open, setOpen, onNew, dialogTitle, form, table }: { title: string; description: string; actionLabel: string; open: boolean; setOpen: (open: boolean) => void; onNew: () => void; dialogTitle: string; form: React.ReactNode; table: React.ReactNode }) {
  return (
    <div className="space-y-5">
      <StoragePageHeader title={title} description={description} action={<Button onClick={() => { onNew(); setOpen(true); }}><Plus className="h-4 w-4" />{actionLabel}</Button>} />
      <StorageDialog open={open} onOpenChange={setOpen} title={dialogTitle}>{form}</StorageDialog>
      {table}
    </div>
  );
}

function LocalForm({ local, isSaving, error, onSubmit }: { local: LocalGuarda | null; isSaving: boolean; error?: string; onSubmit: (payload: LocalGuardaPayload) => void }) {
  const [values, setValues] = useState<LocalGuardaPayload>({
    codigo: local?.codigo ?? "",
    nome: local?.nome ?? "",
    tipo_local: local?.tipo_local ?? "DEPOSITO",
    descricao: local?.descricao ?? "",
    logradouro: local?.logradouro ?? "",
    numero: local?.numero ?? "",
    complemento: local?.complemento ?? "",
    bairro: local?.bairro ?? "",
    municipio: local?.municipio ?? "",
    uf: local?.uf ?? "",
    cep: local?.cep ?? "",
    pais: local?.pais ?? "Brasil",
    observacoes: local?.observacoes ?? "",
    ativo: local?.ativo ?? true,
  });
  return <SimpleForm isSaving={isSaving} error={error} onSubmit={() => onSubmit(normalizeLocalPayload(values))}><TextField label="Código" value={values.codigo} onChange={(codigo) => setValues({ ...values, codigo })} required /><TextField label="Nome" value={values.nome} onChange={(nome) => setValues({ ...values, nome })} required /><SelectField label="Tipo" value={values.tipo_local} options={tipoLocalOptions} onChange={(tipo_local) => setValues({ ...values, tipo_local: tipo_local as LocalGuardaPayload["tipo_local"] })} required /><TextField label="Município" value={values.municipio ?? ""} onChange={(municipio) => setValues({ ...values, municipio })} /><TextField label="UF" value={values.uf ?? ""} maxLength={2} onChange={(uf) => setValues({ ...values, uf: uf.toUpperCase() })} /><TextField label="CEP" value={values.cep ?? ""} onChange={(cep) => setValues({ ...values, cep })} /><TextField label="Logradouro" value={values.logradouro ?? ""} onChange={(logradouro) => setValues({ ...values, logradouro })} /><TextField label="Número" value={values.numero ?? ""} onChange={(numero) => setValues({ ...values, numero })} /><TextField label="Complemento" value={values.complemento ?? ""} onChange={(complemento) => setValues({ ...values, complemento })} /><TextField label="Bairro" value={values.bairro ?? ""} onChange={(bairro) => setValues({ ...values, bairro })} /><TextField label="País" value={values.pais ?? ""} onChange={(pais) => setValues({ ...values, pais })} /><TextField label="Observações" value={values.observacoes ?? ""} onChange={(observacoes) => setValues({ ...values, observacoes })} /><CheckField label="Ativo" checked={values.ativo ?? true} onChange={(ativo) => setValues({ ...values, ativo })} /></SimpleForm>;
}

function ZonaForm({ zona, locais, isSaving, error, onSubmit }: { zona: ZonaGuarda | null; locais: LocalGuarda[]; isSaving: boolean; error?: string; onSubmit: (payload: ZonaGuardaPayload) => void }) {
  const [values, setValues] = useState<ZonaGuardaPayload>({ id_local_guarda: zona?.id_local_guarda ?? locais[0]?.id ?? 0, codigo: zona?.codigo ?? "", nome: zona?.nome ?? "", tipo_zona: zona?.tipo_zona ?? "ACERVO_TEXTUAL", descricao: zona?.descricao ?? "", quantidade_corredores: zona?.quantidade_corredores ?? 1, quantidade_modulos_por_corredor: zona?.quantidade_modulos_por_corredor ?? 1, quantidade_estantes_por_modulo: zona?.quantidade_estantes_por_modulo ?? 1, quantidade_prateleiras_por_estante: zona?.quantidade_prateleiras_por_estante ?? 1, capacidade_caixas_por_prateleira: zona?.capacidade_caixas_por_prateleira ?? 1, observacoes: zona?.observacoes ?? "", ativo: zona?.ativo ?? true });
  return <SimpleForm isSaving={isSaving} error={error} onSubmit={() => onSubmit(values)}><SelectField label="Local" value={String(values.id_local_guarda)} options={locais.map((item) => [String(item.id), item.nome] as const)} onChange={(id) => setValues({ ...values, id_local_guarda: Number(id) })} required /><TextField label="Código" value={values.codigo} onChange={(codigo) => setValues({ ...values, codigo })} required /><TextField label="Nome" value={values.nome} onChange={(nome) => setValues({ ...values, nome })} required /><SelectField label="Tipo" value={values.tipo_zona} options={tipoZonaOptions} onChange={(tipo_zona) => setValues({ ...values, tipo_zona: tipo_zona as ZonaGuardaPayload["tipo_zona"] })} required />{(["quantidade_corredores", "quantidade_modulos_por_corredor", "quantidade_estantes_por_modulo", "quantidade_prateleiras_por_estante", "capacidade_caixas_por_prateleira"] as const).map((field) => <NumberField key={field} label={field.replaceAll("_", " ")} value={values[field] ?? 1} onChange={(value) => setValues({ ...values, [field]: value })} />)}<div className="rounded-md border p-3 text-sm">Capacidade estimada: {capacidadeZona(values).toLocaleString("pt-BR")} posições</div><TextField label="Observações" value={values.observacoes ?? ""} onChange={(observacoes) => setValues({ ...values, observacoes })} /><CheckField label="Ativo" checked={values.ativo ?? true} onChange={(ativo) => setValues({ ...values, ativo })} /></SimpleForm>;
}

function EstruturaForm({ estrutura, zonas, isSaving, error, onSubmit }: { estrutura: EstruturaArmazenamento | null; zonas: ZonaGuarda[]; isSaving: boolean; error?: string; onSubmit: (payload: EstruturaPayload) => void }) {
  const [values, setValues] = useState<EstruturaPayload>({ id_zona_guarda: estrutura?.id_zona_guarda ?? zonas[0]?.id ?? 0, codigo: estrutura?.codigo ?? "", nome: estrutura?.nome ?? "", tipo_estrutura: estrutura?.tipo_estrutura ?? "ESTANTE", ordem: estrutura?.ordem ?? 1, capacidade_total: estrutura?.capacidade_total ?? 1, descricao: estrutura?.descricao ?? "", observacoes: estrutura?.observacoes ?? "", ativo: estrutura?.ativo ?? true });
  return <SimpleForm isSaving={isSaving} error={error} onSubmit={() => onSubmit(values)}><SelectField label="Zona" value={String(values.id_zona_guarda)} options={zonas.map((item) => [String(item.id), item.nome] as const)} onChange={(id) => setValues({ ...values, id_zona_guarda: Number(id) })} required /><TextField label="Código" value={values.codigo} onChange={(codigo) => setValues({ ...values, codigo })} required /><TextField label="Nome" value={values.nome} onChange={(nome) => setValues({ ...values, nome })} required /><SelectField label="Tipo" value={values.tipo_estrutura} options={tipoEstruturaOptions} onChange={(tipo_estrutura) => setValues({ ...values, tipo_estrutura: tipo_estrutura as EstruturaPayload["tipo_estrutura"] })} required /><NumberField label="Ordem" value={values.ordem ?? 1} onChange={(ordem) => setValues({ ...values, ordem })} /><NumberField label="Capacidade total" value={values.capacidade_total ?? 1} onChange={(capacidade_total) => setValues({ ...values, capacidade_total })} /><TextField label="Observações" value={values.observacoes ?? ""} onChange={(observacoes) => setValues({ ...values, observacoes })} /><CheckField label="Ativo" checked={values.ativo ?? true} onChange={(ativo) => setValues({ ...values, ativo })} /></SimpleForm>;
}

function CompartimentoForm({ compartimento, estruturas, isSaving, error, onSubmit }: { compartimento: CompartimentoArmazenamento | null; estruturas: EstruturaArmazenamento[]; isSaving: boolean; error?: string; onSubmit: (payload: CompartimentoPayload) => void }) {
  const [values, setValues] = useState<CompartimentoPayload>({ id_estrutura_armazenamento: compartimento?.id_estrutura_armazenamento ?? estruturas[0]?.id ?? 0, codigo: compartimento?.codigo ?? "", nome: compartimento?.nome ?? "", tipo_compartimento: compartimento?.tipo_compartimento ?? "PRATELEIRA", ordem: compartimento?.ordem ?? 1, capacidade_posicoes: compartimento?.capacidade_posicoes ?? 1, descricao: compartimento?.descricao ?? "", observacoes: compartimento?.observacoes ?? "", ativo: compartimento?.ativo ?? true });
  return <SimpleForm isSaving={isSaving} error={error} onSubmit={() => onSubmit(values)}><SelectField label="Estrutura" value={String(values.id_estrutura_armazenamento)} options={estruturas.map((item) => [String(item.id), item.nome] as const)} onChange={(id) => setValues({ ...values, id_estrutura_armazenamento: Number(id) })} required /><TextField label="Código" value={values.codigo} onChange={(codigo) => setValues({ ...values, codigo })} required /><TextField label="Nome" value={values.nome} onChange={(nome) => setValues({ ...values, nome })} required /><SelectField label="Tipo" value={values.tipo_compartimento} options={tipoCompartimentoOptions} onChange={(tipo_compartimento) => setValues({ ...values, tipo_compartimento: tipo_compartimento as CompartimentoPayload["tipo_compartimento"] })} required /><NumberField label="Ordem" value={values.ordem ?? 1} onChange={(ordem) => setValues({ ...values, ordem })} /><NumberField label="Capacidade de posições" value={values.capacidade_posicoes ?? 1} onChange={(capacidade_posicoes) => setValues({ ...values, capacidade_posicoes })} /><TextField label="Observações" value={values.observacoes ?? ""} onChange={(observacoes) => setValues({ ...values, observacoes })} /><CheckField label="Ativo" checked={values.ativo ?? true} onChange={(ativo) => setValues({ ...values, ativo })} /></SimpleForm>;
}

function PosicaoForm({ posicao, compartimentos, isSaving, error, onSubmit }: { posicao: PosicaoArmazenamento | null; compartimentos: CompartimentoArmazenamento[]; isSaving: boolean; error?: string; onSubmit: (payload: PosicaoPayload) => void }) {
  const [values, setValues] = useState<PosicaoPayload>({ id_compartimento_armazenamento: posicao?.id_compartimento_armazenamento ?? compartimentos[0]?.id ?? 0, codigo: posicao?.codigo ?? "", codigo_completo: posicao?.codigo_completo ?? "", tipo_posicao: posicao?.tipo_posicao ?? "POSICAO_CAIXA", ordem: posicao?.ordem ?? 1, capacidade_unidades: posicao?.capacidade_unidades ?? 1, ocupada: posicao?.ocupada ?? false, ativo: posicao?.ativo ?? true, observacoes: posicao?.observacoes ?? "" });
  return <SimpleForm isSaving={isSaving} error={error} onSubmit={() => onSubmit(values)}><SelectField label="Compartimento" value={String(values.id_compartimento_armazenamento)} options={compartimentos.map((item) => [String(item.id), item.nome] as const)} onChange={(id) => setValues({ ...values, id_compartimento_armazenamento: Number(id) })} required /><TextField label="Código" value={values.codigo} onChange={(codigo) => setValues({ ...values, codigo })} required /><TextField label="Código completo" value={values.codigo_completo} onChange={(codigo_completo) => setValues({ ...values, codigo_completo })} required /><SelectField label="Tipo" value={values.tipo_posicao} options={tipoPosicaoOptions} onChange={(tipo_posicao) => setValues({ ...values, tipo_posicao: tipo_posicao as PosicaoPayload["tipo_posicao"] })} required /><NumberField label="Ordem" value={values.ordem ?? 1} onChange={(ordem) => setValues({ ...values, ordem })} /><NumberField label="Capacidade" value={values.capacidade_unidades ?? 1} onChange={(capacidade_unidades) => setValues({ ...values, capacidade_unidades })} required /><TextField label="Observações" value={values.observacoes ?? ""} onChange={(observacoes) => setValues({ ...values, observacoes })} /><CheckField label="Ativo" checked={values.ativo ?? true} onChange={(ativo) => setValues({ ...values, ativo })} /></SimpleForm>;
}

function EntityTable({ columns, rows }: { columns: string[]; rows: React.ReactNode[][] }) {
  return <Card><CardContent className="overflow-x-auto p-0"><Table><TableHeader><TableRow>{columns.map((column) => <TableHead key={column}>{column}</TableHead>)}</TableRow></TableHeader><TableBody>{rows.map((row, index) => <TableRow key={index}>{row.map((cell, cellIndex) => <TableCell key={cellIndex}>{cell}</TableCell>)}</TableRow>)}{!rows.length ? <EmptyTable colSpan={columns.length} message="Nenhum registro encontrado." /> : null}</TableBody></Table></CardContent></Card>;
}

function RowActions({ onEdit, onToggle, children }: { onEdit: () => void; onToggle: () => void; children?: React.ReactNode }) {
  return <div className="flex justify-end gap-1">{children}<Button variant="ghost" size="icon" onClick={onEdit}><Edit className="h-4 w-4" /></Button><Button variant="ghost" size="icon" onClick={onToggle}><Trash2 className="h-4 w-4" /></Button></div>;
}

function FilterBar({ search, onSearch, selects = [] }: { search?: string; onSearch?: (value: string) => void; selects?: Array<{ label: string; value: string; options: readonly Option[]; onChange: (value: string) => void }> }) {
  return <div className="flex flex-col gap-3 rounded-md border p-3 lg:flex-row lg:items-end">{onSearch ? <div className="space-y-2 lg:w-80"><Label>Busca</Label><div className="relative"><Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input className="pl-9" value={search ?? ""} onChange={(event) => onSearch(event.target.value)} placeholder="Buscar" /></div></div> : null}{selects.map((select) => <SelectField key={select.label} label={select.label} value={select.value} options={select.options} onChange={select.onChange} includeEmpty />)}</div>;
}

function StorageDialog({ open, onOpenChange, title, children }: { open: boolean; onOpenChange: (open: boolean) => void; title: string; children: React.ReactNode }) {
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto"><DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader>{children}</DialogContent></Dialog>;
}

function SimpleForm({ children, isSaving, error, onSubmit }: { children: React.ReactNode; isSaving: boolean; error?: string; onSubmit: () => void }) {
  return <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); onSubmit(); }}>{children}{error ? <p className="text-sm text-destructive sm:col-span-2">{error}</p> : null}<div className="sm:col-span-2"><Button type="submit" disabled={isSaving}>{isSaving ? "Salvando..." : "Salvar"}</Button></div></form>;
}

function RequiredLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return <Label>{children}{required ? <span className="ml-1 text-destructive" aria-label="obrigatório">*</span> : null}</Label>;
}

function TextField({ label, value, onChange, required, maxLength }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; maxLength?: number }) {
  return <div className="space-y-2"><RequiredLabel required={required}>{label}</RequiredLabel><Input value={value} required={required} maxLength={maxLength} onChange={(event) => onChange(event.target.value)} /></div>;
}

function NumberField({ label, value, onChange, required }: { label: string; value: number; onChange: (value: number) => void; required?: boolean }) {
  return <div className="space-y-2"><RequiredLabel required={required}>{label}</RequiredLabel><Input type="number" min={1} value={value} required={required} onChange={(event) => onChange(Number(event.target.value))} /></div>;
}

function SelectField({ label, value, options, onChange, includeEmpty, required }: { label: string; value: string; options: readonly Option[]; onChange: (value: string) => void; includeEmpty?: boolean; required?: boolean }) {
  return <div className="space-y-2"><RequiredLabel required={required}>{label}</RequiredLabel><select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" value={value} required={required} onChange={(event) => onChange(event.target.value)}>{includeEmpty ? <option value="">Todos</option> : null}{options.map(([optionValue, label]) => <option key={optionValue} value={optionValue}>{label}</option>)}</select></div>;
}

function CheckField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return <label className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm"><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />{label}</label>;
}

function EmptyTable({ colSpan, message }: { colSpan: number; message: string }) {
  return <TableRow><TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground">{message}</TableCell></TableRow>;
}

function PositionDetails({ posicao }: { posicao: PosicaoArmazenamento }) {
  return <div className="space-y-4"><div className="grid gap-3 sm:grid-cols-2"><Detail label="Código" value={posicao.codigo} /><Detail label="Código completo" value={posicao.codigo_completo} /><Detail label="Local" value={posicao.local_guarda ?? "-"} /><Detail label="Zona" value={posicao.zona ?? "-"} /><Detail label="Tipo" value={storageLabel(posicao.tipo_posicao)} /><Detail label="Status" value={posicao.ocupada ? "Ocupada" : "Livre"} /></div><MovementTimeline data={[]} /></div>;
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 text-sm">{value}</div></div>;
}

function localName(data: LocalGuarda[] | undefined, id: number) {
  return data?.find((item) => item.id === id)?.nome ?? `#${id}`;
}

function zonaName(data: ZonaGuarda[] | undefined, id: number) {
  return data?.find((item) => item.id === id)?.nome ?? `#${id}`;
}

function estruturaName(data: EstruturaArmazenamento[] | undefined, id: number) {
  return data?.find((item) => item.id === id)?.nome ?? `#${id}`;
}

function optionalText(value: string | null | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function normalizeLocalPayload(values: LocalGuardaPayload): LocalGuardaPayload {
  return {
    ...values,
    codigo: values.codigo.trim(),
    nome: values.nome.trim(),
    descricao: optionalText(values.descricao),
    logradouro: optionalText(values.logradouro),
    numero: optionalText(values.numero),
    complemento: optionalText(values.complemento),
    bairro: optionalText(values.bairro),
    municipio: optionalText(values.municipio),
    uf: optionalText(values.uf)?.toUpperCase() ?? null,
    cep: optionalText(values.cep),
    pais: optionalText(values.pais),
    observacoes: optionalText(values.observacoes),
  };
}

function capacidadeZona(zona: Partial<ZonaGuarda>) {
  return (zona.quantidade_corredores ?? 0) * (zona.quantidade_modulos_por_corredor ?? 0) * (zona.quantidade_estantes_por_modulo ?? 0) * (zona.quantidade_prateleiras_por_estante ?? 0) * (zona.capacidade_caixas_por_prateleira ?? 0);
}

function compareStructureCodes(a: EstruturaArmazenamento, b: EstruturaArmazenamento) {
  const parsedA = parseStructureCode(a.codigo);
  const parsedB = parseStructureCode(b.codigo);

  return (
    parsedA.corredor - parsedB.corredor ||
    parsedA.modulo - parsedB.modulo ||
    parsedA.estante - parsedB.estante ||
    a.codigo.localeCompare(b.codigo)
  );
}

function groupStructuresByCorridor(estruturas: EstruturaArmazenamento[]) {
  const groups = new Map<string, EstruturaArmazenamento[]>();

  for (const estrutura of estruturas) {
    const parsed = parseStructureCode(estrutura.codigo);
    const key = parsed.corredorLabel;
    groups.set(key, [...(groups.get(key) ?? []), estrutura]);
  }

  return Array.from(groups.entries());
}

function groupStructuresByModule(estruturas: EstruturaArmazenamento[]) {
  const groups = new Map<string, EstruturaArmazenamento[]>();

  for (const estrutura of estruturas) {
    const parsed = parseStructureCode(estrutura.codigo);
    const key = parsed.moduloLabel;
    groups.set(key, [...(groups.get(key) ?? []), estrutura]);
  }

  return Array.from(groups.entries());
}

type PositionStatusSummary = {
  livres: number;
  ocupados: number;
};

function PositionStatusPills({ summary }: { summary: PositionStatusSummary }) {
  return (
    <span className="inline-flex flex-wrap items-center gap-1">
      <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800">
        {summary.livres} livres
      </span>
      <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
        {summary.ocupados} ocupados
      </span>
    </span>
  );
}

function formatPositionStatus(summary: PositionStatusSummary) {
  return `${summary.livres} livres / ${summary.ocupados} ocupados`;
}

function countPositionStatusForStructures(
  estruturas: EstruturaArmazenamento[],
  compartimentos: CompartimentoArmazenamento[],
  posicoes: PosicaoArmazenamento[],
) {
  const estruturaIds = new Set(estruturas.map((estrutura) => estrutura.id));
  const relevantCompartimentos = compartimentos.filter((compartimento) =>
    estruturaIds.has(compartimento.id_estrutura_armazenamento),
  );

  return countPositionStatusInCompartments(relevantCompartimentos, posicoes);
}

function countPositionStatusInCompartments(
  compartimentos: CompartimentoArmazenamento[],
  posicoes: PosicaoArmazenamento[],
) {
  const compartimentoIds = new Set(compartimentos.map((compartimento) => compartimento.id));
  const summary: PositionStatusSummary = { livres: 0, ocupados: 0 };

  for (const posicao of posicoes) {
    if (!compartimentoIds.has(posicao.id_compartimento_armazenamento) || !posicao.ativo) {
      continue;
    }

    if (posicao.ocupada) {
      summary.ocupados += 1;
    } else {
      summary.livres += 1;
    }
  }

  return summary;
}

function parseStructureCode(codigo: string) {
  const match = /^C(\d+)-M(\d+)-E(\d+)$/i.exec(codigo);
  if (!match) {
    return {
      corredor: Number.MAX_SAFE_INTEGER,
      modulo: Number.MAX_SAFE_INTEGER,
      estante: Number.MAX_SAFE_INTEGER,
      corredorLabel: "Sem corredor",
      moduloLabel: "Sem módulo",
    };
  }

  return {
    corredor: Number(match[1]),
    modulo: Number(match[2]),
    estante: Number(match[3]),
    corredorLabel: `Corredor ${match[1]}`,
    moduloLabel: `Módulo ${match[2]}`,
  };
}

function formatDateTime(value?: string | null) {
  return value ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)) : "-";
}

function tipoObjeto(item: { id_unidade_acondicionamento?: number | null; id_midia_armazenamento?: number | null }) {
  if (item.id_unidade_acondicionamento) return "Unidade";
  if (item.id_midia_armazenamento) return "Mídia";
  return "Cópia digital";
}

function objetoId(item: { id_unidade_acondicionamento?: number | null; id_midia_armazenamento?: number | null; id_copia_unidade_acondicionamento_digital?: number | null }) {
  return item.id_unidade_acondicionamento ?? item.id_midia_armazenamento ?? item.id_copia_unidade_acondicionamento_digital ?? "-";
}
