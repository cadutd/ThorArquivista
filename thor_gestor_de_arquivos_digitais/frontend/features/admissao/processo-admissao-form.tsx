"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { obterInstituicaoArquivo } from "@/lib/api/admin";
import { createProcessoAdmissao, updateProcessoAdmissao, type ProcessoAdmissao } from "@/lib/api/admissao";
import { listarRegistrosDescricao } from "@/lib/api/descricao-arquivistica";
import { listEntidadesProdutoras } from "@/lib/api/entidades-produtoras";

const schema = z.object({
  numero_processo: z.string().trim().min(1, "Informe o número.").max(100),
  titulo: z.string().trim().min(1, "Informe o título.").max(255),
  descricao: z.string().optional(),
  id_instituicao_arquivo: z.string().min(1, "Cadastre ou selecione a Instituição de Arquivo."),
  id_entidade_produtora: z.string().min(1, "Selecione a entidade produtora."),
  id_descricao_arquivistica: z.string().optional(),
  nome_usuario_responsavel: z.string().optional(),
  tipo_processo_admissao: z.enum(["FECHADO", "CONTINUO"]),
  tipo_ingresso: z.enum(["TRANSFERENCIA", "RECOLHIMENTO", "DOACAO", "AQUISICAO", "INCORPORACAO", "REGULARIZACAO_LEGADO", "OUTRO"]),
  tipo_suporte: z.enum(["DIGITAL", "FISICO", "HIBRIDO"]),
  data_inicio: z.string().min(1, "Informe a data de início."),
  data_fim_prevista: z.string().optional(),
  data_encerramento: z.string().optional(),
  processo_ativo: z.boolean(),
  admissoes_recorrentes: z.boolean(),
  status: z.enum(["ABERTO", "EM_NEGOCIACAO", "EM_RECEBIMENTO", "EM_QUARENTENA", "EM_VALIDACAO", "PENDENTE_COMPLEMENTACAO", "EM_GERACAO_AIP", "CONCLUIDO", "CANCELADO", "REJEITADO"]),
  resultado_final: z.enum(["ADMITIDO", "ADMITIDO_COM_RESSALVA", "REJEITADO", "CANCELADO"]).or(z.literal("")),
  codigo_classificacao: z.string().optional(),
  codigo_classificacao_descricao: z.string().optional(),
  restricao_acesso: z.string().optional(),
  hipotese_legal_restricao: z.string().optional(),
  volume_estimado: z.string().optional(),
  volume_recebido: z.string().optional(),
  quantidade_unidades_estimadas: z.string().optional(),
  quantidade_unidades_recebidas: z.string().optional(),
  observacoes: z.string().optional(),
  parecer_final: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaultValues: FormValues = {
  numero_processo: "",
  titulo: "",
  descricao: "",
  id_instituicao_arquivo: "",
  id_entidade_produtora: "",
  id_descricao_arquivistica: "",
  nome_usuario_responsavel: "",
  tipo_processo_admissao: "FECHADO",
  tipo_ingresso: "TRANSFERENCIA",
  tipo_suporte: "DIGITAL",
  data_inicio: new Date().toISOString().slice(0, 10),
  data_fim_prevista: "",
  data_encerramento: "",
  processo_ativo: true,
  admissoes_recorrentes: false,
  status: "ABERTO",
  resultado_final: "",
  codigo_classificacao: "",
  codigo_classificacao_descricao: "",
  restricao_acesso: "",
  hipotese_legal_restricao: "",
  volume_estimado: "",
  volume_recebido: "",
  quantidade_unidades_estimadas: "",
  quantidade_unidades_recebidas: "",
  observacoes: "",
  parecer_final: "",
};

export function ProcessoAdmissaoForm({ processo, onSaved }: { processo?: ProcessoAdmissao; onSaved?: (processo: ProcessoAdmissao) => void }) {
  const queryClient = useQueryClient();
  const [descricaoDialogOpen, setDescricaoDialogOpen] = useState(false);
  const [descricaoSearch, setDescricaoSearch] = useState("");
  const [descricaoTitle, setDescricaoTitle] = useState<string | null>(null);
  const instituicao = useQuery({ queryKey: ["admin", "instituicao-arquivo"], queryFn: obterInstituicaoArquivo });
  const produtoras = useQuery({ queryKey: ["entidades-produtoras", "lookup"], queryFn: listEntidadesProdutoras });
  const descricoes = useQuery({
    queryKey: ["descricao-arquivistica", "consulta", descricaoSearch],
    queryFn: () => listarRegistrosDescricao({ q: descricaoSearch }),
    enabled: descricaoDialogOpen,
  });
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues });

  useEffect(() => {
    if (processo) {
      form.reset(toFormValues(processo));
    } else {
      form.reset({ ...defaultValues, id_instituicao_arquivo: instituicao.data?.id ?? "" });
    }
  }, [form, instituicao.data, processo]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = toPayload(values);
      return processo ? updateProcessoAdmissao(processo.id, payload) : createProcessoAdmissao(payload);
    },
    onSuccess: async (saved) => {
      await queryClient.invalidateQueries({ queryKey: ["admissao"] });
      onSaved?.(saved);
    },
  });
  const descricaoDisplayTitle = descricaoTitle ?? processo?.titulo_descricao_arquivistica ?? "";
  const produtorasOptions =
    processo && processo.nome_entidade_produtora && !(produtoras.data ?? []).some((entidade) => entidade.id === processo.id_entidade_produtora)
      ? [{ id: processo.id_entidade_produtora, nome: processo.nome_entidade_produtora }, ...(produtoras.data ?? [])]
      : (produtoras.data ?? []);

  return (
    <form className="space-y-6" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <section className="space-y-3">
        <h2 className="text-base font-semibold">Identificação</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Número do processo" error={form.formState.errors.numero_processo?.message} required><Input {...form.register("numero_processo")} /></Field>
          <Field label="Título" error={form.formState.errors.titulo?.message} required><Input {...form.register("titulo")} /></Field>
          <SelectField label="Instituição de Arquivo" error={form.formState.errors.id_instituicao_arquivo?.message} {...form.register("id_instituicao_arquivo")} required>
            <option value="">Selecione</option>
            {instituicao.data ? <option value={instituicao.data.id}>{instituicao.data.nome}</option> : null}
          </SelectField>
          <SelectField label="Entidade produtora" error={form.formState.errors.id_entidade_produtora?.message} {...form.register("id_entidade_produtora")} required>
            <option value="">Selecione</option>
            {produtorasOptions.map((entidade) => <option key={entidade.id} value={entidade.id}>{entidade.nome}</option>)}
          </SelectField>
          <Field label="Descrição Arquivística Associada">
            <input type="hidden" {...form.register("id_descricao_arquivistica")} />
            <div className="flex gap-2">
              <Input value={descricaoDisplayTitle} readOnly placeholder="Sem vínculo" />
              <Button type="button" variant="outline" onClick={() => setDescricaoDialogOpen(true)}><Search className="h-4 w-4" />Consultar</Button>
              {descricaoDisplayTitle ? <Button type="button" variant="outline" onClick={() => { form.setValue("id_descricao_arquivistica", ""); setDescricaoTitle(""); }}>Limpar</Button> : null}
            </div>
          </Field>
          <Field label="Nome do usuário responsável"><Input {...form.register("nome_usuario_responsavel")} /></Field>
          <SelectField label="Tipo do processo" {...form.register("tipo_processo_admissao")}><option value="FECHADO">FECHADO</option><option value="CONTINUO">CONTINUO</option></SelectField>
          <SelectField label="Tipo de ingresso" {...form.register("tipo_ingresso")}>{["TRANSFERENCIA","RECOLHIMENTO","DOACAO","AQUISICAO","INCORPORACAO","REGULARIZACAO_LEGADO","OUTRO"].map((value) => <option key={value} value={value}>{label(value)}</option>)}</SelectField>
          <SelectField label="Suporte" {...form.register("tipo_suporte")}><option value="DIGITAL">DIGITAL</option><option value="FISICO">FISICO</option><option value="HIBRIDO">HIBRIDO</option></SelectField>
          <SelectField label="Status" {...form.register("status")}>{["ABERTO","EM_NEGOCIACAO","EM_RECEBIMENTO","EM_QUARENTENA","EM_VALIDACAO","PENDENTE_COMPLEMENTACAO","EM_GERACAO_AIP","CONCLUIDO","CANCELADO","REJEITADO"].map((value) => <option key={value} value={value}>{label(value)}</option>)}</SelectField>
        </div>
        <TextAreaField label="Descrição" {...form.register("descricao")} />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Controle</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Data de início" error={form.formState.errors.data_inicio?.message} required><Input type="date" {...form.register("data_inicio")} /></Field>
          <Field label="Fim previsto"><Input type="date" {...form.register("data_fim_prevista")} /></Field>
          <Field label="Encerramento"><Input type="date" {...form.register("data_encerramento")} /></Field>
          <Field label="Volume estimado"><Input {...form.register("volume_estimado")} /></Field>
          <Field label="Volume recebido"><Input {...form.register("volume_recebido")} /></Field>
          <Field label="Quantidade de unidades estimadas"><Input type="number" min={0} {...form.register("quantidade_unidades_estimadas")} /></Field>
          <Field label="Quantidade de unidades recebidas"><Input type="number" min={0} {...form.register("quantidade_unidades_recebidas")} /></Field>
          <SelectField label="Resultado final" {...form.register("resultado_final")}><option value="">Sem resultado</option><option value="ADMITIDO">ADMITIDO</option><option value="ADMITIDO_COM_RESSALVA">ADMITIDO COM RESSALVA</option><option value="REJEITADO">REJEITADO</option><option value="CANCELADO">CANCELADO</option></SelectField>
          <label className="flex items-center gap-2 pt-8 text-sm font-medium"><input type="checkbox" {...form.register("processo_ativo")} />Processo ativo</label>
          <label className="flex items-center gap-2 pt-8 text-sm font-medium"><input type="checkbox" {...form.register("admissoes_recorrentes")} />Admissões recorrentes</label>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Classificação e acesso</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Código de classificação"><Input {...form.register("codigo_classificacao")} /></Field>
          <Field label="Descrição da classificação"><Input {...form.register("codigo_classificacao_descricao")} /></Field>
          <Field label="Restrição de acesso"><Input {...form.register("restricao_acesso")} /></Field>
          <Field label="Hipótese legal"><Input {...form.register("hipotese_legal_restricao")} /></Field>
        </div>
        <TextAreaField label="Observações" {...form.register("observacoes")} />
        <TextAreaField label="Parecer final" {...form.register("parecer_final")} />
      </section>

      {processo ? (
        <section className="space-y-3">
          <h2 className="text-base font-semibold">Auditoria</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="criado_em"><Input value={formatDateTime(processo.criado_em)} disabled readOnly /></Field>
            <Field label="atualizado_em"><Input value={formatDateTime(processo.atualizado_em)} disabled readOnly /></Field>
            <Field label="criado_por"><Input value={processo.criado_por ?? ""} disabled readOnly /></Field>
            <Field label="atualizado_por"><Input value={processo.atualizado_por ?? ""} disabled readOnly /></Field>
          </div>
        </section>
      ) : null}

      {mutation.error ? <p className="text-sm text-destructive">{mutation.error.message}</p> : null}
      <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Salvando..." : "Salvar processo"}</Button>
      <Dialog open={descricaoDialogOpen} onOpenChange={setDescricaoDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Consultar descrição arquivística</DialogTitle>
            <DialogDescription>Selecione uma descrição existente para vincular ao processo.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="Buscar por código ou título"
                value={descricaoSearch}
                onChange={(event) => setDescricaoSearch(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    descricoes.refetch();
                  }
                }}
              />
              <Button type="button" variant="outline" onClick={() => descricoes.refetch()}><Search className="h-4 w-4" />Buscar</Button>
            </div>
            <div className="max-h-96 overflow-auto rounded-md border">
              {(descricoes.data ?? []).map((descricao) => (
                <button
                  key={descricao.id}
                  type="button"
                  className="flex w-full flex-col gap-1 border-b px-3 py-2 text-left text-sm last:border-b-0 hover:bg-muted"
                  onClick={() => {
                    form.setValue("id_descricao_arquivistica", descricao.id, { shouldDirty: true });
                    setDescricaoTitle(descricao.titulo);
                    setDescricaoDialogOpen(false);
                  }}
                >
                  <span className="font-medium">{descricao.titulo}</span>
                  <span className="text-xs text-muted-foreground">{descricao.codigo_referencia}</span>
                </button>
              ))}
              {!descricoes.data?.length ? <p className="p-4 text-sm text-muted-foreground">{descricoes.isLoading ? "Carregando..." : "Nenhuma descrição encontrada."}</p> : null}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </form>
  );
}

