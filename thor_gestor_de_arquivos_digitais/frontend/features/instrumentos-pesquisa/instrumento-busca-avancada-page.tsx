"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { advancedSearchInstrumentoRegistros, getInstrumentoPesquisaSchema, getInstrumentoRegistroFacets } from "@/lib/api/domain";
import type { InstrumentoCampoSchema, InstrumentoRegistro } from "@/types/domain";

const PAGE_SIZE = 25;

export function InstrumentoBuscaAvancadaPage({ instrumentoId }: { instrumentoId: string }) {
  const [q, setQ] = useState("");
  const [submittedQ, setSubmittedQ] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, unknown>>({});
  const [submittedFilters, setSubmittedFilters] = useState<Record<string, unknown>>({});
  const [sortValue, setSortValue] = useState("");
  const [submittedSort, setSubmittedSort] = useState<Array<Record<string, "asc" | "desc">>>([]);
  const [cursorStack, setCursorStack] = useState<string[]>([]);
  const currentCursor = cursorStack.at(-1) ?? null;

  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });

  const searchQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "busca-avancada", submittedQ, submittedFilters, submittedSort, currentCursor],
    queryFn: () =>
      advancedSearchInstrumentoRegistros(instrumentoId, {
        q: submittedQ,
        filters: submittedFilters,
        sort: submittedSort,
        page_size: PAGE_SIZE,
        cursor: currentCursor,
      }),
    enabled: Boolean(schemaQuery.data),
  });

  const facetsQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "facetas"],
    queryFn: () => getInstrumentoRegistroFacets(instrumentoId),
    enabled: Boolean(schemaQuery.data),
  });

  const schema = schemaQuery.data;
  const advancedFields = useMemo(
    () => schema?.campos.filter((campo) => campo.filtro_avancado) ?? [],
    [schema],
  );
  const facetFields = advancedFields.filter((campo) => campo.facetavel);
  const sortFields = schema?.campos.filter((campo) => campo.ordenavel) ?? [];
  const columns = schema?.campos.filter((campo) => campo.aparece_listagem) ?? [];
  const registros = searchQuery.data?.items ?? [];
  const facetOptions = useMemo(
    () =>
      Object.fromEntries(
        (facetsQuery.data?.facets ?? []).map((facet) => [
          facet.campo,
          facet.values.map((item) => ({
            value: item.value,
            label: `${item.value} (${item.count})`,
          })),
        ]),
      ),
    [facetsQuery.data],
  );

  if (schemaQuery.isLoading) return <p className="text-sm text-muted-foreground">Carregando schema...</p>;
  if (schemaQuery.error) return <p className="text-sm text-destructive">{schemaQuery.error.message}</p>;
  if (!schema) return <p className="text-sm text-muted-foreground">Schema nao encontrado.</p>;

  function submitSearch() {
    setCursorStack([]);
    setSubmittedQ(q.trim());
    setSubmittedFilters(cleanFilters(filterValues));
    setSubmittedSort(parseSort(sortValue));
  }

  function clearSearch() {
    setQ("");
    setFilterValues({});
    setSortValue("");
    setCursorStack([]);
    setSubmittedQ("");
    setSubmittedFilters({});
    setSubmittedSort([]);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{schema.instrumento.nome}</h1>
        <p className="text-sm text-muted-foreground">Busca avancada dinamica por campos configurados no instrumento.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <SlidersHorizontal className="h-4 w-4" />
            Filtros
          </CardTitle>
          <CardDescription>{advancedFields.length} campos disponiveis.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="space-y-2">
              <Label>Texto</Label>
              <Input value={q} placeholder="Buscar" onChange={(event) => setQ(event.target.value)} />
            </div>
            {facetFields.map((campo) => (
              <DynamicFilter
                key={campo.id}
                campo={campo}
                options={facetOptions[campo.chave] ?? []}
                value={filterValues[campo.chave]}
                onChange={(value) => setFilterValues((current) => ({ ...current, [campo.chave]: value }))}
              />
            ))}
            {advancedFields.filter((campo) => !campo.facetavel).map((campo) => (
              <DynamicFilter
                key={campo.id}
                campo={campo}
                options={optionsFrom(campo)}
                value={filterValues[campo.chave]}
                onChange={(value) => setFilterValues((current) => ({ ...current, [campo.chave]: value }))}
              />
            ))}
            <div className="space-y-2">
              <Label>Ordenacao</Label>
              <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={sortValue} onChange={(event) => setSortValue(event.target.value)}>
                <option value="">Mais recentes</option>
                {sortFields.flatMap((campo) => [
                  <option key={`${campo.chave}:asc`} value={`${campo.chave}:asc`}>{campo.nome} asc</option>,
                  <option key={`${campo.chave}:desc`} value={`${campo.chave}:desc`}>{campo.nome} desc</option>,
                ])}
              </select>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={submitSearch}>
              <Search className="h-4 w-4" />
              Buscar
            </Button>
            <Button type="button" variant="outline" onClick={clearSearch}>
              Limpar
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resultados</CardTitle>
          <CardDescription>{registros.length} registros nesta pagina.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {searchQuery.error ? <p className="p-6 text-sm text-destructive">{searchQuery.error.message}</p> : null}
          <ResultsTable registros={registros} columns={columns} />
        </CardContent>
        <div className="flex items-center justify-between border-t px-6 py-4 text-sm text-muted-foreground">
          <span>Pagina {cursorStack.length + 1}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={!cursorStack.length || searchQuery.isFetching} onClick={() => setCursorStack((stack) => stack.slice(0, -1))}>
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!searchQuery.data?.has_more || !searchQuery.data.next_cursor || searchQuery.isFetching}
              onClick={() => {
                if (searchQuery.data?.next_cursor) setCursorStack((stack) => [...stack, searchQuery.data!.next_cursor as string]);
              }}
            >
              Proxima
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function DynamicFilter({
  campo,
  options,
  value,
  onChange,
}: {
  campo: InstrumentoCampoSchema;
  options: Array<{ value: string; label: string }>;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  if (options.length) {
    return (
      <div className="space-y-2">
        <Label>{campo.nome}</Label>
        <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={Array.isArray(value) ? String(value[0] ?? "") : ""} onChange={(event) => onChange(event.target.value ? [event.target.value] : [])}>
          <option value="">Todos</option>
          {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </div>
    );
  }

  if (campo.tipo === "DATA" || campo.tipo === "PERIODO" || campo.tipo === "NUMERO") {
    const range = typeof value === "object" && value ? value as Record<string, string> : {};
    return (
      <div className="space-y-2">
        <Label>{campo.nome}</Label>
        <div className="grid grid-cols-2 gap-2">
          <Input placeholder="De" value={range.gte ?? ""} onChange={(event) => onChange({ ...range, gte: event.target.value })} />
          <Input placeholder="Ate" value={range.lte ?? ""} onChange={(event) => onChange({ ...range, lte: event.target.value })} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Label>{campo.nome}</Label>
      <Input value={filterTextValue(value)} onChange={(event) => onChange(event.target.value ? [event.target.value] : [])} />
    </div>
  );
}

function ResultsTable({ registros, columns }: { registros: InstrumentoRegistro[]; columns: InstrumentoCampoSchema[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((campo) => <TableHead key={campo.id}>{campo.nome}</TableHead>)}
          <TableHead>Status</TableHead>
          <TableHead>Atualizado em</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {registros.map((registro) => (
          <TableRow key={registro.id}>
            {columns.map((campo) => <TableCell key={campo.id}>{formatValue(registro.dados[campo.chave])}</TableCell>)}
            <TableCell>{registro.status}</TableCell>
            <TableCell>{formatDateTime(registro.atualizado_em)}</TableCell>
          </TableRow>
        ))}
        {!registros.length ? (
          <TableRow>
            <TableCell colSpan={columns.length + 2} className="h-24 text-center text-muted-foreground">Nenhum registro encontrado.</TableCell>
          </TableRow>
        ) : null}
      </TableBody>
    </Table>
  );
}

function cleanFilters(filters: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => {
      if (Array.isArray(value)) return value.length > 0;
      if (typeof value === "object" && value) return Object.values(value).some(Boolean);
      return Boolean(value);
    }),
  );
}

function parseSort(value: string): Array<Record<string, "asc" | "desc">> {
  if (!value) return [];
  const [field, direction] = value.split(":");
  return [{ [field]: direction === "desc" ? "desc" : "asc" }];
}

function optionsFrom(campo: InstrumentoCampoSchema) {
  if (!Array.isArray(campo.opcoes)) return [];
  return campo.opcoes
    .map((option) => {
      if (typeof option === "string") return { value: option, label: option };
      if (option && typeof option === "object") {
        const record = option as Record<string, unknown>;
        const value = String(record.valor ?? record.value ?? "");
        const label = String(record.rotulo ?? record.label ?? value);
        return value ? { value, label } : null;
      }
      return null;
    })
    .filter((option): option is { value: string; label: string } => Boolean(option));
}

function filterTextValue(value: unknown) {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return String(value[0] ?? "");
  return "";
}

function formatValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
