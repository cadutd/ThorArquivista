"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createEntidadeProdutora,
  listEntidadesProdutoras,
  updateEntidadeProdutora,
} from "@/lib/api/entidades-produtoras";
import type { EntidadeProdutora, TipoEntidadeProdutora } from "@/types/domain";

const tipoEntidadeValues = [
  "ORGAO_PUBLICO",
  "UNIDADE_ADMINISTRATIVA",
  "EMPRESA_PUBLICA",
  "EMPRESA_PRIVADA",
  "PESSOA_FISICA",
  "FAMILIA",
  "COMISSAO",
  "GRUPO_TRABALHO",
  "FUNDO",
  "COLECAO",
  "OUTRO",
] as const;

const schema = z
  .object({
    nome: z.string().trim().min(1, "Informe o nome.").max(255),
    sigla: z.string().max(50).optional(),
    codigo_referencia: z.string().max(100).optional(),
    tipo_entidade: z.enum(tipoEntidadeValues),
    natureza_juridica: z.string().max(100).optional(),
    id_entidade_superior: z.string().optional(),
    data_inicio: z.string().optional(),
    data_fim: z.string().optional(),
    entidade_ativa: z.boolean(),
    historico: z.string().optional(),
    competencias_funcoes: z.string().optional(),
    observacoes: z.string().optional(),
    email: z.string().email("Informe um e-mail válido.").or(z.literal("")).optional(),
    telefone: z.string().max(50).optional(),
    site: z.string().max(255).optional(),
    endereco_logradouro: z.string().max(255).optional(),
    endereco_numero: z.string().max(50).optional(),
    endereco_complemento: z.string().max(100).optional(),
    endereco_bairro: z.string().max(100).optional(),
    endereco_municipio: z.string().max(100).optional(),
    endereco_uf: z.string().max(2, "UF deve ter até dois caracteres.").optional(),
    endereco_cep: z.string().max(20).optional(),
    endereco_pais: z.string().max(100).optional(),
  })
  .superRefine((values, ctx) => {
    if (values.data_inicio && values.data_fim && values.data_fim < values.data_inicio) {
      ctx.addIssue({
        code: "custom",
        path: ["data_fim"],
        message: "Data final não pode ser anterior à data inicial.",
      });
    }
    if (values.data_fim && values.entidade_ativa && !values.observacoes?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["observacoes"],
        message: "Justifique para manter ativa uma entidade com data final.",
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  nome: "",
  sigla: "",
  codigo_referencia: "",
  tipo_entidade: "ORGAO_PUBLICO",
  natureza_juridica: "",
  id_entidade_superior: "",
  data_inicio: "",
  data_fim: "",
  entidade_ativa: true,
  historico: "",
  competencias_funcoes: "",
  observacoes: "",
  email: "",
  telefone: "",
  site: "",
  endereco_logradouro: "",
  endereco_numero: "",
  endereco_complemento: "",
  endereco_bairro: "",
  endereco_municipio: "",
  endereco_uf: "",
  endereco_cep: "",
  endereco_pais: "Brasil",
};

export const tipoEntidadeOptions: Array<{ value: TipoEntidadeProdutora; label: string }> =
  tipoEntidadeValues.map((value) => ({
    value,
    label: value.replaceAll("_", " "),
  }));

export function EntidadeProdutoraForm({
  entidade,
  onSaved,
}: {
  entidade?: EntidadeProdutora;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(entidade);
  const superiores = useQuery({
    queryKey: ["entidades-produtoras", "lookup"],
    queryFn: listEntidadesProdutoras,
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (!entidade) {
      form.reset(defaultValues);
      return;
    }
    form.reset({
      ...defaultValues,
      ...toFormValues(entidade),
    });
  }, [entidade, form]);

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (entidade && values.id_entidade_superior === entidade.id) {
        throw new Error("A entidade superior não pode ser a própria entidade.");
      }
      const payload = toPayload(values);
      return entidade
        ? updateEntidadeProdutora(entidade.id, payload)
        : createEntidadeProdutora(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["entidades-produtoras"] });
      onSaved?.();
    },
  });

  return (
    <form className="space-y-6" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <FormSection title="Identificação">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nome" error={form.formState.errors.nome?.message} required>
            <Input {...form.register("nome")} required />
          </Field>
          <Field label="Sigla" error={form.formState.errors.sigla?.message}>
            <Input {...form.register("sigla")} />
          </Field>
          <Field label="Código de referência" error={form.formState.errors.codigo_referencia?.message}>
            <Input {...form.register("codigo_referencia")} />
          </Field>
          <SelectField label="Tipo de entidade" error={form.formState.errors.tipo_entidade?.message} {...form.register("tipo_entidade")} required>
            {tipoEntidadeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </SelectField>
          <Field label="Natureza jurídica" error={form.formState.errors.natureza_juridica?.message}>
            <Input {...form.register("natureza_juridica")} />
          </Field>
          <SelectField label="Entidade superior" error={form.formState.errors.id_entidade_superior?.message} {...form.register("id_entidade_superior")}>
            <option value="">Nenhuma</option>
            {(superiores.data ?? [])
              .filter((item) => item.id !== entidade?.id)
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
          </SelectField>
        </div>
      </FormSection>

      <FormSection title="Temporalidade">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Data de início" error={form.formState.errors.data_inicio?.message}>
            <Input type="date" {...form.register("data_inicio")} />
          </Field>
          <Field label="Data de fim" error={form.formState.errors.data_fim?.message}>
            <Input type="date" {...form.register("data_fim")} />
          </Field>
          <label className="flex items-center gap-2 pt-8 text-sm font-medium">
            <input type="checkbox" {...form.register("entidade_ativa")} />
            Entidade ativa
          </label>
        </div>
      </FormSection>

      <FormSection title="Histórico e funções">
        <div className="grid gap-4">
          <TextAreaField label="Histórico" error={form.formState.errors.historico?.message} {...form.register("historico")} />
          <TextAreaField label="Competências/Funções" error={form.formState.errors.competencias_funcoes?.message} {...form.register("competencias_funcoes")} />
          <TextAreaField label="Observações" error={form.formState.errors.observacoes?.message} {...form.register("observacoes")} />
        </div>
      </FormSection>

      <FormSection title="Contato">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="E-mail" error={form.formState.errors.email?.message}>
            <Input type="email" {...form.register("email")} />
          </Field>
          <Field label="Telefone" error={form.formState.errors.telefone?.message}>
            <Input {...form.register("telefone")} />
          </Field>
          <Field label="Site" error={form.formState.errors.site?.message}>
            <Input {...form.register("site")} />
          </Field>
        </div>
      </FormSection>

      <FormSection title="Endereço">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Logradouro" error={form.formState.errors.endereco_logradouro?.message}>
            <Input {...form.register("endereco_logradouro")} />
          </Field>
          <Field label="Número" error={form.formState.errors.endereco_numero?.message}>
            <Input {...form.register("endereco_numero")} />
          </Field>
          <Field label="Complemento" error={form.formState.errors.endereco_complemento?.message}>
            <Input {...form.register("endereco_complemento")} />
          </Field>
          <Field label="Bairro" error={form.formState.errors.endereco_bairro?.message}>
            <Input {...form.register("endereco_bairro")} />
          </Field>
          <Field label="Município" error={form.formState.errors.endereco_municipio?.message}>
            <Input {...form.register("endereco_municipio")} />
          </Field>
          <Field label="UF" error={form.formState.errors.endereco_uf?.message}>
            <Input maxLength={2} {...form.register("endereco_uf")} />
          </Field>
          <Field label="CEP" error={form.formState.errors.endereco_cep?.message}>
            <Input {...form.register("endereco_cep")} />
          </Field>
          <Field label="País" error={form.formState.errors.endereco_pais?.message}>
            <Input {...form.register("endereco_pais")} />
          </Field>
        </div>
      </FormSection>

      {mutation.data?.avisos_duplicidade?.length ? (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          {mutation.data.avisos_duplicidade.map((aviso) => (
            <p key={aviso}>{aviso}</p>
          ))}
        </div>
      ) : null}
      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Salvar entidade produtora"}
      </Button>
    </form>
  );
}

function toFormValues(entidade: EntidadeProdutora): Partial<FormValues> {
  return {
    nome: entidade.nome,
    sigla: entidade.sigla ?? "",
    codigo_referencia: entidade.codigo_referencia ?? "",
    tipo_entidade: entidade.tipo_entidade,
    natureza_juridica: entidade.natureza_juridica ?? "",
    id_entidade_superior: entidade.id_entidade_superior ?? "",
    data_inicio: entidade.data_inicio ?? "",
    data_fim: entidade.data_fim ?? "",
    entidade_ativa: entidade.entidade_ativa,
    historico: entidade.historico ?? "",
    competencias_funcoes: entidade.competencias_funcoes ?? "",
    observacoes: entidade.observacoes ?? "",
    email: entidade.email ?? "",
    telefone: entidade.telefone ?? "",
    site: entidade.site ?? "",
    endereco_logradouro: entidade.endereco_logradouro ?? "",
    endereco_numero: entidade.endereco_numero ?? "",
    endereco_complemento: entidade.endereco_complemento ?? "",
    endereco_bairro: entidade.endereco_bairro ?? "",
    endereco_municipio: entidade.endereco_municipio ?? "",
    endereco_uf: entidade.endereco_uf ?? "",
    endereco_cep: entidade.endereco_cep ?? "",
    endereco_pais: entidade.endereco_pais ?? "Brasil",
  };
}

function toPayload(values: FormValues) {
  const stringFields = Object.fromEntries(
    Object.entries(values).map(([key, value]) => [
      key,
      typeof value === "string" ? value.trim() || null : value,
    ]),
  );
  return {
    ...stringFields,
    nome: values.nome.trim(),
    tipo_entidade: values.tipo_entidade,
    entidade_ativa: values.entidade_ativa,
  };
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-base font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Field({ label, error, children, required }: { label: string; error?: string; children: React.ReactNode; required?: boolean }) {
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
  error,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string }) {
  return (
    <div className="space-y-2">
      <RequiredLabel required={props.required}>{label}</RequiredLabel>
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props}>
        {children}
      </select>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function TextAreaField({
  label,
  error,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <textarea className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props} />
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
