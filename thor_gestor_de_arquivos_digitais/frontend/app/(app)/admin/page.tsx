"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Save, ServerCog, Settings, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  obterConfiguracaoEnderecamento,
  salvarConfiguracaoEnderecamento,
  type ConfiguracaoEnderecamento,
} from "@/lib/api/admin";
import { config } from "@/lib/config";

const adminItems = [
  {
    title: "Keycloak",
    description: "Realm, clientes, papéis e políticas de autenticação.",
    icon: KeyRound,
    value: "thor",
  },
  {
    title: "Usuários",
    description: "Gestão delegada ao provedor de identidade.",
    icon: Users,
    value: "OIDC",
  },
  {
    title: "API",
    description: "Endpoint FastAPI usado pelo frontend.",
    icon: ServerCog,
    value: config.apiBaseUrl,
  },
  {
    title: "Configurações",
    description: "Preferências operacionais e parâmetros futuros.",
    icon: Settings,
    value: "MVP",
  },
];

export default function AdminPage() {
  const queryClient = useQueryClient();
  const configuracao = useQuery({
    queryKey: ["admin", "configuracoes", "enderecamento"],
    queryFn: obterConfiguracaoEnderecamento,
  });
  const defaultValues: ConfiguracaoEnderecamento = {
    digitos_codigo_estrutura: {
      corredor: 2,
      modulo: 2,
      estante: 2,
    },
  };
  const [draft, setDraft] = useState<ConfiguracaoEnderecamento | null>(null);
  const values = draft ?? configuracao.data ?? defaultValues;
  const preview = useMemo(() => {
    const { corredor, modulo, estante } = values.digitos_codigo_estrutura;
    return `C${"1".padStart(corredor, "0")}-M${"1".padStart(modulo, "0")}-E${"1".padStart(estante, "0")}`;
  }, [values]);
  const mutation = useMutation({
    mutationFn: salvarConfiguracaoEnderecamento,
    onSuccess: async (data) => {
      setDraft(data);
      await queryClient.invalidateQueries({ queryKey: ["admin", "configuracoes", "enderecamento"] });
    },
  });

  const setDigitos = (field: keyof ConfiguracaoEnderecamento["digitos_codigo_estrutura"], value: number) => {
    setDraft((current) => ({
      ...(current ?? values),
      digitos_codigo_estrutura: {
        ...(current ?? values).digitos_codigo_estrutura,
        [field]: Math.max(1, Math.min(6, value || 1)),
      },
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Administração</h1>
        <p className="text-sm text-muted-foreground">
          Configurações de autenticação, integração e governança.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        {adminItems.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title}>
              <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>{item.description}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <code className="block rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                  {item.value}
                </code>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <Card>
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Endereçamento</CardTitle>
              <CardDescription>
                Parâmetros usados na geração automática de topografia.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <NumberParameter
              label="Dígitos do corredor"
              value={values.digitos_codigo_estrutura.corredor}
              onChange={(value) => setDigitos("corredor", value)}
            />
            <NumberParameter
              label="Dígitos do módulo"
              value={values.digitos_codigo_estrutura.modulo}
              onChange={(value) => setDigitos("modulo", value)}
            />
            <NumberParameter
              label="Dígitos da estante"
              value={values.digitos_codigo_estrutura.estante}
              onChange={(value) => setDigitos("estante", value)}
            />
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-muted-foreground">Exemplo de código de estrutura</p>
            <code className="mt-1 block font-semibold text-foreground">{preview}</code>
          </div>
          {configuracao.error ? <p className="text-sm text-destructive">{configuracao.error.message}</p> : null}
          {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
          {mutation.isSuccess ? <p className="text-sm text-emerald-700">Configuração salva.</p> : null}
          <Button
            disabled={configuracao.isLoading || mutation.isPending}
            onClick={() => mutation.mutate(values)}
          >
            <Save className="h-4 w-4" />
            Salvar parametrização
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function NumberParameter({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input
        type="number"
        min={1}
        max={6}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}
