"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CircleHelp, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listMidiasPage, listUnidadesPage, type MidiaPage, type UnidadePage } from "@/lib/api/domain";
import type { InstrumentoCampoSchema, InstrumentoPesquisaSchema, MidiaArmazenamento, UnidadeAcondicionamento } from "@/types/domain";

export type DynamicReferenceValue = {
  id: number;
  rotulo: string;
};
export type DynamicValue = string | number | boolean | string[] | DynamicReferenceValue;
export type DynamicValues = Record<string, DynamicValue>;

export function DynamicInstrumentForm({
  schema,
  initialValues,
  submitLabel = "Salvar registro",
  isSaving,
  onSubmit,
}: {
  schema: InstrumentoPesquisaSchema;
  initialValues?: Record<string, unknown>;
  submitLabel?: string;
  isSaving?: boolean;
  onSubmit?: (values: DynamicValues) => void;
}) {
  const normalizedInitialValues = useMemo(
    () => buildInitialValues(schema.campos, initialValues),
    [schema.campos, initialValues],
  );
  const [values, setValues] = useState<DynamicValues>(normalizedInitialValues);

  return (
    <form
      className="grid gap-4 sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit?.(values);
      }}
    >
      {schema.campos
        .filter((campo) => campo.aparece_cadastro)
        .map((campo) => (
          <DynamicField
            key={campo.id}
            campo={campo}
            value={values[campo.chave]}
            onChange={(value) => setValues((current) => ({ ...current, [campo.chave]: value }))}
          />
      ))}
      <div className="sm:col-span-2">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? "Salvando..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}

function DynamicField({
  campo,
  value,
  onChange,
}: {
  campo: InstrumentoCampoSchema;
  value: DynamicValue | undefined;
  onChange: (value: DynamicValue) => void;
}) {
  const common = {
    id: campo.chave,
    name: campo.chave,
    required: campo.obrigatorio,
    placeholder: campo.placeholder ?? undefined,
  };

  if (campo.tipo === "BOOLEANO") {
    return (
      <div className="flex items-center gap-3 rounded-md border px-3 py-2">
        <input
          id={campo.chave}
          name={campo.chave}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
        />
        <FieldText campo={campo} />
      </div>
    );
  }

  return (
    <div className={campo.tipo === "TEXTO_LONGO" ? "space-y-2 sm:col-span-2" : "space-y-2"}>
      <FieldText campo={campo} />
      {campo.tipo === "TEXTO_LONGO" ? (
        <textarea
          {...common}
          className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={String(value ?? "")}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : campo.tipo === "LISTA_SIMPLES" ? (
        <SelectInput campo={campo} value={String(value ?? "")} onChange={onChange} />
      ) : campo.tipo === "LISTA_MULTIPLA" ? (
        <MultiSelectInput campo={campo} value={Array.isArray(value) ? value : []} onChange={onChange} />
      ) : campo.tipo === "UNIDADE_ACONDICIONAMENTO" || campo.tipo === "MIDIA_ARMAZENAMENTO" ? (
        <ReferenceLookupField
          campo={campo}
          value={referenceFrom(value)}
          onChange={onChange}
        />
      ) : (
        <Input
          {...common}
          type={inputType(campo)}
          value={String(value ?? "")}
          onChange={(event) => onChange(campo.tipo === "NUMERO" && event.target.value !== "" ? Number(event.target.value) : event.target.value)}
        />
      )}
    </div>
  );
}

function FieldText({ campo }: { campo: InstrumentoCampoSchema }) {
  const help = contextualHelp(campo);

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Label htmlFor={campo.chave}>
          {campo.nome}
          {campo.obrigatorio ? <span className="ml-1 text-destructive">*</span> : null}
        </Label>
        <span title={help}>
          <CircleHelp className="h-4 w-4 text-muted-foreground" aria-label={help} />
        </span>
      </div>
      {campo.ajuda ? <p className="text-xs text-muted-foreground">{campo.ajuda}</p> : null}
    </div>
  );
}

