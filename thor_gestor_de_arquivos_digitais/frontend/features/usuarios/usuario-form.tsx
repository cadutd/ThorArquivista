"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { listPerfisPage } from "@/lib/api/perfis-permissoes";
import { createIdentityAccount, createUsuario, updateUsuario, type IdentityAccount } from "@/lib/api/usuarios";
import type { PapelUsuario, Usuario } from "@/types/domain";

const papelValues = ["ADMIN", "ARQUIVISTA", "ADMISSAO", "GESTOR_ARMAZENAMENTO", "CONSULTA"] as const;

const schema = z.object({
  keycloak_sub: z.string().max(255).optional(),
  username: z.string().trim().min(3, "Informe ao menos 3 caracteres.").max(150),
  nome: z.string().trim().min(1, "Informe o nome.").max(255),
  email: z.string().trim().email("Informe um e-mail válido.").max(255),
  papel: z.enum(papelValues),
  id_perfil: z.string().optional(),
  ativo: z.boolean(),
  observacoes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  keycloak_sub: "",
  username: "",
  nome: "",
  email: "",
  papel: "ARQUIVISTA",
  id_perfil: "",
  ativo: true,
  observacoes: "",
};

export const papelUsuarioOptions: Array<{ value: PapelUsuario; label: string }> = [
  { value: "ADMIN", label: "Administrador" },
  { value: "ARQUIVISTA", label: "Arquivista" },
  { value: "ADMISSAO", label: "Admissão" },
  { value: "GESTOR_ARMAZENAMENTO", label: "Gestor de Armazenamento" },
  { value: "CONSULTA", label: "Consulta" },
];

export function UsuarioForm({ usuario, onSaved }: { usuario?: Usuario; onSaved?: () => void }) {
  const queryClient = useQueryClient();
  const isEditing = Boolean(usuario);
  const [savedUsuario, setSavedUsuario] = useState<Usuario | undefined>(usuario);
  const [identityAccount, setIdentityAccount] = useState<IdentityAccount | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });
  const perfis = useQuery({
    queryKey: ["perfis", "usuarios-form"],
    queryFn: () => listPerfisPage({ limit: 100, filters: { ativo: "true" } }),
  });

  useEffect(() => {
    if (!usuario) {
      form.reset(defaultValues);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSavedUsuario(undefined);
      setIdentityAccount(null);
      return;
    }
    setSavedUsuario(usuario);
    setIdentityAccount(null);
    form.reset({
      keycloak_sub: usuario.keycloak_sub ?? "",
      username: usuario.username,
      nome: usuario.nome,
      email: usuario.email,
      papel: usuario.papel,
      id_perfil: usuario.id_perfil ?? "",
      ativo: usuario.ativo,
      observacoes: usuario.observacoes ?? "",
    });
  }, [form, usuario]);

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        keycloak_sub: values.keycloak_sub?.trim() || null,
        username: values.username.trim(),
        nome: values.nome.trim(),
        email: values.email.trim(),
        papel: values.papel,
        id_perfil: values.id_perfil || null,
        ativo: values.ativo,
        observacoes: values.observacoes?.trim() || null,
      };
      return usuario ? updateUsuario(usuario.id, payload) : createUsuario(payload);
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      setSavedUsuario(data);
      if (isEditing) {
        onSaved?.();
      }
    },
  });
  const identityMutation = useMutation({
    mutationFn: (targetUsuario: Usuario) => createIdentityAccount(targetUsuario.id, "KEYCLOAK"),
    onSuccess: async (data) => {
      setIdentityAccount(data);
      const refreshed = {
        ...(savedUsuario as Usuario),
        keycloak_sub: data.provider_user_id,
      };
      setSavedUsuario(refreshed);
      await queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
  const canCreateIdentity = Boolean(savedUsuario && !savedUsuario.keycloak_sub);

  return (
    <div className="space-y-6">
      <form className="space-y-6" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nome" error={form.formState.errors.nome?.message} required>
            <Input {...form.register("nome")} required />
          </Field>
          <Field label="Usuário" error={form.formState.errors.username?.message} required>
            <Input {...form.register("username")} required />
          </Field>
          <Field label="E-mail" error={form.formState.errors.email?.message} required>
            <Input type="email" {...form.register("email")} required />
          </Field>
          <SelectField
            label="Perfil"
            error={form.formState.errors.id_perfil?.message}
            {...form.register("id_perfil", {
              onChange: (event) => {
                const perfil = perfis.data?.items.find((item) => item.id === event.target.value);
                if (perfil && (papelValues as readonly string[]).includes(perfil.codigo)) {
                  form.setValue("papel", perfil.codigo as PapelUsuario);
                }
              },
            })}
          >
            <option value="">Selecione um perfil</option>
            {(perfis.data?.items ?? []).map((perfil) => (
              <option key={perfil.id} value={perfil.id}>
                {perfil.nome}
              </option>
            ))}
          </SelectField>
          <input type="hidden" {...form.register("papel")} />
          <Field label="Sub Keycloak" error={form.formState.errors.keycloak_sub?.message}>
            <Input {...form.register("keycloak_sub")} />
          </Field>
          <label className="flex items-center gap-2 pt-8 text-sm font-medium">
            <input type="checkbox" {...form.register("ativo")} />
            Usuário ativo
          </label>
        </div>

        <TextAreaField label="Observações" error={form.formState.errors.observacoes?.message} {...form.register("observacoes")} />

        {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
        {mutation.isSuccess && !isEditing ? <p className="text-sm text-emerald-700">Usuário cadastrado. Agora você pode criar a conta no provedor de identidade.</p> : null}

        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Salvar usuário"}
        </Button>
      </form>

      {savedUsuario ? (
        <section className="space-y-3 rounded-md border p-4">
          <div>
            <h2 className="text-base font-semibold">Provedor de identidade</h2>
            <p className="text-sm text-muted-foreground">Crie a conta externa depois de salvar o perfil local.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={!canCreateIdentity || identityMutation.isPending}
              onClick={() => savedUsuario && identityMutation.mutate(savedUsuario)}
            >
              <KeyRound className="h-4 w-4" />
              {identityMutation.isPending ? "Criando..." : "Criar no Keycloak"}
            </Button>
            {savedUsuario.keycloak_sub ? (
              <span className="text-sm text-muted-foreground">Vinculado: {savedUsuario.keycloak_sub}</span>
            ) : null}
          </div>
          {identityMutation.error ? <p className="text-sm text-destructive">{identityMutation.error.message}</p> : null}
          {identityAccount ? (
            <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
              <p className="font-medium">Conta criada no Keycloak.</p>
              <p>Usuário: {identityAccount.username}</p>
              <p>Senha temporária: <code className="rounded bg-white px-1">{identityAccount.temporary_password}</code></p>
              <p>O Keycloak exigirá troca de senha no primeiro acesso.</p>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
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
