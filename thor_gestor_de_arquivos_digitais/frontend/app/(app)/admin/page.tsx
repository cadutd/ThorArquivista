"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Image as ImageIcon, KeyRound, Save, ServerCog, Settings, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  obterConfiguracaoEnderecamento,
  obterConfiguracaoInstituicao,
  salvarConfiguracaoEnderecamento,
  salvarConfiguracaoInstituicao,
  type ConfiguracaoEnderecamento,
  type ConfiguracaoInstituicao,
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
  const instituicao = useQuery({
    queryKey: ["admin", "configuracoes", "instituicao"],
    queryFn: obterConfiguracaoInstituicao,
  });
  const defaultValues: ConfiguracaoEnderecamento = {
    digitos_codigo_estrutura: {
      corredor: 2,
      modulo: 2,
      estante: 2,
    },
  };
  const [draft, setDraft] = useState<ConfiguracaoEnderecamento | null>(null);
  const [institutionDraft, setInstitutionDraft] = useState<ConfiguracaoInstituicao | null>(null);
  const [logoError, setLogoError] = useState<string | null>(null);
  const values = draft ?? configuracao.data ?? defaultValues;
  const institutionValues = institutionDraft ?? instituicao.data ?? {};
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
  const institutionMutation = useMutation({
    mutationFn: salvarConfiguracaoInstituicao,
    onSuccess: async (data) => {
      setInstitutionDraft(data);
      await queryClient.invalidateQueries({ queryKey: ["admin", "configuracoes", "instituicao"] });
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

  const setInstitutionValue = (field: keyof ConfiguracaoInstituicao, value: string | null) => {
    setInstitutionDraft((current) => ({
      ...(current ?? institutionValues),
      [field]: value,
    }));
  };

  const loadLogo = async (file?: File) => {
    if (!file) {
      return;
    }
    setLogoError(null);
    try {
      const dataUrl = await resizeImageToDataUrl(file, 900, 900);
      setInstitutionValue("logotipo_data_url", dataUrl);
    } catch {
      setLogoError("Não foi possível processar o logotipo selecionado.");
    }
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

      <Card>
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
              <ImageIcon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Instituição</CardTitle>
              <CardDescription>Logotipo e nome usados nas fichas espelho impressas.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-[1fr_220px]">
            <div className="space-y-4">
              <NumberlessField label="Nome da instituição">
                <Input
                  value={institutionValues.nome ?? ""}
                  onChange={(event) => setInstitutionValue("nome", event.target.value)}
                />
              </NumberlessField>
              <NumberlessField label="Logotipo">
                <Input type="file" accept="image/*" onChange={(event) => loadLogo(event.target.files?.[0])} />
              </NumberlessField>
              {logoError ? <p className="text-sm text-destructive">{logoError}</p> : null}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  disabled={instituicao.isLoading || institutionMutation.isPending}
                  onClick={() => institutionMutation.mutate(institutionValues)}
                >
                  <Save className="h-4 w-4" />
                  Salvar instituição
                </Button>
                {institutionValues.logotipo_data_url ? (
                  <Button type="button" variant="outline" onClick={() => setInstitutionValue("logotipo_data_url", null)}>
                    Remover logotipo
                  </Button>
                ) : null}
              </div>
            </div>
            <div className="flex min-h-32 items-center justify-center rounded-md border bg-muted/30 p-3">
              {institutionValues.logotipo_data_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={institutionValues.logotipo_data_url} alt="Logotipo da instituição" className="max-h-28 max-w-full object-contain" />
              ) : (
                <p className="text-center text-sm text-muted-foreground">Sem logotipo cadastrado.</p>
              )}
            </div>
          </div>
          {instituicao.error ? <p className="text-sm text-destructive">{instituicao.error.message}</p> : null}
          {institutionMutation.error ? <p className="text-sm text-destructive">{institutionMutation.error.message}</p> : null}
          {institutionMutation.isSuccess ? <p className="text-sm text-emerald-700">Instituição salva.</p> : null}
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

function NumberlessField({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function resizeImageToDataUrl(file: File, maxWidth: number, maxHeight: number) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Falha ao ler arquivo."));
    reader.onload = () => {
      const image = new Image();
      image.onerror = () => reject(new Error("Falha ao carregar imagem."));
      image.onload = () => {
        const scale = Math.min(1, maxWidth / image.width, maxHeight / image.height);
        const width = Math.max(1, Math.round(image.width * scale));
        const height = Math.max(1, Math.round(image.height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (!context) {
          reject(new Error("Canvas indisponível."));
          return;
        }
        context.drawImage(image, 0, 0, width, height);
        resolve(canvas.toDataURL("image/png"));
      };
      image.src = String(reader.result);
    };
    reader.readAsDataURL(file);
  });
}
