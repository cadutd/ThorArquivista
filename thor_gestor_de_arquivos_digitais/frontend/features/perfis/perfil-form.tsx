"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createPerfil, listPermissoesPage, updatePerfil } from "@/lib/api/perfis-permissoes";
import type { Perfil } from "@/types/domain";

const schema = z.object({
  codigo: z.string().trim().min(2).max(80),
  nome: z.string().trim().min(3).max(150),
  descricao: z.string().optional(),
  ativo: z.boolean(),
  sistema: z.boolean(),
  permissao_ids: z.array(z.string()),
});

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  codigo: "",
  nome: "",
  descricao: "",
  ativo: true,
  sistema: false,
  permissao_ids: [],
};

export function PerfilForm({ perfil, onSaved }: { perfil?: Perfil; onSaved?: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues });
  const permissoes = useQuery({
    queryKey: ["permissoes", "perfil-form"],
    queryFn: () => listPermissoesPage({ limit: 100, filters: { ativo: "true" } }),
  });
  // eslint-disable-next-line react-hooks/incompatible-library
  const selectedIds = form.watch("permissao_ids");
  const isEditing = Boolean(perfil);

  useEffect(() => {
    form.reset(
      perfil
        ? {
            codigo: perfil.codigo,
            nome: perfil.nome,
            descricao: perfil.descricao ?? "",
            ativo: perfil.ativo,
            sistema: perfil.sistema,
            permissao_ids: perfil.permissoes.map((permissao) => permissao.id),
          }
        : defaultValues,
    );
  }, [form, perfil]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = {
        codigo: values.codigo.trim(),
        nome: values.nome.trim(),
        descricao: values.descricao?.trim() || null,
        ativo: values.ativo,
        sistema: values.sistema,
        permissao_ids: values.permissao_ids,
      };
      return perfil ? updatePerfil(perfil.id, payload) : createPerfil(payload);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["perfis"] }),
        queryClient.invalidateQueries({ queryKey: ["usuarios"] }),
      ]);
      onSaved?.();
    },
  });

  const togglePermission = (id: string) => {
    const next = selectedIds.includes(id) ? selectedIds.filter((value) => value !== id) : [...selectedIds, id];
    form.setValue("permissao_ids", next, { shouldDirty: true, shouldValidate: true });
  };

  return (
    <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Código" error={form.formState.errors.codigo?.message} required>
          <Input {...form.register("codigo")} required />
        </Field>
        <Field label="Nome" error={form.formState.errors.nome?.message} required>
          <Input {...form.register("nome")} required />
        </Field>
        <label className="flex items-center gap-2 pt-8 text-sm font-medium">
          <input type="checkbox" {...form.register("ativo")} />
          Perfil ativo
        </label>
        <label className="flex items-center gap-2 pt-8 text-sm font-medium">
          <input type="checkbox" {...form.register("sistema")} />
          Perfil de sistema
        </label>
      </div>
      <TextAreaField label="Descrição" error={form.formState.errors.descricao?.message} {...form.register("descricao")} />

      <section className="space-y-3 rounded-md border p-4">
        <div>
          <h2 className="text-base font-semibold">Permissões</h2>
          <p className="text-sm text-muted-foreground">{selectedIds.length} permissões selecionadas.</p>
        </div>
        {permissoes.isLoading ? <p className="text-sm text-muted-foreground">Carregando permissões...</p> : null}
        {permissoes.error ? <p className="text-sm text-destructive">{permissoes.error.message}</p> : null}
        <div className="grid gap-2 md:grid-cols-2">
          {(permissoes.data?.items ?? []).map((permissao) => (
            <label key={permissao.id} className="flex items-start gap-2 rounded-md border p-3 text-sm">
              <input type="checkbox" className="mt-1" checked={selectedIds.includes(permissao.id)} onChange={() => togglePermission(permissao.id)} />
              <span>
                <span className="block font-medium">{permissao.nome}</span>
                <span className="block text-xs text-muted-foreground">{permissao.codigo}</span>
              </span>
            </label>
          ))}
        </div>
      </section>

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Salvar perfil"}
      </Button>
    </form>
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

function TextAreaField({ label, error, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <textarea className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props} />
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
