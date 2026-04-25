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
  atribuirPosicaoCopia,
  atribuirPosicaoUnidade,
} from "@/lib/api/storage-addressing";
import { StoragePositionPicker } from "@/features/armazenamento/storage-components";
import {
  createCopiaDigital,
  createMidia,
  createUnidade,
  listMidias,
  updateUnidade,
} from "@/lib/api/domain";
import type { UnidadeAcondicionamento } from "@/types/domain";

const schema = z
  .object({
    identificador: z.string().min(2).max(255),
    titulo: z.string().min(2).max(500),
    descricao: z.string().max(2000).optional(),
    tipo_suporte: z.enum(["FISICO", "DIGITAL", "HIBRIDO"]),
    tipo_unidade: z.enum(["CAIXA", "PASTA", "VOLUME", "AIP", "SIP", "DIP"]),
    nivel_acesso: z.enum(["PUBLICO", "RESTRITO", "CONFIDENCIAL"]),
    status: z.enum(["ATIVA", "INATIVA", "TRANSFERIDA", "ELIMINADA"]),
    id_unidade_pai: z.string().optional(),
    id_representa: z.string().optional(),
    id_posicao_armazenamento: z.number().nullable(),
    associar_midia: z.boolean(),
    modo_midia: z.enum(["existente", "nova"]),
    id_midia_armazenamento: z.string().optional(),
    nova_midia_nome: z.string().max(255).optional(),
    nova_midia_tipo: z.enum(["FILESYSTEM", "NAS", "NFS", "LTO", "S3", "CLOUD"]),
    nova_midia_descricao: z.string().max(2000).optional(),
    uri_copia: z.string().max(1200).optional(),
    funcao_copia: z.enum(["PRESERVACAO", "BACKUP", "ACESSO", "QUARENTENA"]),
    status_copia: z.enum(["ATIVA", "INDISPONIVEL", "CORROMPIDA", "EM_VERIFICACAO"]),
    algoritmo_fixidez: z.string().max(32).optional(),
    hash_fixidez: z.string().max(128).optional(),
    ultima_verificacao_em: z.string().optional(),
    id_posicao_copia: z.number().nullable(),
  })
  .superRefine((values, ctx) => {
    if (values.tipo_suporte !== "DIGITAL" || !values.associar_midia) {
      return;
    }

    if (!values.uri_copia?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["uri_copia"],
        message: "Informe a URI da cópia digital.",
      });
    }

    if (values.modo_midia === "existente" && !values.id_midia_armazenamento) {
      ctx.addIssue({
        code: "custom",
        path: ["id_midia_armazenamento"],
        message: "Selecione uma mídia.",
      });
    }

    if (values.modo_midia === "nova" && !values.nova_midia_nome?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["nova_midia_nome"],
        message: "Informe o nome da nova mídia.",
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  identificador: "",
  titulo: "",
  descricao: "",
  tipo_suporte: "DIGITAL",
  tipo_unidade: "AIP",
  nivel_acesso: "RESTRITO",
  status: "ATIVA",
  id_unidade_pai: "",
  id_representa: "",
  id_posicao_armazenamento: null,
  associar_midia: false,
  modo_midia: "existente",
  id_midia_armazenamento: "",
  nova_midia_nome: "",
  nova_midia_tipo: "FILESYSTEM",
  nova_midia_descricao: "",
  uri_copia: "",
  funcao_copia: "PRESERVACAO",
  status_copia: "ATIVA",
  algoritmo_fixidez: "",
  hash_fixidez: "",
  ultima_verificacao_em: "",
  id_posicao_copia: null,
};

