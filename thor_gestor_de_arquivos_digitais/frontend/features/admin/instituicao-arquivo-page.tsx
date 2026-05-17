"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Edit, Plus, Save, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  atualizarInstituicaoArquivo,
  criarInstituicaoArquivo,
  excluirInstituicaoArquivo,
  obterInstituicaoArquivo,
  type EsferaAdministrativa,
  type InstituicaoArquivo,
  type InstituicaoArquivoPayload,
} from "@/lib/api/admin";

const esferaOptions: Array<{ value: EsferaAdministrativa; label: string }> = [
  { value: "FEDERAL", label: "Federal" },
  { value: "ESTADUAL", label: "Estadual" },
  { value: "DISTRITAL", label: "Distrital" },
  { value: "MUNICIPAL", label: "Municipal" },
  { value: "PRIVADA", label: "Privada" },
  { value: "COMUNITARIA", label: "Comunitária" },
  { value: "UNIVERSITARIA", label: "Universitária" },
  { value: "OUTRA", label: "Outra" },
];

const emailSchema = z.string().email("Informe um e-mail válido.").or(z.literal(""));
const cnpjSchema = z.string().superRefine((value, ctx) => {
  if (!value.trim()) {
    return;
  }
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 14 || digits === digits[0].repeat(14) || !isValidCnpj(digits)) {
    ctx.addIssue({ code: "custom", message: "Informe um CNPJ válido." });
  }
});