function toFormValues(processo: ProcessoAdmissao): FormValues {
  return {
    ...defaultValues,
    numero_processo: processo.numero_processo,
    titulo: processo.titulo,
    descricao: processo.descricao ?? "",
    id_instituicao_arquivo: processo.id_instituicao_arquivo,
    id_entidade_produtora: processo.id_entidade_produtora,
    id_descricao_arquivistica: processo.id_descricao_arquivistica ?? "",
    nome_usuario_responsavel: processo.nome_usuario_responsavel ?? "",
    tipo_processo_admissao: processo.tipo_processo_admissao,
    tipo_ingresso: processo.tipo_ingresso,
    tipo_suporte: processo.tipo_suporte,
    processo_ativo: processo.processo_ativo,
    admissoes_recorrentes: processo.admissoes_recorrentes,
    status: processo.status,
    data_inicio: processo.data_inicio?.slice(0, 10) ?? "",
    data_fim_prevista: processo.data_fim_prevista?.slice(0, 10) ?? "",
    data_encerramento: processo.data_encerramento?.slice(0, 10) ?? "",
    resultado_final: processo.resultado_final ?? "",
    codigo_classificacao: processo.codigo_classificacao ?? "",
    codigo_classificacao_descricao: processo.codigo_classificacao_descricao ?? "",
    restricao_acesso: processo.restricao_acesso ?? "",
    hipotese_legal_restricao: processo.hipotese_legal_restricao ?? "",
    volume_estimado: processo.volume_estimado ?? "",
    volume_recebido: processo.volume_recebido ?? "",
    quantidade_unidades_estimadas: processo.quantidade_unidades_estimadas?.toString() ?? "",
    quantidade_unidades_recebidas: processo.quantidade_unidades_recebidas?.toString() ?? "",
    observacoes: processo.observacoes ?? "",
    parecer_final: processo.parecer_final ?? "",
  };
}

