"use client";

import { useMemo, useState } from "react";
import { CircleHelp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { InstrumentoCampoSchema, InstrumentoPesquisaSchema } from "@/types/domain";

export type DynamicValue = string | number | boolean | string[];
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
  return typeof value === "string" ? value : "";
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
