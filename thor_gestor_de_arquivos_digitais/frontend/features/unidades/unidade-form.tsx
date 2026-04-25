"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createUnidade } from "@/lib/api/domain";

const schema = z.object({
  identificador: z.string().min(2).max(255),
  titulo: z.string().min(2).max(500),
  descricao: z.string().max(2000).optional(),
  tipo_suporte: z.enum(["FISICO", "DIGITAL", "HIBRIDO"]),
  tipo_unidade: z.enum(["CAIXA", "PASTA", "VOLUME", "AIP", "SIP", "DIP"]),
  nivel_acesso: z.enum(["PUBLICO", "RESTRITO", "CONFIDENCIAL"]),
  status: z.enum(["ATIVA", "INATIVA", "TRANSFERIDA", "ELIMINADA"]),
});

type FormValues = z.infer<typeof schema>;

export function UnidadeForm({ onCreated }: { onCreated?: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      identificador: "",
      titulo: "",
      descricao: "",
      tipo_suporte: "DIGITAL",
      tipo_unidade: "AIP",
      nivel_acesso: "RESTRITO",
      status: "ATIVA",
    },
  });

  const mutation = useMutation({
    mutationFn: createUnidade,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["unidades"] });
      form.reset();
      onCreated?.();
    },
  });

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Identificador" error={form.formState.errors.identificador?.message}>
          <Input {...form.register("identificador")} placeholder="AIP-2026-0001" />
        </Field>
        <Field label="Título" error={form.formState.errors.titulo?.message}>
          <Input {...form.register("titulo")} placeholder="Conjunto documental" />
        </Field>
      </div>

      <Field label="Descrição" error={form.formState.errors.descricao?.message}>
        <Input {...form.register("descricao")} placeholder="Descrição breve" />
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
      </div>

      {mutation.error ? (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      ) : null}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : "Salvar unidade"}
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

function SelectField({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        {...props}
      >
        {children}
      </select>
    </div>
  );
}
