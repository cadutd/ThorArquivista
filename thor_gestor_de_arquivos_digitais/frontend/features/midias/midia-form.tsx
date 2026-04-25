"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createMidia } from "@/lib/api/domain";
import { atribuirPosicaoMidia } from "@/lib/api/storage-addressing";
import { StoragePositionPicker } from "@/features/armazenamento/storage-components";
import type { MidiaArmazenamento } from "@/types/domain";

const schema = z.object({
  nome: z.string().min(2).max(255),
  tipo: z.enum(["FILESYSTEM", "NAS", "NFS", "LTO", "S3", "CLOUD"]),
  descricao: z.string().max(2000).optional(),
  ativo: z.boolean(),
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
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: "",
      tipo: "FILESYSTEM",
      descricao: "",
      ativo: true,
      id_posicao_armazenamento: midia?.id_posicao_armazenamento ?? null,
    },
  });
  // React Hook Form opts this hook out of React Compiler memoization.
  // eslint-disable-next-line react-hooks/incompatible-library
  const posicaoSelecionada = form.watch("id_posicao_armazenamento");

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const created = await createMidia({
        nome: values.nome,
        tipo: values.tipo,
        descricao: values.descricao || null,
        ativo: values.ativo,
      });

      if (values.id_posicao_armazenamento) {
        await atribuirPosicaoMidia(created.id, {
          id_posicao: values.id_posicao_armazenamento,
          motivo: "Atribuição realizada pelo cadastro de mídia.",
        });
      }

      return created;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["midias"] });
      form.reset();
      onCreated?.();
    },
  });

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <Field label="Nome" error={form.formState.errors.nome?.message}>
        <Input {...form.register("nome")} placeholder="NAS preservação 01" />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Tipo</Label>
          <select
            className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            {...form.register("tipo")}
          >
            <option value="FILESYSTEM">Filesystem</option>
            <option value="NAS">NAS</option>
            <option value="NFS">NFS</option>
            <option value="LTO">LTO</option>
            <option value="S3">S3</option>
            <option value="CLOUD">Cloud</option>
          </select>
        </div>
        <label className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm">
          <input type="checkbox" className="h-4 w-4" {...form.register("ativo")} />
          Mídia ativa
        </label>
      </div>
      <Field label="Descrição" error={form.formState.errors.descricao?.message}>
        <Input {...form.register("descricao")} placeholder="Uso, localização ou política" />
      </Field>
      <StoragePositionPicker
        value={posicaoSelecionada}
        onChange={(value) => form.setValue("id_posicao_armazenamento", value)}
      />

      {mutation.error ? (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      ) : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : "Salvar mídia"}
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
