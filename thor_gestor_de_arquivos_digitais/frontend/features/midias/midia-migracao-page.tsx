"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRightLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  anexarRelatorioMigracaoMidia,
  concluirMigracaoMidia,
  getMidia,
  iniciarMigracaoMidia,
  listTiposMidiaAtivos,
  registrarEtapaMigracaoMidia,
} from "@/lib/api/domain";

const schema = z.object({
  nome: z.string().min(2).max(255),
  tipo_midia_id: z.string().min(1, "Selecione o tipo de midia destino."),
  descricao: z.string().max(2000).optional(),
  data_aquisicao: z.string().optional(),
  data_inicio_uso: z.string().optional(),
  data_validade: z.string().optional(),
  capacidade_total_bytes: z.string().optional(),
  capacidade_utilizada_bytes: z.string().optional(),
  identificador_fisico: z.string().max(255).optional(),
  motivo_migracao: z.string().min(3),
  procedimento_utilizado: z.string().min(3),
  software_utilizado: z.string().optional(),
  versao_software: z.string().optional(),
  observacoes: z.string().optional(),
  etapa_descricao: z.string().optional(),
  etapa_resultado: z.string().optional(),
  relatorio_tipo: z.string().optional(),
  relatorio_referencia: z.string().optional(),
  relatorio_descricao: z.string().optional(),
  concluir_agora: z.boolean(),
  relatorio_integridade_origem: z.string().optional(),
  relatorio_integridade_destino: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function MidiaMigracaoPage({ midiaId }: { midiaId: number }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const midiaQuery = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const tiposQuery = useQuery({
    queryKey: ["tipos-midia", "ativos"],
    queryFn: listTiposMidiaAtivos,
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: "",
      tipo_midia_id: "",
      descricao: "",
      data_aquisicao: "",
      data_inicio_uso: "",
      data_validade: "",
      capacidade_total_bytes: "",
      capacidade_utilizada_bytes: "",
      identificador_fisico: "",
      motivo_migracao: "",
      procedimento_utilizado: "",
      software_utilizado: "",
      versao_software: "",
      observacoes: "",
      etapa_descricao: "",
      etapa_resultado: "",
      relatorio_tipo: "",
      relatorio_referencia: "",
      relatorio_descricao: "",
      concluir_agora: false,
      relatorio_integridade_origem: "",
      relatorio_integridade_destino: "",
    },
  });
  // React Hook Form opts this hook out of React Compiler memoization.
  // eslint-disable-next-line react-hooks/incompatible-library
  const concluirAgora = form.watch("concluir_agora");

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const migracao = await iniciarMigracaoMidia(midiaId, {
        nova_midia: {
          nome: values.nome,
          tipo_midia_id: values.tipo_midia_id,
          descricao: values.descricao || null,
          ativo: true,
          status: "EM_MIGRACAO",
          data_aquisicao: values.data_aquisicao || null,
          data_inicio_uso: values.data_inicio_uso || null,
          data_validade: values.data_validade || null,
          capacidade_total_bytes: toNullableNumber(values.capacidade_total_bytes),
          capacidade_utilizada_bytes: toNullableNumber(values.capacidade_utilizada_bytes),
          identificador_fisico: values.identificador_fisico || null,
        },
        motivo_migracao: values.motivo_migracao,
        procedimento_utilizado: values.procedimento_utilizado,
        software_utilizado: values.software_utilizado || null,
        versao_software: values.versao_software || null,
        observacoes: values.observacoes || null,
      });

      if (values.etapa_descricao) {
        await registrarEtapaMigracaoMidia(migracao.id, {
          descricao: values.etapa_descricao,
          resultado: values.etapa_resultado || null,
        });
      }

      if (values.relatorio_tipo && values.relatorio_referencia) {
        await anexarRelatorioMigracaoMidia(migracao.id, {
          tipo: values.relatorio_tipo,
          referencia: values.relatorio_referencia,
          descricao: values.relatorio_descricao || null,
        });
      }

      if (values.concluir_agora) {
        return concluirMigracaoMidia(migracao.id, {
          resultado: "CONCLUIDA",
          observacoes: values.observacoes || null,
          relatorio_integridade_origem: values.relatorio_integridade_origem || null,
          relatorio_integridade_destino: values.relatorio_integridade_destino || null,
        });
      }

      return migracao;
    },
    onSuccess: async (migracao) => {
      await queryClient.invalidateQueries({ queryKey: ["midias"] });
      await queryClient.invalidateQueries({ queryKey: ["migracoes-midias"] });
      router.push(`/midias/${migracao.midia_destino_id}`);
    },
  });

  const midia = midiaQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Migrar midia</h1>
          <p className="text-sm text-muted-foreground">Crie a midia destino e registre o inicio da migracao.</p>
        </div>
        <Button asChild variant="outline">
          <Link href={`/midias/${midiaId}`}>
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{midia?.nome ?? "Midia de origem"}</CardTitle>
          <CardDescription>
            {midiaQuery.isLoading
              ? "Carregando midia de origem."
              : midia
                ? `Origem ${midia.id} - ${midia.tipo_midia?.nome ?? "tipo nao informado"}`
                : "Midia de origem nao encontrada."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {midiaQuery.error ? <p className="text-sm text-destructive">{midiaQuery.error.message}</p> : null}
          {midia ? (
            <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <section className="space-y-4">
                <h2 className="text-base font-semibold">Midia destino</h2>
                <Field label="Nome" error={form.formState.errors.nome?.message}>
                  <Input {...form.register("nome")} placeholder={`Destino de ${midia.nome}`} />
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
                  <Field label="Identificador fisico" error={form.formState.errors.identificador_fisico?.message}>
                    <Input {...form.register("identificador_fisico")} placeholder="Etiqueta, serial ou barcode" />
                  </Field>
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
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Capacidade total (bytes)" error={form.formState.errors.capacidade_total_bytes?.message}>
                    <Input type="number" min={0} {...form.register("capacidade_total_bytes")} />
                  </Field>
                  <Field label="Capacidade utilizada (bytes)" error={form.formState.errors.capacidade_utilizada_bytes?.message}>
                    <Input type="number" min={0} {...form.register("capacidade_utilizada_bytes")} />
                  </Field>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-base font-semibold">Procedimento</h2>
                <Field label="Motivo da migracao" error={form.formState.errors.motivo_migracao?.message}>
                  <Input {...form.register("motivo_migracao")} placeholder="Validade, falha, substituicao ou ampliacao" />
                </Field>
                <Field label="Procedimento utilizado" error={form.formState.errors.procedimento_utilizado?.message}>
                  <Input {...form.register("procedimento_utilizado")} placeholder="Metodo, etapas planejadas e criterio de validacao" />
                </Field>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Software utilizado" error={form.formState.errors.software_utilizado?.message}>
                    <Input {...form.register("software_utilizado")} />
                  </Field>
                  <Field label="Versao do software" error={form.formState.errors.versao_software?.message}>
                    <Input {...form.register("versao_software")} />
                  </Field>
                </div>
                <Field label="Observacoes" error={form.formState.errors.observacoes?.message}>
                  <Input {...form.register("observacoes")} />
                </Field>
              </section>

              <section className="space-y-4">
                <h2 className="text-base font-semibold">Etapa e relatorio</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Etapa realizada" error={form.formState.errors.etapa_descricao?.message}>
                    <Input {...form.register("etapa_descricao")} placeholder="Copia, conferencia, validacao ou outra etapa" />
                  </Field>
                  <Field label="Resultado da etapa" error={form.formState.errors.etapa_resultado?.message}>
                    <Input {...form.register("etapa_resultado")} placeholder="Sucesso, alerta ou falha observada" />
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                  <Field label="Tipo de relatorio" error={form.formState.errors.relatorio_tipo?.message}>
                    <Input {...form.register("relatorio_tipo")} placeholder="Fixidez, copia, conferencia" />
                  </Field>
                  <Field label="Referencia do relatorio" error={form.formState.errors.relatorio_referencia?.message}>
                    <Input {...form.register("relatorio_referencia")} placeholder="URI, caminho ou identificador" />
                  </Field>
                  <Field label="Descricao do relatorio" error={form.formState.errors.relatorio_descricao?.message}>
                    <Input {...form.register("relatorio_descricao")} />
                  </Field>
                </div>
              </section>

              <section className="space-y-4">
                <label className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm">
                  <input type="checkbox" className="h-4 w-4" {...form.register("concluir_agora")} />
                  Concluir migracao apos registrar a validacao de integridade
                </label>
                {concluirAgora ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Field label="Integridade da origem" error={form.formState.errors.relatorio_integridade_origem?.message}>
                      <Input {...form.register("relatorio_integridade_origem")} placeholder="Resumo ou referencia da validacao" />
                    </Field>
                    <Field label="Integridade do destino" error={form.formState.errors.relatorio_integridade_destino?.message}>
                      <Input {...form.register("relatorio_integridade_destino")} placeholder="Resumo ou referencia da validacao" />
                    </Field>
                  </div>
                ) : null}
              </section>

              {tiposQuery.error ? <p className="text-sm text-destructive">{tiposQuery.error.message}</p> : null}
              {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}

              <Button type="submit" disabled={mutation.isPending || tiposQuery.isLoading}>
                <ArrowRightLeft className="h-4 w-4" />
                {mutation.isPending ? "Processando..." : concluirAgora ? "Executar e concluir migracao" : "Iniciar migracao"}
              </Button>
            </form>
          ) : null}
        </CardContent>
      </Card>
    </div>
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