function toPayload(values: FormValues) {
  const nullable = (value?: string) => value?.trim() || null;
  const numberOrNull = (value?: string) => value ? Number(value) : null;
  return {
    ...values,
    descricao: nullable(values.descricao),
    id_descricao_arquivistica: values.id_descricao_arquivistica || null,
    nome_usuario_responsavel: nullable(values.nome_usuario_responsavel),
    data_fim_prevista: values.data_fim_prevista || null,
    data_encerramento: values.data_encerramento || null,
    resultado_final: values.resultado_final || null,
    codigo_classificacao: nullable(values.codigo_classificacao),
    codigo_classificacao_descricao: nullable(values.codigo_classificacao_descricao),
    restricao_acesso: nullable(values.restricao_acesso),
    hipotese_legal_restricao: nullable(values.hipotese_legal_restricao),
    volume_estimado: nullable(values.volume_estimado),
    volume_recebido: nullable(values.volume_recebido),
    quantidade_unidades_estimadas: numberOrNull(values.quantidade_unidades_estimadas),
    quantidade_unidades_recebidas: numberOrNull(values.quantidade_unidades_recebidas),
    observacoes: nullable(values.observacoes),
    parecer_final: nullable(values.parecer_final),
  };
}

function label(value: string) { return value.replaceAll("_", " "); }
function formatDateTime(value?: string | null) { return value ? new Date(value).toLocaleString("pt-BR") : ""; }

function Field({ label, error, children, required }: { label: string; error?: string; children: React.ReactNode; required?: boolean }) {
  return <div className="space-y-2"><Label>{label}{required ? <span className="ml-1 text-destructive">*</span> : null}</Label>{children}{error ? <p className="text-xs text-destructive">{error}</p> : null}</div>;
}

function SelectField({ label, error, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string }) {
  return <div className="space-y-2"><Label>{label}</Label><select className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props}>{children}</select>{error ? <p className="text-xs text-destructive">{error}</p> : null}</div>;
}

function TextAreaField({ label, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string }) {
  return <div className="space-y-2"><Label>{label}</Label><textarea className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" {...props} /></div>;
}