function SelectInput({
  campo,
  value,
  onChange,
}: {
  campo: InstrumentoCampoSchema;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <select
      id={campo.chave}
      name={campo.chave}
      required={campo.obrigatorio}
      className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">Selecione</option>
      {optionsFrom(campo).map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function MultiSelectInput({
  campo,
  value,
  onChange,
}: {
  campo: InstrumentoCampoSchema;
  value: string[];
  onChange: (value: string[]) => void;
}) {
  return (
    <div className="grid gap-2 rounded-md border p-3">
      {optionsFrom(campo).map((option) => (
        <label key={option.value} className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={value.includes(option.value)}
            onChange={(event) => {
              if (event.target.checked) {
                onChange([...value, option.value]);
              } else {
                onChange(value.filter((item) => item !== option.value));
              }
            }}
          />
          {option.label}
        </label>
      ))}
    </div>
  );
}

function inputType(campo: InstrumentoCampoSchema) {
  if (campo.tipo === "NUMERO") return "number";
  if (campo.tipo === "DATA") return "date";
  if (campo.tipo === "URL") return "url";
  return "text";
}

function buildInitialValues(campos: InstrumentoCampoSchema[], values?: Record<string, unknown>): DynamicValues {
  return campos.reduce<DynamicValues>((acc, campo) => {
    acc[campo.chave] = normalizeValue(campo, values?.[campo.chave]);
    return acc;
  }, {});
}

function normalizeValue(campo: InstrumentoCampoSchema, value: unknown): DynamicValue {
  if (campo.tipo === "BOOLEANO") return typeof value === "boolean" ? value : false;
  if (campo.tipo === "LISTA_MULTIPLA") return Array.isArray(value) ? value.map(String) : [];
  if (campo.tipo === "NUMERO") return typeof value === "number" ? value : "";
  if (campo.tipo === "UNIDADE_ACONDICIONAMENTO" || campo.tipo === "MIDIA_ARMAZENAMENTO") {
    return referenceFrom(value) ?? "";
  }
  return typeof value === "string" ? value : "";
}

function ReferenceLookupField({
  campo,
  value,
  onChange,
}: {
  campo: InstrumentoCampoSchema;
  value?: DynamicReferenceValue;
  onChange: (value: DynamicValue) => void;
}) {
  const [open, setOpen] = useState(false);
  const label = campo.tipo === "UNIDADE_ACONDICIONAMENTO" ? "unidade de acondicionamento" : "mídia de armazenamento";

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          id={campo.chave}
          name={campo.chave}
          required={campo.obrigatorio}
          readOnly
          value={value?.rotulo ?? ""}
          placeholder={`Selecione uma ${label}`}
        />
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
        tipo={campo.tipo}
        title={`Pesquisar ${label}`}
        onOpenChange={setOpen}
        onSelect={(reference) => {
          onChange(reference);
          setOpen(false);
        }}
      />
    </div>
  );
}

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
    queryKey: ["instrumento-lookup", tipo, searchTerm],
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
            <Input
              value={searchInput}
              placeholder="Buscar"
              onChange={(event) => setSearchInput(event.target.value)}
            />
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

function referenceFrom(value: unknown): DynamicReferenceValue | undefined {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    const id = Number(record.id);
    const rotulo = String(record.rotulo ?? record.label ?? record.nome ?? record.identificador ?? id);
    if (Number.isFinite(id) && rotulo) return { id, rotulo };
  }
  const id = Number(value);
  if (Number.isFinite(id) && id > 0) return { id, rotulo: String(id) };
  return undefined;
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

function contextualHelp(campo: InstrumentoCampoSchema) {
  return [
    campo.ajuda,
    campo.placeholder ? `Placeholder: ${campo.placeholder}` : null,
    `Tipo de dado: ${campo.tipo}`,
    campo.obrigatorio ? "Obrigatório" : "Opcional",
  ]
    .filter(Boolean)
    .join("\n");
}
