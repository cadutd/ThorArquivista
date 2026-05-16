"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  atualizarModeloFichaEspelho,
  criarModeloFichaEspelho,
} from "@/lib/api/ficha-espelho";
import {
  campoFichaEspelhoLabels,
  camposFichaEspelhoPadrao,
  type CampoFichaEspelho,
  type ModeloFichaEspelho,
  type ModeloFichaEspelhoPayload,
} from "@/types/ficha-espelho";

const schema = z
  .object({
    nome: z.string().min(2, "Informe ao menos 2 caracteres.").max(255),
    descricao: z.string().max(2000).optional(),
    campos: z.array(z.enum(camposFichaEspelhoPadrao as [CampoFichaEspelho, ...CampoFichaEspelho[]])).min(1, "Selecione ao menos um campo."),
    tamanho_papel: z.enum(["A4", "CARTA"]),
    orientacao: z.enum(["RETRATO", "PAISAGEM"]),
    colunas: z.number().int().min(1).max(2),
    largura_cm: z.number().positive("Informe a largura.").max(200),
    altura_cm: z.number().positive("Informe a altura.").max(200),
    ativo: z.boolean(),
  })
  .superRefine((values, ctx) => {
    const limits = getPrintableLimits(values.tamanho_papel, values.orientacao, values.colunas);
    if (values.largura_cm > limits.maxWidthCm) {
      ctx.addIssue({
        code: "custom",
        path: ["largura_cm"],
        message: `Máximo para esta configuração: ${limits.maxWidthCm} cm.`,
      });
    }
    if (values.altura_cm > limits.maxHeightCm) {
      ctx.addIssue({
        code: "custom",
        path: ["altura_cm"],
        message: `Máximo para esta configuração: ${limits.maxHeightCm} cm.`,
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  nome: "",
  descricao: "",
  campos: camposFichaEspelhoPadrao,
  tamanho_papel: "A4",
  orientacao: "RETRATO",
  colunas: 1,
  largura_cm: 18.6,
  altura_cm: 27.3,
  ativo: true,
};

export function ModeloFichaForm({
  modelo,
  onSaved,
}: {
  modelo?: ModeloFichaEspelho;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(modelo);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: modelo ? toFormValues(modelo) : defaultValues,
  });
  // eslint-disable-next-line react-hooks/incompatible-library
  const selectedFields = form.watch("campos");
  // eslint-disable-next-line react-hooks/incompatible-library
  const paper = form.watch("tamanho_papel");
  // eslint-disable-next-line react-hooks/incompatible-library
  const orientation = form.watch("orientacao");
  // eslint-disable-next-line react-hooks/incompatible-library
  const columns = form.watch("colunas");
  const limits = getPrintableLimits(paper, orientation, columns || 1);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload: ModeloFichaEspelhoPayload = {
        nome: values.nome.trim(),
        descricao: values.descricao?.trim() || null,
        campos: values.campos,
        tamanho_papel: values.tamanho_papel,
        orientacao: values.orientacao,
        colunas: values.colunas,
        largura_cm: values.largura_cm,
        altura_cm: values.altura_cm,
        ativo: values.ativo,
      };
      return modelo ? atualizarModeloFichaEspelho(modelo.id, payload) : criarModeloFichaEspelho(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["fichas-espelho", "modelos"] });
      onSaved?.();
    },
  });

  const toggleField = (field: CampoFichaEspelho) => {
    const current = form.getValues("campos");
    form.setValue(
      "campos",
      current.includes(field) ? current.filter((item) => item !== field) : [...current, field],
      { shouldDirty: true, shouldValidate: true },
    );
  };

  return (
    <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Nome" error={form.formState.errors.nome?.message} required>
          <Input {...form.register("nome")} />
        </Field>
        <Field label="Status">
          <label className="flex h-10 items-center gap-2 rounded-md border px-3 text-sm">
            <input type="checkbox" {...form.register("ativo")} />
            Modelo ativo
          </label>
        </Field>
      </div>

      <Field label="Descrição" error={form.formState.errors.descricao?.message}>
        <textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" {...form.register("descricao")} />
      </Field>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SelectField label="Papel" {...form.register("tamanho_papel")}>
          <option value="A4">A4</option>
          <option value="CARTA">Carta</option>
        </SelectField>
        <SelectField label="Orientação" {...form.register("orientacao")}>
          <option value="RETRATO">Retrato</option>
          <option value="PAISAGEM">Paisagem</option>
        </SelectField>
        <Field label="Largura do modelo (cm)" error={form.formState.errors.largura_cm?.message} required>
          <Input type="number" step="0.1" min="0.1" max={limits.maxWidthCm} {...form.register("largura_cm", { valueAsNumber: true })} />
        </Field>
        <Field label="Altura do modelo (cm)" error={form.formState.errors.altura_cm?.message} required>
          <Input type="number" step="0.1" min="0.1" max={limits.maxHeightCm} {...form.register("altura_cm", { valueAsNumber: true })} />
        </Field>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Colunas por página" error={form.formState.errors.colunas?.message} required>
          <Input type="number" min="1" max="2" {...form.register("colunas", { valueAsNumber: true })} />
        </Field>
        <div className="rounded-md border p-3 text-sm">
          <p className="text-muted-foreground">Dimensão final</p>
          <p className="mt-1 font-semibold">
            {form.watch("largura_cm") || 0} cm x {form.watch("altura_cm") || 0} cm
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Máximo nesta configuração: {limits.maxWidthCm} cm x {limits.maxHeightCm} cm.
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <RequiredLabel required>Campos da ficha</RequiredLabel>
        <div className="grid gap-2 md:grid-cols-2">
          {camposFichaEspelhoPadrao.map((field) => (
            <label key={field} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
              <input type="checkbox" checked={selectedFields.includes(field)} onChange={() => toggleField(field)} />
              {campoFichaEspelhoLabels[field]}
            </label>
          ))}
        </div>
        {form.formState.errors.campos?.message ? (
          <p className="text-xs text-destructive">{form.formState.errors.campos.message}</p>
        ) : null}
      </div>

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending}>
        <Save className="h-4 w-4" />
        {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Salvar modelo"}
      </Button>
    </form>
  );
}