export function UnidadeForm({
  unidade,
  onSaved,
}: {
  unidade?: UnidadeAcondicionamento;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const midias = useQuery({ queryKey: ["midias"], queryFn: () => listMidias() });
  const isEditing = Boolean(unidade);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });
  // React Hook Form opts this hook out of React Compiler memoization.
  // eslint-disable-next-line react-hooks/incompatible-library
  const tipoSuporte = form.watch("tipo_suporte");
  const associarMidia = form.watch("associar_midia");
  const modoMidia = form.watch("modo_midia");

  useEffect(() => {
    if (!unidade) {
      form.reset(defaultValues);
      return;
    }

    form.reset({
      ...defaultValues,
      identificador: unidade.identificador,
      titulo: unidade.titulo,
      descricao: unidade.descricao ?? "",
      tipo_suporte: unidade.tipo_suporte,
      tipo_unidade: unidade.tipo_unidade,
      nivel_acesso: unidade.nivel_acesso,
      status: unidade.status,
      id_unidade_pai: unidade.id_unidade_pai ? String(unidade.id_unidade_pai) : "",
      id_representa: unidade.id_representa ? String(unidade.id_representa) : "",
      id_posicao_armazenamento: unidade.id_posicao_armazenamento ?? null,
    });
  }, [form, unidade]);

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        identificador: values.identificador,
        titulo: values.titulo,
        descricao: values.descricao || null,
        tipo_suporte: values.tipo_suporte,
        tipo_unidade: values.tipo_unidade,
        nivel_acesso: values.nivel_acesso,
        status: values.status,
        id_unidade_pai: toOptionalNumber(values.id_unidade_pai),
        id_representa: toOptionalNumber(values.id_representa),
      };

      if (unidade) {
        const updated = await updateUnidade(unidade.id, payload);
        if (
          values.id_posicao_armazenamento &&
          values.id_posicao_armazenamento !== unidade.id_posicao_armazenamento
        ) {
          await atribuirPosicaoUnidade(unidade.id, {
            id_posicao: values.id_posicao_armazenamento,
            motivo: "Atribuição realizada pela edição da unidade.",
          });
        }
        return updated;
      }

      const created = await createUnidade(payload);

      if (values.id_posicao_armazenamento) {
        await atribuirPosicaoUnidade(created.id, {
          id_posicao: values.id_posicao_armazenamento,
          motivo: "Atribuição realizada pelo cadastro da unidade.",
        });
      }

      if (values.tipo_suporte === "DIGITAL" && values.associar_midia) {
        const midia =
          values.modo_midia === "nova"
            ? await createMidia({
                nome: values.nova_midia_nome?.trim() ?? "",
                tipo: values.nova_midia_tipo,
                descricao: values.nova_midia_descricao || null,
                ativo: true,
              })
            : null;

        const copia = await createCopiaDigital(created.id, {
          id_midia_armazenamento:
            midia?.id ?? toOptionalNumber(values.id_midia_armazenamento) ?? 0,
          uri_copia: values.uri_copia?.trim() ?? "",
          funcao_copia: values.funcao_copia,
          status_copia: values.status_copia,
          algoritmo_fixidez: values.algoritmo_fixidez || null,
          hash_fixidez: values.hash_fixidez || null,
          ultima_verificacao_em: values.ultima_verificacao_em || null,
        });

        if (values.id_posicao_copia) {
          await atribuirPosicaoCopia(copia.id, {
            id_posicao: values.id_posicao_copia,
            motivo: "Atribuição realizada pelo cadastro da cópia digital.",
          });
        }
      }

      return created;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["unidades"] }),
        queryClient.invalidateQueries({ queryKey: ["midias"] }),
      ]);
      if (!isEditing) {
        form.reset(defaultValues);
      }
      onSaved?.();
    },
  });

  return (
    <form
      className="space-y-5"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Identificador" error={form.formState.errors.identificador?.message}>
          <Input {...form.register("identificador")} placeholder="AIP-2026-0001" />
        </Field>
        <Field label="Título" error={form.formState.errors.titulo?.message}>
          <Input {...form.register("titulo")} placeholder="Conjunto documental" />
        </Field>
      </div>

      <Field label="Descrição" error={form.formState.errors.descricao?.message}>
        <textarea
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("descricao")}
          placeholder="Descrição breve"
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField label="Suporte" {...form.register("tipo_suporte")}>
          <option value="FISICO">Físico</option>
          <option value="DIGITAL">Digital</option>
          <option value="HIBRIDO">Híbrido</option>
        </SelectField>
        <SelectField label="Tipo" {...form.register("tipo_unidade")}>
          <option value="CAIXA">Caixa</option>
          <option value="PASTA">Pasta</option>
          <option value="VOLUME">Volume</option>
          <option value="AIP">AIP</option>
          <option value="SIP">SIP</option>
          <option value="DIP">DIP</option>
        </SelectField>
        <SelectField label="Acesso" {...form.register("nivel_acesso")}>
          <option value="PUBLICO">Público</option>
          <option value="RESTRITO">Restrito</option>
          <option value="CONFIDENCIAL">Confidencial</option>
        </SelectField>
        <SelectField label="Status" {...form.register("status")}>
          <option value="ATIVA">Ativa</option>
          <option value="INATIVA">Inativa</option>
          <option value="TRANSFERIDA">Transferida</option>
          <option value="ELIMINADA">Eliminada</option>
        </SelectField>
        <Field label="Unidade pai" error={form.formState.errors.id_unidade_pai?.message}>
          <Input type="number" min={1} {...form.register("id_unidade_pai")} />
        </Field>
        <Field label="Representa" error={form.formState.errors.id_representa?.message}>
          <Input type="number" min={1} {...form.register("id_representa")} />
        </Field>
      </div>

      <StoragePositionPicker
        value={form.watch("id_posicao_armazenamento")}
        onChange={(value) => form.setValue("id_posicao_armazenamento", value)}
        label="Posição de armazenamento da unidade"
      />

      {!isEditing && tipoSuporte === "DIGITAL" ? (
        <section className="space-y-4 rounded-md border p-4">
          <label className="flex items-center gap-2 text-sm font-medium">
            <input type="checkbox" {...form.register("associar_midia")} />
            Associar mídia de armazenamento
          </label>

          {associarMidia ? (
            <>
              <SelectField label="Mídia" {...form.register("modo_midia")}>
                <option value="existente">Usar mídia existente</option>
                <option value="nova">Criar nova mídia</option>
              </SelectField>

              {modoMidia === "existente" ? (
                <SelectField
                  label="Mídia existente"
                  error={form.formState.errors.id_midia_armazenamento?.message}
                  {...form.register("id_midia_armazenamento")}
                >
                  <option value="">Selecione</option>
                  {(midias.data ?? []).map((midia) => (
                    <option key={midia.id} value={midia.id}>
                      {midia.nome} ({midia.tipo})
                    </option>
                  ))}
                </SelectField>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Nome da mídia"
                    error={form.formState.errors.nova_midia_nome?.message}
                  >
                    <Input {...form.register("nova_midia_nome")} />
                  </Field>
                  <SelectField label="Tipo da mídia" {...form.register("nova_midia_tipo")}>
                    <option value="FILESYSTEM">Filesystem</option>
                    <option value="NAS">NAS</option>
                    <option value="NFS">NFS</option>
                    <option value="LTO">LTO</option>
                    <option value="S3">S3</option>
                    <option value="CLOUD">Cloud</option>
                  </SelectField>
                  <Field label="Descrição da mídia">
                    <Input {...form.register("nova_midia_descricao")} />
                  </Field>
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="URI da cópia" error={form.formState.errors.uri_copia?.message}>
                  <Input {...form.register("uri_copia")} placeholder="s3://bucket/aip" />
                </Field>
                <SelectField label="Função da cópia" {...form.register("funcao_copia")}>
                  <option value="PRESERVACAO">Preservação</option>
                  <option value="BACKUP">Backup</option>
                  <option value="ACESSO">Acesso</option>
                  <option value="QUARENTENA">Quarentena</option>
                </SelectField>
                <SelectField label="Status da cópia" {...form.register("status_copia")}>
                  <option value="ATIVA">Ativa</option>
                  <option value="INDISPONIVEL">Indisponível</option>
                  <option value="CORROMPIDA">Corrompida</option>
                  <option value="EM_VERIFICACAO">Em verificação</option>
                </SelectField>
                <Field label="Última verificação">
                  <Input type="datetime-local" {...form.register("ultima_verificacao_em")} />
                </Field>
                <Field label="Algoritmo de fixidez">
                  <Input {...form.register("algoritmo_fixidez")} placeholder="SHA-256" />
                </Field>
                <Field label="Hash de fixidez">
                  <Input {...form.register("hash_fixidez")} />
                </Field>
              </div>
              <StoragePositionPicker
                value={form.watch("id_posicao_copia")}
                onChange={(value) => form.setValue("id_posicao_copia", value)}
                label="Posição de armazenamento da cópia digital"
              />
            </>
          ) : null}
        </section>
      ) : null}

      {mutation.error ? (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      ) : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending
          ? "Salvando..."
          : isEditing
            ? "Salvar alterações"
            : "Salvar unidade"}
      </Button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function toOptionalNumber(value?: string) {
  return value ? Number(value) : null;
}

function SelectField({
  label,
  error,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  error?: string;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        {...props}
      >
        {children}
      </select>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
