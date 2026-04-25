"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Box, CheckCircle2, CircleOff, MapPin, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { listarPosicoesLivres } from "@/lib/api/storage-addressing";
import type { MovimentacaoArmazenamento, PosicaoArmazenamento } from "@/types/storage";
import { storageLabel } from "@/features/armazenamento/storage-labels";

export function StorageStatusBadge({ ativo, ocupada }: { ativo?: boolean; ocupada?: boolean }) {
  if (ativo === false) {
    return <Badge variant="neutral">Inativa</Badge>;
  }

  if (ocupada) {
    return <Badge variant="warning">Ocupada</Badge>;
  }

  return <Badge variant="success">Livre</Badge>;
}

export function StorageLocationPath({ posicao }: { posicao?: PosicaoArmazenamento | null }) {
  if (!posicao) {
    return <span className="text-muted-foreground">Sem posição</span>;
  }

  return (
    <span className="font-medium">
      {posicao.localizacao_completa ?? posicao.codigo_completo}
    </span>
  );
}

export function StorageBreadcrumb({ posicao }: { posicao?: PosicaoArmazenamento | null }) {
  if (!posicao) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
      {(posicao.localizacao_completa ?? posicao.codigo_completo).split(" > ").map((part) => (
        <span key={part} className="rounded-md bg-muted px-2 py-1">
          {part}
        </span>
      ))}
    </div>
  );
}

export function OccupancyCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="mt-2 text-2xl font-semibold tracking-normal">{value}</p>
      </CardContent>
    </Card>
  );
}

export function OccupancyProgressBar({ value }: { value: number }) {
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="h-2 overflow-hidden rounded-full bg-muted">
      <div className="h-full bg-primary" style={{ width: `${bounded}%` }} />
    </div>
  );
}

export function StoragePositionPicker({
  value,
  onChange,
  label = "Posição de armazenamento",
}: {
  value?: number | null;
  onChange: (value: number | null) => void;
  label?: string;
}) {
  const [term, setTerm] = useState("");
  const posicoes = useQuery({
    queryKey: ["posicoes-livres-picker"],
    queryFn: () => listarPosicoesLivres(),
  });
  const filtered = useMemo(() => {
    const normalized = term.trim().toLowerCase();
    return (posicoes.data ?? []).filter((posicao) =>
      normalized
        ? posicao.codigo_completo.toLowerCase().includes(normalized) ||
          (posicao.localizacao_completa ?? "").toLowerCase().includes(normalized)
        : true,
    );
  }, [posicoes.data, term]);
  const selected = filtered.find((posicao) => posicao.id === value) ?? null;

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Buscar por código completo"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
        />
      </div>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
      >
        <option value="">Selecione uma posição livre</option>
        {filtered.map((posicao) => (
          <option key={posicao.id} value={posicao.id}>
            {posicao.codigo_completo}
          </option>
        ))}
      </select>
      {selected ? (
        <p className="text-xs text-muted-foreground">
          {selected.localizacao_completa ?? selected.codigo_completo}
        </p>
      ) : null}
    </div>
  );
}

export function PositionCard({
  posicao,
  onSelect,
}: {
  posicao: PosicaoArmazenamento;
  onSelect?: (posicao: PosicaoArmazenamento) => void;
}) {
  return (
    <button
      type="button"
      className="min-h-28 rounded-md border bg-background p-3 text-left transition-colors hover:bg-muted"
      onClick={() => onSelect?.(posicao)}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">{posicao.codigo}</span>
        <StorageStatusBadge ativo={posicao.ativo} ocupada={posicao.ocupada} />
      </div>
      <p className="mt-2 break-all text-xs text-muted-foreground">{posicao.codigo_completo}</p>
      <p className="mt-2 text-xs">{storageLabel(posicao.tipo_posicao)}</p>
    </button>
  );
}

export function TopographicTree({
  items,
  selected,
  onSelect,
}: {
  items: Array<{ id: number; label: string; parent?: string }>;
  selected?: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="space-y-1">
      {items.map((item) => (
        <Button
          key={item.id}
          type="button"
          variant={selected === item.id ? "secondary" : "ghost"}
          className="w-full justify-start"
          onClick={() => onSelect(item.id)}
        >
          <MapPin className="h-4 w-4" />
          <span className="truncate">{item.label}</span>
        </Button>
      ))}
    </div>
  );
}

export function MovementTimeline({ data }: { data: MovimentacaoArmazenamento[] }) {
  if (!data.length) {
    return <p className="text-sm text-muted-foreground">Nenhuma movimentação registrada.</p>;
  }

  return (
    <div className="space-y-3">
      {data.map((item) => (
        <div key={item.id} className="flex gap-3 rounded-md border p-3">
          <div className="mt-1">
            {item.id_posicao_destino ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <CircleOff className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
          <div className="space-y-1 text-sm">
            <p className="font-medium">{formatDateTime(item.data_movimentacao)}</p>
            <p className="text-muted-foreground">
              Origem #{item.id_posicao_origem ?? "-"} → destino #{item.id_posicao_destino ?? "-"}
            </p>
            <p>{item.motivo ?? "Movimentação de armazenamento"}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function StoragePageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-32 items-center justify-center rounded-md border text-sm text-muted-foreground">
      <Box className="mr-2 h-4 w-4" />
      {message}
    </div>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}