function getPrintableLimits(
  paper: "A4" | "CARTA",
  orientation: "RETRATO" | "PAISAGEM",
  columns: number,
) {
  const base = paper === "CARTA" ? { widthCm: 21.59, heightCm: 27.94 } : { widthCm: 21, heightCm: 29.7 };
  const page = orientation === "PAISAGEM" ? { widthCm: base.heightCm, heightCm: base.widthCm } : base;
  const marginCm = 1.2;
  const gapCm = 0.2;
  const safeColumns = Math.max(1, Math.min(2, columns || 1));
  const printableWidth = page.widthCm - marginCm * 2;
  const printableHeight = page.heightCm - marginCm * 2;
  return {
    maxWidthCm: roundCm((printableWidth - gapCm * (safeColumns - 1)) / safeColumns),
    maxHeightCm: roundCm(printableHeight),
  };
}

function roundCm(value: number) {
  return Math.floor(value * 10) / 10;
}

function toFormValues(modelo: ModeloFichaEspelho): FormValues {
  return {
    nome: modelo.nome,
    descricao: modelo.descricao ?? "",
    campos: modelo.campos,
    tamanho_papel: modelo.tamanho_papel,
    orientacao: modelo.orientacao,
    colunas: modelo.colunas,
    largura_cm: modelo.largura_cm,
    altura_cm: modelo.altura_cm,
    ativo: modelo.ativo,
  };
}

function Field({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <RequiredLabel required={required}>{label}</RequiredLabel>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function RequiredLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <Label>
      {children}
      {required ? <span className="ml-1 text-destructive">*</span> : null}
    </Label>
  );
}

function SelectField({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" {...props}>
        {children}
      </select>
    </div>
  );
}
