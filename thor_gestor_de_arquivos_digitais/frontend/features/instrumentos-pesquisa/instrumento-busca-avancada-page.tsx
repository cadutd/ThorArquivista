"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Filter, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  advancedSearchInstrumentoRegistros,
  getInstrumentoPesquisaSchema,
  getInstrumentoRegistroFacets,
  listMidiasPage,
  listUnidadesPage,
  type MidiaPage,
  type UnidadePage,
} from "@/lib/api/domain";
import type { InstrumentoCampoSchema, InstrumentoRegistro, MidiaArmazenamento, UnidadeAcondicionamento } from "@/types/domain";

const DEFAULT_PAGE_SIZE = 20;

export function InstrumentoBuscaAvancadaPage({ instrumentoId }: { instrumentoId: string }) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [draftQ, setDraftQ] = useState("");
  const [draftFilters, setDraftFilters] = useState<Record<string, unknown>>({});
  const [draftSort, setDraftSort] = useState("");
  const [submittedQ, setSubmittedQ] = useState("");
  const [submittedFilters, setSubmittedFilters] = useState<Record<string, unknown>>({});
  const [submittedSort, setSubmittedSort] = useState<Array<Record<string, "asc" | "desc">>>([]);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const schemaQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "schema"],
    queryFn: () => getInstrumentoPesquisaSchema(instrumentoId),
  });

  const facetsQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "facetas"],
    queryFn: () => getInstrumentoRegistroFacets(instrumentoId),
    enabled: Boolean(schemaQuery.data),
  });

  const searchQuery = useQuery({
    queryKey: ["instrumentos-pesquisa", instrumentoId, "busca-avancada", submittedQ, submittedFilters, submittedSort, pageIndex, pageSize],
    queryFn: () =>
      advancedSearchInstrumentoRegistros(instrumentoId, {
        q: submittedQ,
        filters: submittedFilters,
        sort: submittedSort,
        page_size: pageSize,
        offset: pageIndex * pageSize,
        cursor: null,
      }),
    enabled: Boolean(schemaQuery.data),
  });

  const schema = schemaQuery.data;
  const advancedFields = useMemo(() => schema?.campos ?? [], [schema]);
  const facetFields = advancedFields.filter((campo) => campo.facetavel);
  const metadataFields = advancedFields.filter((campo) => !campo.facetavel);
  const sortFields = schema?.campos.filter((campo) => campo.ordenavel) ?? [];
  const columns = schema?.campos.filter((campo) => campo.aparece_listagem) ?? [];
  const registros = searchQuery.data?.items ?? [];
  const total = searchQuery.data?.total ?? registros.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageIndex + 1, totalPages);
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
    setPageIndex(0);
    setSubmittedQ(draftQ.trim());
    setSubmittedFilters(normalizeFilters(cleanFilters(draftFilters), advancedFields));
    setSubmittedSort(parseSort(draftSort));
  }

  function clearFilters() {
    setDraftQ("");
    setDraftFilters({});
    setDraftSort("");
    setPageIndex(0);
    setSubmittedQ("");
    setSubmittedFilters({});
    setSubmittedSort([]);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{schema.instrumento.nome}</h1>
        <p className="text-sm text-muted-foreground">Busca avancada dinamica por campos configurados no instrumento.</p>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar registro"
            value={draftQ}
            onChange={(event) => setDraftQ(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") submitSearch();
            }}
          />
        </div>
        <Button type="button" onClick={submitSearch}>
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
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={registros.length}
        total={total}
        isLoading={searchQuery.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPageIndex(0);
        }}
      />

      {showAdvanced ? (
        <div className="grid gap-3 rounded-md border p-4 md:grid-cols-2 xl:grid-cols-4">
          {facetFields.map((campo) => (
            <DynamicFilter
              key={campo.id}
              campo={campo}
              options={facetOptions[campo.chave] ?? []}
              value={draftFilters[campo.chave]}
              onChange={(value) => setDraftFilters((current) => ({ ...current, [campo.chave]: value }))}
            />
          ))}
          {metadataFields.map((campo) => (
            <DynamicFilter
              key={campo.id}
              campo={campo}
              options={optionsFrom(campo)}
              value={draftFilters[campo.chave]}
              onChange={(value) => setDraftFilters((current) => ({ ...current, [campo.chave]: value }))}
            />
          ))}
          <SelectFilter label="Ordenacao" value={draftSort} onChange={setDraftSort}>
            <option value="">Mais recentes</option>
            {sortFields.flatMap((campo) => [
              <option key={`${campo.chave}:asc`} value={`${campo.chave}:asc`}>{campo.nome} asc</option>,
              <option key={`${campo.chave}:desc`} value={`${campo.chave}:desc`}>{campo.nome} desc</option>,
            ])}
          </SelectFilter>
          <div className="flex items-end gap-2">
            <Button type="button" onClick={submitSearch}>
              <Search className="h-4 w-4" />
              Pesquisar
            </Button>
            <Button type="button" variant="outline" onClick={clearFilters}>
              Limpar filtros
            </Button>
          </div>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-md border">
        {searchQuery.error ? <p className="p-6 text-sm text-destructive">{searchQuery.error.message}</p> : null}
        <ResultsTable registros={registros} columns={columns} />
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        displayedCount={registros.length}
        total={total}
        isLoading={searchQuery.isFetching}
        onPageChange={setPageIndex}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPageIndex(0);
        }}
      />
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
      <SelectFilter
        label={campo.nome}
        value={Array.isArray(value) ? String(value[0] ?? "") : ""}
        onChange={(selected) => onChange(selected ? [selected] : [])}
      >
        <option value="">Todos</option>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </SelectFilter>
    );
  }

  if (campo.tipo === "UNIDADE_ACONDICIONAMENTO" || campo.tipo === "MIDIA_ARMAZENAMENTO") {
    const reference = referenceFrom(value);
    const label = campo.tipo === "UNIDADE_ACONDICIONAMENTO" ? "unidade de acondicionamento" : "mídia de armazenamento";

    return (
      <FilterField label={campo.nome}>
        <ReferenceFilter
          tipo={campo.tipo}
          label={label}
          value={reference}
          onChange={onChange}
        />
      </FilterField>
    );
  }

  if (campo.tipo === "BOOLEANO") {
    return (
      <SelectFilter
        label={campo.nome}
        value={typeof value === "boolean" ? String(value) : ""}
        onChange={(selected) => onChange(selected === "" ? "" : selected === "true")}
      >
        <option value="">Todos</option>
        <option value="true">Sim</option>
        <option value="false">Não</option>
      </SelectFilter>
    );
  }

  if (campo.tipo === "DATA" || campo.tipo === "PERIODO" || campo.tipo === "NUMERO") {
    const range = typeof value === "object" && value ? value as Record<string, string> : {};
    return (
      <FilterField label={campo.nome}>
        <div className="grid grid-cols-2 gap-2">
          <Input placeholder="De" value={range.gte ?? ""} onChange={(event) => onChange({ ...range, gte: event.target.value })} />
          <Input placeholder="Ate" value={range.lte ?? ""} onChange={(event) => onChange({ ...range, lte: event.target.value })} />
        </div>
      </FilterField>
    );
  }

  return (
    <FilterField label={campo.nome}>
      <Input value={filterTextValue(value)} onChange={(event) => onChange(event.target.value ? [event.target.value] : [])} />
    </FilterField>
  );
}