const schema = z.object({
  nome: z.string().trim().min(1, "Informe o nome.").max(255),
  sigla: z.string().max(50).optional(),
  codigo_referencia: z.string().max(100).optional(),
  natureza_juridica: z.string().max(100).optional(),
  esfera_administrativa: z.enum(["FEDERAL", "ESTADUAL", "DISTRITAL", "MUNICIPAL", "PRIVADA", "COMUNITARIA", "UNIVERSITARIA", "OUTRA"]).or(z.literal("")),
  cnpj: cnpjSchema,
  email: emailSchema,
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
  responsavel_nome: z.string().max(255).optional(),
  responsavel_cargo: z.string().max(255).optional(),
  responsavel_email: emailSchema,
  responsavel_telefone: z.string().max(50).optional(),
  historico: z.string().optional(),
  missao: z.string().optional(),
  observacoes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  nome: "",
  sigla: "",
  codigo_referencia: "",
  natureza_juridica: "",
  esfera_administrativa: "",
  cnpj: "",
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
  responsavel_nome: "",
  responsavel_cargo: "",
  responsavel_email: "",
  responsavel_telefone: "",
  historico: "",
  missao: "",
  observacoes: "",
};

export function InstituicaoArquivoPage() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"view" | "form">("view");
  const query = useQuery({
    queryKey: ["admin", "instituicao-arquivo"],
    queryFn: obterInstituicaoArquivo,
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (query.data) {
      form.reset(toFormValues(query.data));
    } else {
      form.reset(defaultValues);
    }
  }, [form, query.data]);

  const saveMutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = toPayload(values);
      return query.data ? atualizarInstituicaoArquivo(payload) : criarInstituicaoArquivo(payload);
    },
    onSuccess: async () => {
      setMode("view");
      await queryClient.invalidateQueries({ queryKey: ["admin", "instituicao-arquivo"] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: excluirInstituicaoArquivo,
    onSuccess: async () => {
      setMode("view");
      await queryClient.invalidateQueries({ queryKey: ["admin", "instituicao-arquivo"] });
    },
  });
  const showForm = mode === "form" || !query.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Instituição de Arquivo</h1>
          <p className="text-sm text-muted-foreground">
            Cadastro da custodiante padrão dos documentos administrados no Thor.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/admin">
            <ArrowLeft className="h-4 w-4" />
            Administração
          </Link>
        </Button>
      </div>

      <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
        O Thor permite o cadastro de uma única Instituição de Arquivo, que será usada como custodiante padrão do sistema.
      </div>

      {query.isLoading ? (
        <p className="rounded-md border p-4 text-sm text-muted-foreground">Carregando cadastro...</p>
      ) : showForm ? (
        <Card>
          <CardHeader>
            <CardTitle>{query.data ? "Editar cadastro" : "Cadastrar Instituição de Arquivo"}</CardTitle>
            <CardDescription>
              {query.data ? "Atualize os dados da custodiante padrão." : "Nenhuma Instituição de Arquivo cadastrada."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <InstituicaoArquivoForm
              form={form}
              isSaving={saveMutation.isPending}
              error={saveMutation.error?.message}
              onCancel={query.data ? () => setMode("view") : undefined}
              onSubmit={(values) => saveMutation.mutate(values)}
            />
          </CardContent>
        </Card>
      ) : query.data ? (
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <CardTitle>{query.data.nome}</CardTitle>
                <CardDescription>{query.data.sigla || query.data.codigo_referencia || "Custodiante padrão cadastrada"}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={() => setMode("form")}>
                  <Edit className="h-4 w-4" />
                  Editar
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  disabled={deleteMutation.isPending}
                  onClick={() => {
                    if (window.confirm("Remover o cadastro da Instituição de Arquivo?")) {
                      deleteMutation.mutate();
                    }
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                  {deleteMutation.isPending ? "Removendo..." : "Remover"}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <InstituicaoReadOnly instituicao={query.data} />
            {deleteMutation.error ? <p className="mt-4 text-sm text-destructive">{deleteMutation.error.message}</p> : null}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <p className="text-sm text-muted-foreground">Nenhuma Instituição de Arquivo cadastrada.</p>
            <Button type="button" onClick={() => setMode("form")}>
              <Plus className="h-4 w-4" />
              Cadastrar Instituição de Arquivo
            </Button>
          </CardContent>
        </Card>
      )}

      {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
    </div>
  );
}

function InstituicaoArquivoForm({
  form,
  isSaving,
  error,
  onCancel,
  onSubmit,
}: {
  form: ReturnType<typeof useForm<FormValues>>;
  isSaving: boolean;
  error?: string;
  onCancel?: () => void;
  onSubmit: (values: FormValues) => void;
}) {
  return (
    <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
      <FormSection title="Identificação">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Nome" error={form.formState.errors.nome?.message} required>
            <Input {...form.register("nome")} required />
          </Field>
          <Field label="Sigla" error={form.formState.errors.sigla?.message}>
            <Input {...form.register("sigla")} />
          </Field>
          <Field label="CODEARQ" error={form.formState.errors.codigo_referencia?.message}>
            <Input {...form.register("codigo_referencia")} />
          </Field>
          <Field label="Natureza jurídica" error={form.formState.errors.natureza_juridica?.message}>
            <Input {...form.register("natureza_juridica")} />
          </Field>
          <SelectField label="Esfera administrativa" error={form.formState.errors.esfera_administrativa?.message} {...form.register("esfera_administrativa")}>
            <option value="">Selecione</option>
            {esferaOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </SelectField>
          <Field label="CNPJ" error={form.formState.errors.cnpj?.message}>
            <Input {...form.register("cnpj")} placeholder="00.000.000/0000-00" />
          </Field>
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
          <Field label="Logradouro" error={form.formState.errors.endereco_logradouro?.message}><Input {...form.register("endereco_logradouro")} /></Field>
          <Field label="Número" error={form.formState.errors.endereco_numero?.message}><Input {...form.register("endereco_numero")} /></Field>
          <Field label="Complemento" error={form.formState.errors.endereco_complemento?.message}><Input {...form.register("endereco_complemento")} /></Field>
          <Field label="Bairro" error={form.formState.errors.endereco_bairro?.message}><Input {...form.register("endereco_bairro")} /></Field>
          <Field label="Município" error={form.formState.errors.endereco_municipio?.message}><Input {...form.register("endereco_municipio")} /></Field>
          <Field label="UF" error={form.formState.errors.endereco_uf?.message}><Input maxLength={2} {...form.register("endereco_uf")} /></Field>
          <Field label="CEP" error={form.formState.errors.endereco_cep?.message}><Input {...form.register("endereco_cep")} /></Field>
          <Field label="País" error={form.formState.errors.endereco_pais?.message}><Input {...form.register("endereco_pais")} /></Field>
        </div>
      </FormSection>

      <FormSection title="Responsável institucional">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Nome" error={form.formState.errors.responsavel_nome?.message}><Input {...form.register("responsavel_nome")} /></Field>
          <Field label="Cargo" error={form.formState.errors.responsavel_cargo?.message}><Input {...form.register("responsavel_cargo")} /></Field>
          <Field label="E-mail" error={form.formState.errors.responsavel_email?.message}><Input type="email" {...form.register("responsavel_email")} /></Field>
          <Field label="Telefone" error={form.formState.errors.responsavel_telefone?.message}><Input {...form.register("responsavel_telefone")} /></Field>
        </div>
      </FormSection>

      <FormSection title="Informações institucionais">
        <div className="grid gap-4">
          <TextAreaField label="Histórico" error={form.formState.errors.historico?.message} {...form.register("historico")} />
          <TextAreaField label="Missão" error={form.formState.errors.missao?.message} {...form.register("missao")} />
          <TextAreaField label="Observações" error={form.formState.errors.observacoes?.message} {...form.register("observacoes")} />
        </div>
      </FormSection>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <div className="flex gap-2">
        <Button type="submit" disabled={isSaving}>
          <Save className="h-4 w-4" />
          {isSaving ? "Salvando..." : "Salvar"}
        </Button>
        {onCancel ? <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button> : null}
      </div>
    </form>
  );
}

function InstituicaoReadOnly({ instituicao }: { instituicao: InstituicaoArquivo }) {
  const fields: Array<[string, string | null | undefined]> = [
    ["Sigla", instituicao.sigla],
    ["CODEARQ", instituicao.codigo_referencia],
    ["Natureza jurídica", instituicao.natureza_juridica],
    ["Esfera administrativa", instituicao.esfera_administrativa],
    ["CNPJ", instituicao.cnpj],
    ["E-mail", instituicao.email],
    ["Telefone", instituicao.telefone],
    ["Site", instituicao.site],
    ["Logradouro", instituicao.endereco_logradouro],
    ["Número", instituicao.endereco_numero],
    ["Complemento", instituicao.endereco_complemento],
    ["Bairro", instituicao.endereco_bairro],
    ["Município", instituicao.endereco_municipio],
    ["UF", instituicao.endereco_uf],
    ["CEP", instituicao.endereco_cep],
    ["País", instituicao.endereco_pais],
    ["Responsável", instituicao.responsavel_nome],
    ["Cargo", instituicao.responsavel_cargo],
    ["E-mail do responsável", instituicao.responsavel_email],
    ["Telefone do responsável", instituicao.responsavel_telefone],
  ];
  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
            <p className="mt-1 text-sm">{value || "-"}</p>
          </div>
        ))}
      </div>
      <LongText label="Histórico" value={instituicao.historico} />
      <LongText label="Missão" value={instituicao.missao} />
      <LongText label="Observações" value={instituicao.observacoes} />
    </div>
  );
}

