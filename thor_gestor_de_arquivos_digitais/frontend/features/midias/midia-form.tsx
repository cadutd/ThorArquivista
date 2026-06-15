"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StoragePositionPicker } from "@/features/armazenamento/storage-components";
import { createMidia, listTiposMidiaAtivos, updateMidia } from "@/lib/api/domain";
import { atribuirPosicaoMidia } from "@/lib/api/storage-addressing";
import type { MidiaArmazenamento } from "@/types/domain";

const schema = z.object({
  nome: z.string().min(2).max(255),
  tipo_midia_id: z.string().min(1, "Selecione o tipo de midia."),
  descricao: z.string().max(2000).optional(),
  ativo: z.boolean(),
  data_aquisicao: z.string().optional(),
  data_inicio_uso: z.string().optional(),
  data_validade: z.string().optional(),
  capacidade_total_bytes: z.string().optional(),
  capacidade_utilizada_bytes: z.string().optional(),
  identificador_fisico: z.string().max(255).optional(),
  id_posicao_armazenamento: z.number().nullable(),
});

type FormValues = z.infer<typeof schema>;

export function MidiaForm({
  midia,
  onCreated,
}: {
  midia?: MidiaArmazenamento;
  onCreated?: () => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(midia);
  const tiposQuery = useQuery({
    queryKey: ["tipos-midia", "ativos"],
    queryFn: listTiposMidiaAtivos,
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: midia?.nome ?? "",
      tipo_midia_id: midia?.tipo_midia_id ?? "",
      descricao: midia?.descricao ?? "",
      ativo: midia?.ativo ?? true,
      data_aquisicao: midia?.data_aquisicao ?? "",
      data_inicio_uso: midia?.data_inicio_uso ?? "",
      data_validade: midia?.data_validade ?? "",
      capacidade_total_bytes: midia?.capacidade_total_bytes ? String(midia.capacidade_total_bytes) : "",
      capacidade_utilizada_bytes: midia?.capacidade_utilizada_bytes ? String(midia.capacidade_utilizada_bytes) : "",
      identificador_fisico: midia?.identificador_fisico ?? "",
      id_posicao_armazenamento: midia?.id_posicao_armazenamento ?? null,
    },
  });
  // React Hook Form opts this hook out of React Compiler memoization.
  // eslint-disable-next-line react-hooks/incompatible-library
  const posicaoSelecionada = form.watch("id_posicao_armazenamento");

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        nome: values.nome,
        tipo_midia_id: values.tipo_midia_id,
        descricao: values.descricao || null,
        ativo: values.ativo,
        data_aquisicao: values.data_aquisicao || null,
        data_inicio_uso: values.data_inicio_uso || null,
        data_validade: values.data_validade || null,
        capacidade_total_bytes: toNullableNumber(values.capacidade_total_bytes),
        capacidade_utilizada_bytes: toNullableNumber(values.capacidade_utilizada_bytes),
        identificador_fisico: values.identificador_fisico || null,
      };
      const saved = midia ? await updateMidia(midia.id, payload) : await createMidia(payload);

      if (
        values.id_posicao_armazenamento &&
        values.id_posicao_armazenamento !== midia?.id_posicao_armazenamento
      ) {
        await atribuirPosicaoMidia(saved.id, {
          id_posicao: values.id_posicao_armazenamento,
          motivo: "Atribuicao realizada pelo cadastro de midia.",
        });
      }

      return saved;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["midias"] });
      if (!isEditing) {
        form.reset();
      }
      onCreated?.();
    },
  });

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <Field label="Nome" error={form.formState.errors.nome?.message}>
        <Input {...form.register("nome")} placeholder="NAS preservacao 01" />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Tipo</Label>
          <select
            className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            {...form.register("tipo_midia_id")}
          >
            <option value="">Selecione</option>
            {(tiposQuery.data ?? []).map((tipo) => (
              <option key={tipo.id} value={tipo.id}>
                {tipo.nome}
              </option>
            ))}
          </select>
          {form.formState.errors.tipo_midia_id ? (
            <p className="text-xs text-destructive">{form.formState.errors.tipo_midia_id.message}</p>
          ) : null}
        </div>
        <label className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm">
          <input type="checkbox" className="h-4 w-4" {...form.register("ativo")} />
          Midia ativa
        </label>
      </div>
      <Field label="Descricao" error={form.formState.errors.descricao?.message}>
        <Input {...form.register("descricao")} placeholder="Uso, localizacao ou politica" />
      </Field>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Aquisicao" error={form.formState.errors.data_aquisicao?.message}>
          <Input type="date" {...form.register("data_aquisicao")} />
        </Field>
        <Field label="Inicio de uso" error={form.formState.errors.data_inicio_uso?.message}>
          <Input type="date" {...form.register("data_inicio_uso")} />
        </Field>
        <Field label="Validade" error={form.formState.errors.data_validade?.message}>
          <Input type="date" {...form.register("data_validade")} />
        </Field>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Capacidade total (bytes)" error={form.formState.errors.capacidade_total_bytes?.message}>
          <Input type="number" min={0} {...form.register("capacidade_total_bytes")} />
        </Field>
        <Field label="Capacidade utilizada (bytes)" error={form.formState.errors.capacidade_utilizada_bytes?.message}>
          <Input type="number" min={0} {...form.register("capacidade_utilizada_bytes")} />
        </Field>
        <Field label="Identificador fisico" error={form.formState.errors.identificador_fisico?.message}>
          <Input {...form.register("identificador_fisico")} placeholder="Etiqueta, serial ou barcode" />
        </Field>
      </div>
      <StoragePositionPicker
        value={posicaoSelecionada}
        onChange={(value) => form.setValue("id_posicao_armazenamento", value)}
      />

      {tiposQuery.error ? <p className="text-sm text-destructive">{tiposQuery.error.message}</p> : null}
      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

      <Button type="submit" disabled={mutation.isPending || tiposQuery.isLoading}>
        {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alteracoes" : "Salvar midia"}
      </Button>
    </form>
  );
}

function toNullableNumber(value?: string) {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
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