function FilterField({ label, children }: { label: string; children: ReactNode }) {
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
  children: ReactNode;
}) {
  return (
    <FilterField label={label}>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
    </FilterField>
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
        {registros.length ? (
          registros.map((registro) => (
            <TableRow key={registro.id}>
              {columns.map((campo) => <TableCell key={campo.id}>{formatCampoValue(campo, registro.dados[campo.chave])}</TableCell>)}
              <TableCell>{registro.status}</TableCell>
              <TableCell>{formatDateTime(registro.atualizado_em)}</TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={columns.length + 2} className="h-24 text-center text-muted-foreground">Nenhum registro encontrado.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
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
  const pages = getPaginationItems(currentPage, totalPages);

  return (
    <div className="flex flex-col gap-3 rounded-md border px-3 py-2">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <p className="text-sm text-muted-foreground">
          {displayedCount} registros de {total} | pagina {currentPage} de {totalPages}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(0)}>
            Primeira
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage <= 1} onClick={() => onPageChange(currentPage - 2)}>
            Anterior
          </Button>
          {pages.map((page, index) =>
            page === "ellipsis" ? (
              <span key={`ellipsis-${index}`} className="flex h-9 min-w-9 items-center justify-center px-2 text-sm text-muted-foreground">
                ...
              </span>
            ) : (
              <Button key={page} type="button" variant={page === currentPage ? "default" : "outline"} size="sm" className="min-w-9 px-2" disabled={isLoading || page === currentPage} onClick={() => onPageChange(page - 1)}>
                {page}
              </Button>
            ),
          )}
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(currentPage)}>
            Proxima
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={isLoading || currentPage >= totalPages} onClick={() => onPageChange(totalPages - 1)}>
            Ultima
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Label htmlFor="instrumento-registros-page-size" className="text-sm text-muted-foreground">
          Registros por pagina:
        </Label>
        <select
          id="instrumento-registros-page-size"
          className="h-9 rounded-md border bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}

function getPaginationItems(currentPage: number, totalPages: number) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  return sortedPages.flatMap((page, index) => {
    const previousPage = sortedPages[index - 1];
    if (previousPage && page - previousPage > 1) return ["ellipsis" as const, page];
    return [page];
  });
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

function normalizeFilters(filters: Record<string, unknown>, campos: InstrumentoCampoSchema[]) {
  const camposPorChave = new Map(campos.map((campo) => [campo.chave, campo]));

  return Object.fromEntries(
    Object.entries(filters).map(([chave, value]) => {
      const campo = camposPorChave.get(chave);
      if (campo?.tipo === "UNIDADE_ACONDICIONAMENTO" || campo?.tipo === "MIDIA_ARMAZENAMENTO") {
        return [chave, referenceFrom(value)?.id ?? value];
      }
      return [chave, value];
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
  const reference = referenceFrom(value);
  if (reference) return reference.rotulo;
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function formatCampoValue(campo: InstrumentoCampoSchema, value: unknown) {
  if (campo.tipo === "UNIDADE_ACONDICIONAMENTO") {
    const reference = referenceFrom(value);
    return reference ? (
      <Link href={`/unidades/${reference.id}`} className="font-medium text-primary hover:underline">
        {reference.rotulo}
      </Link>
    ) : formatValue(value);
  }

  if (campo.tipo === "MIDIA_ARMAZENAMENTO") {
    const reference = referenceFrom(value);
    return reference ? (
      <Link href={`/midias/${reference.id}`} className="font-medium text-primary hover:underline">
        {reference.rotulo}
      </Link>
    ) : formatValue(value);
  }

  return formatValue(value);
}

function ReferenceFilter({
  tipo,
  label,
  value,
  onChange,
}: {
  tipo: InstrumentoCampoSchema["tipo"];
  label: string;
  value: DynamicReferenceValue | null;
  onChange: (value: unknown) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="flex gap-2">
        <Input readOnly value={value?.rotulo ?? ""} placeholder={`Selecione uma ${label}`} />
        <Button type="button" variant="outline" size="icon" title={`Pesquisar ${label}`} onClick={() => setOpen(true)}>
          <Search className="h-4 w-4" />
        </Button>
        {value ? (
          <Button type="button" variant="outline" onClick={() => onChange("")}>
            Limpar
          </Button>
        ) : null}
      </div>
      <ReferenceLookupDialog
        open={open}
        tipo={tipo}
        title={`Pesquisar ${label}`}
        onOpenChange={setOpen}
        onSelect={(reference) => {
          onChange(reference);
          setOpen(false);
        }}
      />
    </>
  );
}

type DynamicReferenceValue = {
  id: number;
  rotulo: string;
};

function ReferenceLookupDialog({
  open,
  tipo,
  title,
  onOpenChange,
  onSelect,
}: {
  open: boolean;
  tipo: InstrumentoCampoSchema["tipo"];
  title: string;
  onOpenChange: (open: boolean) => void;
  onSelect: (reference: DynamicReferenceValue) => void;
}) {
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const isUnidade = tipo === "UNIDADE_ACONDICIONAMENTO";
  const query = useQuery<UnidadePage | MidiaPage>({
    queryKey: ["instrumento-advanced-lookup", tipo, searchTerm],
    queryFn: () =>
      isUnidade
        ? listUnidadesPage({ limit: 10, filters: { q: searchTerm } })
        : listMidiasPage({ limit: 10, filters: { q: searchTerm } }),
    enabled: open,
  });
  const items = query.data?.items ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>Busque e selecione um registro cadastrado.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setSearchTerm(searchInput.trim());
            }}
          >
            <Input value={searchInput} placeholder="Buscar" onChange={(event) => setSearchInput(event.target.value)} />
            <Button type="submit">
              <Search className="h-4 w-4" />
              Buscar
            </Button>
          </form>
          {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
          <div className="max-h-80 overflow-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Identificação</TableHead>
                  <TableHead>Descrição</TableHead>
                  <TableHead className="text-right">Ação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => {
                  const reference = isUnidade
                    ? unidadeReference(item as UnidadeAcondicionamento)
                    : midiaReference(item as MidiaArmazenamento);

                  return (
                    <TableRow key={reference.id}>
                      <TableCell className="font-medium">{reference.rotulo}</TableCell>
                      <TableCell>{itemDescription(item, isUnidade)}</TableCell>
                      <TableCell className="text-right">
                        <Button type="button" size="sm" onClick={() => onSelect(reference)}>
                          Selecionar
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {!query.isLoading && !items.length ? (
                  <TableRow>
                    <TableCell colSpan={3} className="h-20 text-center text-muted-foreground">
                      Nenhum registro encontrado.
                    </TableCell>
                  </TableRow>
                ) : null}
                {query.isLoading ? (
                  <TableRow>
                    <TableCell colSpan={3} className="h-20 text-center text-muted-foreground">
                      Carregando...
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function referenceFrom(value: unknown): DynamicReferenceValue | null {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    const id = Number(record.id);
    const rotulo = String(record.rotulo ?? record.label ?? record.nome ?? record.identificador ?? id);
    if (Number.isFinite(id) && id > 0 && rotulo) return { id, rotulo };
  }
  const id = Number(value);
  if (Number.isFinite(id) && id > 0) return { id, rotulo: String(id) };
  return null;
}

function unidadeReference(unidade: UnidadeAcondicionamento): DynamicReferenceValue {
  return {
    id: unidade.id,
    rotulo: `${unidade.identificador} - ${unidade.titulo}`,
  };
}

function midiaReference(midia: MidiaArmazenamento): DynamicReferenceValue {
  return {
    id: midia.id,
    rotulo: midia.nome,
  };
}

function itemDescription(item: UnidadeAcondicionamento | MidiaArmazenamento, isUnidade: boolean) {
  if (isUnidade) {
    const unidade = item as UnidadeAcondicionamento;
    return unidade.produtor || unidade.tipo_unidade || "-";
  }
  const midia = item as MidiaArmazenamento;
  return midia.descricao || midia.tipo_midia?.nome || "-";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