function toFormValues(instituicao: InstituicaoArquivo): FormValues {
  return {
    nome: instituicao.nome,
    sigla: instituicao.sigla ?? "",
    codigo_referencia: instituicao.codigo_referencia ?? "",
    natureza_juridica: instituicao.natureza_juridica ?? "",
    esfera_administrativa: instituicao.esfera_administrativa ?? "",
    cnpj: instituicao.cnpj ?? "",
    email: instituicao.email ?? "",
    telefone: instituicao.telefone ?? "",
    site: instituicao.site ?? "",
    endereco_logradouro: instituicao.endereco_logradouro ?? "",
    endereco_numero: instituicao.endereco_numero ?? "",
    endereco_complemento: instituicao.endereco_complemento ?? "",
    endereco_bairro: instituicao.endereco_bairro ?? "",
    endereco_municipio: instituicao.endereco_municipio ?? "",
    endereco_uf: instituicao.endereco_uf ?? "",
    endereco_cep: instituicao.endereco_cep ?? "",
    endereco_pais: instituicao.endereco_pais ?? "Brasil",
    responsavel_nome: instituicao.responsavel_nome ?? "",
    responsavel_cargo: instituicao.responsavel_cargo ?? "",
    responsavel_email: instituicao.responsavel_email ?? "",
    responsavel_telefone: instituicao.responsavel_telefone ?? "",
    historico: instituicao.historico ?? "",
    missao: instituicao.missao ?? "",
    observacoes: instituicao.observacoes ?? "",
  };
}

function toPayload(values: FormValues): InstituicaoArquivoPayload {
  const payload = Object.fromEntries(
    Object.entries(values).map(([key, value]) => [
      key,
      typeof value === "string" ? value.trim() || null : value,
    ]),
  ) as InstituicaoArquivoPayload;
  return {
    ...payload,
    nome: values.nome.trim(),
    esfera_administrativa: values.esfera_administrativa || null,
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
      <Label>{label}{required ? <span className="ml-1 text-destructive">*</span> : null}</Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function SelectField({ label, error, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props}>
        {children}
      </select>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function TextAreaField({ label, error, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <textarea className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props} />
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function LongText({ label, value }: { label: string; value?: string | null }) {
  return value ? (
    <section className="space-y-1">
      <h3 className="text-sm font-semibold">{label}</h3>
      <p className="whitespace-pre-wrap text-sm text-muted-foreground">{value}</p>
    </section>
  ) : null;
}

function isValidCnpj(digits: string) {
  const calculate = (numbers: string) => {
    const weights = numbers.length === 12
      ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
      : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const sum = numbers.split("").reduce((total, digit, index) => total + Number(digit) * weights[index], 0);
    const remainder = sum % 11;
    return remainder < 2 ? "0" : String(11 - remainder);
  };
  return digits[12] === calculate(digits.slice(0, 12)) && digits[13] === calculate(digits.slice(0, 13));
}
