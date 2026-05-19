"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Edit, Eye, Plus, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  createAcordoAdmissao,
  createEventoAdmissao,
  createReuniaoAdmissao,
  createSessaoSubmissao,
  createSipAdmissao,
  deleteReuniaoAdmissao,
  getProcessoAdmissao,
  listAcordosAdmissao,
  listEventosAdmissao,
  listReunioesAdmissao,
  listSessoesSubmissao,
  listSipsProcesso,
  novaVersaoAcordoAdmissao,
  rejeitarSipAdmissao,
  type AcordoAdmissao,
  type ReuniaoAdmissao,
  type SessaoSubmissao,
  type StatusAcordoAdmissao,
  type TipoReuniaoAdmissao,
  updateAcordoAdmissao,
  updateReuniaoAdmissao,
  validarSipAdmissao,
} from "@/lib/api/admissao";

const TIPOS_REUNIAO: TipoReuniaoAdmissao[] = [
  "NEGOCIACAO_INICIAL",
  "ALINHAMENTO_TECNICO",
  "VALIDACAO_SIP",
  "REVISAO_ACORDO",
  "TRATAMENTO_DIVERGENCIA",
  "HOMOLOGACAO",
  "ENCERRAMENTO",
  "OUTRO",
];

const STATUS_ACORDO: StatusAcordoAdmissao[] = [
  "RASCUNHO",
  "EM_ANALISE",
  "ATIVO",
  "SUSPENSO",
  "ENCERRADO",
];

const CANAIS_SUBMISSAO = ["UPLOAD", "API", "REDE_INTERNA", "MIDIA_REMOVIVEL", "ENTREGA_FISICA", "IMPORTACAO_SISTEMA", "OUTRO"] as const;

type ReuniaoFormData = {
  titulo: string;
  tipo_reuniao: TipoReuniaoAdmissao;
  data_reuniao: string;
  participantes: string;
  descricao: string;
  deliberacoes: string;
  pendencias: string;
  proximos_passos: string;
};

type AcordoFormData = {
  titulo: string;
  descricao: string;
  status: StatusAcordoAdmissao;
  data_inicio_vigencia: string;
  data_fim_vigencia: string;
  motivo_revisao: string;
  regras_empacotamento: string;
  regras_nomenclatura: string;
  formatos_aceitos: string;
  metadados_obrigatorios: string;
  requisitos_fixidez: string;
  requisitos_representacao: string;
  politica_validacao: string;
  politica_rejeicao: string;
  politica_normalizacao: string;
  politica_sigilo: string;
  periodicidade_submissao: string;
  observacoes: string;
  documento_acordo: string;
};

type SessaoFormData = {
  titulo: string;
  data_inicio: string;
  canal_submissao: (typeof CANAIS_SUBMISSAO)[number];
  tipo_suporte: SessaoSubmissao["tipo_suporte"];
  responsavel_envio: string;
  responsavel_recebimento: string;
  volume_informado: string;
  caminho_origem: string;
  observacoes: string;
};

export function ProcessoAdmissaoDetailPage({ id }: { id: string }) {
  const processo = useQuery({ queryKey: ["admissao", "processos", id], queryFn: () => getProcessoAdmissao(id) });
  if (processo.isLoading) return <p className="rounded-md border p-4 text-sm text-muted-foreground">Carregando processo...</p>;
  if (processo.error) return <p className="rounded-md border p-4 text-sm text-destructive">{processo.error.message}</p>;
  if (!processo.data) return null;
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">{processo.data.titulo}</h1>
          <p className="text-sm text-muted-foreground">{processo.data.numero_processo}</p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline"><Link href="/admissao"><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
          <Button asChild><Link href={`/admissao/${id}/editar`}><Edit className="h-4 w-4" />Editar</Link></Button>
        </div>
      </div>

      <Tabs defaultValue="resumo">
        <TabsList className="flex h-auto flex-wrap justify-start">
          {["resumo","reunioes","acordos","sessoes","sips","aips","eventos","documentos"].map((tab) => <TabsTrigger key={tab} value={tab}>{tabLabel(tab)}</TabsTrigger>)}
        </TabsList>
        <TabsContent value="resumo"><Resumo processo={processo.data} /></TabsContent>
        <TabsContent value="reunioes"><Reunioes processoId={id} /></TabsContent>
        <TabsContent value="acordos"><Acordos processoId={id} /></TabsContent>
        <TabsContent value="sessoes"><Sessoes processoId={id} /></TabsContent>
        <TabsContent value="sips"><Sips processoId={id} /></TabsContent>
        <TabsContent value="aips"><p className="rounded-md border p-4 text-sm text-muted-foreground">AIPs são vinculados pela ação transformar em AIP do SIP usando Unidade de Acondicionamento. A tabela de relação já está preparada no backend.</p></TabsContent>
        <TabsContent value="eventos"><Eventos processoId={id} /></TabsContent>
        <TabsContent value="documentos"><p className="rounded-md border p-4 text-sm text-muted-foreground">Documentos administrativos usam campos de referência textual nesta fase. A tela fica reservada para integração com anexos/documentos quando essa entidade for consolidada.</p></TabsContent>
      </Tabs>
    </div>
  );
}

function Resumo({ processo }: { processo: Awaited<ReturnType<typeof getProcessoAdmissao>> }) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", processo.id],
    ["Número do processo", processo.numero_processo],
    ["Título", processo.titulo],
    ["ID da instituição de arquivo", processo.id_instituicao_arquivo],
    ["Instituição", processo.nome_instituicao_arquivo],
    ["ID da entidade produtora", processo.id_entidade_produtora],
    ["Entidade produtora", processo.nome_entidade_produtora],
    ["Descrição Arquivística Associada", processo.titulo_descricao_arquivistica],
    ["ID da descrição arquivística associada", processo.id_descricao_arquivistica],
    ["Nome do usuário responsável", processo.nome_usuario_responsavel],
    ["Status", label(processo.status)],
    ["Tipo do processo", label(processo.tipo_processo_admissao)],
    ["Tipo de ingresso", label(processo.tipo_ingresso)],
    ["Tipo de suporte", label(processo.tipo_suporte)],
    ["Data de início", processo.data_inicio],
    ["Data fim prevista", processo.data_fim_prevista],
    ["Data de encerramento", processo.data_encerramento],
    ["Processo ativo", processo.processo_ativo ? "Sim" : "Não"],
    ["Admissões recorrentes", processo.admissoes_recorrentes ? "Sim" : "Não"],
    ["Resultado final", label(processo.resultado_final)],
    ["Código de classificação", processo.codigo_classificacao],
    ["Descrição da classificação", processo.codigo_classificacao_descricao],
    ["Restrição de acesso", processo.restricao_acesso],
    ["Hipótese legal de restrição", processo.hipotese_legal_restricao],
    ["Volume estimado", processo.volume_estimado],
    ["Volume recebido", processo.volume_recebido],
    ["Quantidade de unidades estimadas", processo.quantidade_unidades_estimadas],
    ["Quantidade de unidades recebidas", processo.quantidade_unidades_recebidas],
    ["Criado por", processo.criado_por],
    ["Atualizado por", processo.atualizado_por],
    ["Criado em", formatDate(processo.criado_em)],
    ["Atualizado em", formatDate(processo.atualizado_em)],
  ];
  return <div className="space-y-4"><div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">{fields.map(([name, value]) => <Detail key={name} label={name} value={value} />)}</div><LongText label="Descrição" value={processo.descricao} /><LongText label="Observações" value={processo.observacoes} /><LongText label="Parecer final" value={processo.parecer_final} /></div>;
}

function Reunioes({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admissao", "reunioes", processoId], queryFn: () => listReunioesAdmissao(processoId) });
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ReuniaoAdmissao | null>(null);
  const [viewing, setViewing] = useState<ReuniaoAdmissao | null>(null);
  const [data, setData] = useState<ReuniaoFormData>(defaultReuniaoFormData());
  const create = useMutation({ mutationFn: (payload: Partial<ReuniaoAdmissao>) => createReuniaoAdmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const update = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Partial<ReuniaoAdmissao> }) => updateReuniaoAdmissao(id, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const remove = useMutation({ mutationFn: deleteReuniaoAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const mutationError = create.error?.message || update.error?.message || remove.error?.message;

  const closeForm = () => {
    setOpen(false);
    setEditing(null);
    setData(defaultReuniaoFormData());
  };

  const startCreate = () => {
    setViewing(null);
    setEditing(null);
    setData(defaultReuniaoFormData());
    setOpen(true);
  };

  const startEdit = (reuniao: ReuniaoAdmissao) => {
    setViewing(null);
    setEditing(reuniao);
    setData({
      titulo: reuniao.titulo,
      tipo_reuniao: reuniao.tipo_reuniao,
      data_reuniao: toDateInput(reuniao.data_reuniao),
      participantes: reuniao.participantes ?? "",
      descricao: reuniao.descricao ?? "",
      deliberacoes: reuniao.deliberacoes ?? "",
      pendencias: reuniao.pendencias ?? "",
      proximos_passos: reuniao.proximos_passos ?? "",
    });
    setOpen(true);
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const payload = reuniaoPayload(data);
    if (editing) {
      update.mutate({ id: editing.id, payload }, { onSuccess: closeForm });
    } else {
      create.mutate(payload, { onSuccess: closeForm });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Button type="button" onClick={startCreate}><Plus className="h-4 w-4" />Nova reunião</Button></div>
      {viewing ? <ReuniaoDetails reuniao={viewing} onClose={() => setViewing(null)} onEdit={() => startEdit(viewing)} /> : null}
      {open ? (
        <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Título"><Input required value={data.titulo} onChange={(event) => setData({ ...data, titulo: event.target.value })} /></Field>
          <Field label="Tipo de reunião">
            <select required className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.tipo_reuniao} onChange={(event) => setData({ ...data, tipo_reuniao: event.target.value as TipoReuniaoAdmissao })}>
              {TIPOS_REUNIAO.map((value) => <option key={value} value={value}>{label(value)}</option>)}
            </select>
          </Field>
          <Field label="Data"><Input required type="datetime-local" value={data.data_reuniao} onChange={(event) => setData({ ...data, data_reuniao: event.target.value })} /></Field>
          <Field label="Participantes"><Input value={data.participantes} onChange={(event) => setData({ ...data, participantes: event.target.value })} /></Field>
          <div className="md:col-span-2"><Field label="Descrição"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.descricao} onChange={(event) => setData({ ...data, descricao: event.target.value })} /></Field></div>
          <div className="md:col-span-2"><Field label="Deliberações"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.deliberacoes} onChange={(event) => setData({ ...data, deliberacoes: event.target.value })} /></Field></div>
          <div className="md:col-span-2"><Field label="Pendências"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.pendencias} onChange={(event) => setData({ ...data, pendencias: event.target.value })} /></Field></div>
          <div className="md:col-span-2"><Field label="Próximos passos"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.proximos_passos} onChange={(event) => setData({ ...data, proximos_passos: event.target.value })} /></Field></div>
          <div className="flex items-end gap-2"><Button type="submit" disabled={create.isPending || update.isPending}>{create.isPending || update.isPending ? "Salvando..." : "Salvar"}</Button><Button type="button" variant="outline" onClick={closeForm}>Cancelar</Button></div>
          {mutationError ? <p className="text-sm text-destructive md:col-span-2">{mutationError}</p> : null}
        </form>
      ) : null}
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader><TableRow><TableHead>Nº</TableHead><TableHead>Título</TableHead><TableHead>Tipo</TableHead><TableHead>Data</TableHead><TableHead>Participantes</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader>
          <TableBody>
            {(query.data ?? []).map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.numero_reuniao}</TableCell>
                <TableCell>{item.titulo}</TableCell>
                <TableCell>{label(item.tipo_reuniao)}</TableCell>
                <TableCell>{formatDate(item.data_reuniao)}</TableCell>
                <TableCell>{item.participantes || "-"}</TableCell>
                <TableCell><div className="flex justify-end gap-1"><Button type="button" variant="ghost" size="icon" aria-label="Visualizar reunião" onClick={() => { setOpen(false); setEditing(null); setViewing(item); }}><Eye className="h-4 w-4" /></Button><Button type="button" variant="ghost" size="icon" aria-label="Editar reunião" onClick={() => startEdit(item)}><Edit className="h-4 w-4" /></Button><Button type="button" variant="ghost" size="icon" aria-label="Excluir reunião" disabled={remove.isPending} onClick={() => window.confirm("Excluir esta reunião?") && remove.mutate(item.id)}><Trash2 className="h-4 w-4" /></Button></div></TableCell>
              </TableRow>
            ))}
            {!query.data?.length ? <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{query.isLoading ? "Carregando..." : "Nenhuma reunião registrada."}</TableCell></TableRow> : null}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function Acordos({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admissao", "acordos", processoId], queryFn: () => listAcordosAdmissao(processoId) });
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<AcordoAdmissao | null>(null);
  const [viewing, setViewing] = useState<AcordoAdmissao | null>(null);
  const [data, setData] = useState<AcordoFormData>(defaultAcordoFormData());
  const create = useMutation({ mutationFn: (payload: Partial<AcordoAdmissao>) => createAcordoAdmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const update = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Partial<AcordoAdmissao> }) => updateAcordoAdmissao(id, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const version = useMutation({
    mutationFn: novaVersaoAcordoAdmissao,
    onSuccess: (acordo) => {
      setViewing(null);
      startEdit(acordo);
      return invalidate(queryClient, processoId);
    },
  });
  const mutationError = create.error?.message || update.error?.message || version.error?.message;

  const latestVersion = Math.max(0, ...(query.data ?? []).map((item) => item.numero_versao));
  const activeAgreement = (query.data ?? []).find((item) => item.status === "ATIVO");

  const closeForm = () => {
    setOpen(false);
    setEditing(null);
    setData(defaultAcordoFormData());
  };

  const startCreate = () => {
    setViewing(null);
    setEditing(null);
    setData(activeAgreement ? acordoToFormData(activeAgreement) : defaultAcordoFormData());
    setOpen(true);
  };

  function startEdit(acordo: AcordoAdmissao) {
    setViewing(null);
    setEditing(acordo);
    setData(acordoToFormData(acordo));
    setOpen(true);
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const payload = acordoPayload(data);
    if (editing) {
      update.mutate({ id: editing.id, payload }, { onSuccess: closeForm });
    } else {
      create.mutate(payload, { onSuccess: closeForm });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Button type="button" onClick={startCreate}><Plus className="h-4 w-4" />Novo acordo de admissão</Button></div>
      {viewing ? (
        <AcordoDetails
          acordo={viewing}
          isLatest={viewing.numero_versao === latestVersion}
          isVersioning={version.isPending}
          onClose={() => setViewing(null)}
          onEdit={() => startEdit(viewing)}
          onNewVersion={() => version.mutate(activeAgreement?.id ?? viewing.id)}
        />
      ) : null}
      {open ? (
        <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Título"><Input required value={data.titulo} onChange={(event) => setData({ ...data, titulo: event.target.value })} /></Field>
          <Field label="Status">
            <select required className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.status} onChange={(event) => setData({ ...data, status: event.target.value as StatusAcordoAdmissao })}>
              {STATUS_ACORDO.map((value) => <option key={value} value={value}>{label(value)}</option>)}
            </select>
          </Field>
          <Field label="Data início vigência"><Input type="date" value={data.data_inicio_vigencia} onChange={(event) => setData({ ...data, data_inicio_vigencia: event.target.value })} /></Field>
          <Field label="Data fim vigência"><Input type="date" value={data.data_fim_vigencia} onChange={(event) => setData({ ...data, data_fim_vigencia: event.target.value })} /></Field>
          <Field label="Periodicidade submissão"><Input value={data.periodicidade_submissao} onChange={(event) => setData({ ...data, periodicidade_submissao: event.target.value })} /></Field>
          <Field label="Documento do acordo"><Input value={data.documento_acordo} onChange={(event) => setData({ ...data, documento_acordo: event.target.value })} /></Field>
          <AcordoTextarea label="Descrição" value={data.descricao} onChange={(value) => setData({ ...data, descricao: value })} />
          <AcordoTextarea label="Motivo revisão" value={data.motivo_revisao} onChange={(value) => setData({ ...data, motivo_revisao: value })} />
          <AcordoTextarea label="Regras empacotamento" value={data.regras_empacotamento} onChange={(value) => setData({ ...data, regras_empacotamento: value })} />
          <AcordoTextarea label="Regras nomenclatura" value={data.regras_nomenclatura} onChange={(value) => setData({ ...data, regras_nomenclatura: value })} />
          <AcordoTextarea label="Formatos aceitos" value={data.formatos_aceitos} onChange={(value) => setData({ ...data, formatos_aceitos: value })} />
          <AcordoTextarea label="Metadados obrigatórios" value={data.metadados_obrigatorios} onChange={(value) => setData({ ...data, metadados_obrigatorios: value })} />
          <AcordoTextarea label="Requisitos fixidez" value={data.requisitos_fixidez} onChange={(value) => setData({ ...data, requisitos_fixidez: value })} />
          <AcordoTextarea label="Requisitos representação" value={data.requisitos_representacao} onChange={(value) => setData({ ...data, requisitos_representacao: value })} />
          <AcordoTextarea label="Política validação" value={data.politica_validacao} onChange={(value) => setData({ ...data, politica_validacao: value })} />
          <AcordoTextarea label="Política rejeição" value={data.politica_rejeicao} onChange={(value) => setData({ ...data, politica_rejeicao: value })} />
          <AcordoTextarea label="Política normalização" value={data.politica_normalizacao} onChange={(value) => setData({ ...data, politica_normalizacao: value })} />
          <AcordoTextarea label="Política sigilo" value={data.politica_sigilo} onChange={(value) => setData({ ...data, politica_sigilo: value })} />
          <AcordoTextarea label="Observações" value={data.observacoes} onChange={(value) => setData({ ...data, observacoes: value })} />
          {editing ? (
            <>
              <Field label="Criado por"><Input value={editing.criado_por ?? ""} disabled /></Field>
              <Field label="Atualizado por"><Input value={editing.atualizado_por ?? ""} disabled /></Field>
              <Field label="Criado em"><Input value={formatDate(editing.criado_em)} disabled /></Field>
              <Field label="Atualizado em"><Input value={formatDate(editing.atualizado_em)} disabled /></Field>
            </>
          ) : null}
          <div className="flex items-end gap-2 md:col-span-2"><Button type="submit" disabled={create.isPending || update.isPending}>{create.isPending || update.isPending ? "Salvando..." : "Salvar"}</Button><Button type="button" variant="outline" onClick={closeForm}>Cancelar</Button></div>
          {mutationError ? <p className="text-sm text-destructive md:col-span-2">{mutationError}</p> : null}
        </form>
      ) : null}
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader><TableRow><TableHead>Versão</TableHead><TableHead>Título</TableHead><TableHead>Status</TableHead><TableHead>Vigência</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader>
          <TableBody>
            {(query.data ?? []).map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.numero_versao}</TableCell>
                <TableCell>{item.titulo}</TableCell>
                <TableCell>{label(item.status)}</TableCell>
                <TableCell>{formatDateOnly(item.data_inicio_vigencia)} - {formatDateOnly(item.data_fim_vigencia)}</TableCell>
                <TableCell className="text-right"><Button type="button" variant="ghost" size="icon" aria-label="Visualizar acordo de admissão" onClick={() => { setOpen(false); setEditing(null); setViewing(item); }}><Eye className="h-4 w-4" /></Button></TableCell>
              </TableRow>
            ))}
            {!query.data?.length ? <TableRow><TableCell colSpan={5} className="h-24 text-center text-muted-foreground">{query.isLoading ? "Carregando..." : "Nenhum acordo de admissão registrado."}</TableCell></TableRow> : null}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function Sessoes({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [viewing, setViewing] = useState<SessaoSubmissao | null>(null);
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<SessaoFormData>(defaultSessaoFormData());
  const sessoes = useQuery({ queryKey: ["admissao", "sessoes", processoId, pageIndex, pageSize], queryFn: () => listSessoesSubmissao(processoId, { limit: pageSize, offset: pageIndex * pageSize }) });
  const acordos = useQuery({ queryKey: ["admissao", "acordos", processoId], queryFn: () => listAcordosAdmissao(processoId) });
  const create = useMutation({
    mutationFn: (payload: Partial<SessaoSubmissao>) => createSessaoSubmissao(processoId, payload),
    onSuccess: () => {
      setOpen(false);
      setData(defaultSessaoFormData());
      return invalidate(queryClient, processoId);
    },
  });
  const activeAgreement = (acordos.data ?? []).find((item) => item.status === "ATIVO") ?? acordos.data?.[0];
  const total = sessoes.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    create.mutate(sessaoPayload(data));
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Button type="button" onClick={() => setOpen((value) => !value)}><Plus className="h-4 w-4" />Nova sessão</Button></div>
      {!activeAgreement ? <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Crie ou ative um acordo antes de registrar sessões.</p> : null}
      {open ? (
        <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Acordo de admissão"><Input readOnly disabled value={activeAgreement ? `Versão ${activeAgreement.numero_versao} - ${activeAgreement.titulo}` : "Sem acordo vigente"} /></Field>
          <Field label="Título"><Input required value={data.titulo} onChange={(event) => setData({ ...data, titulo: event.target.value })} /></Field>
          <Field label="Data início"><Input required type="datetime-local" value={data.data_inicio} onChange={(event) => setData({ ...data, data_inicio: event.target.value })} /></Field>
          <Field label="Canal de submissão"><select required className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.canal_submissao} onChange={(event) => setData({ ...data, canal_submissao: event.target.value as SessaoFormData["canal_submissao"] })}>{CANAIS_SUBMISSAO.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
          <Field label="Suporte"><select required className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.tipo_suporte} onChange={(event) => setData({ ...data, tipo_suporte: event.target.value as SessaoSubmissao["tipo_suporte"] })}><option value="DIGITAL">Digital</option><option value="FISICO">Físico</option><option value="HIBRIDO">Híbrido</option></select></Field>
          <Field label="Responsável pelo envio"><Input value={data.responsavel_envio} onChange={(event) => setData({ ...data, responsavel_envio: event.target.value })} /></Field>
          <Field label="Responsável pelo recebimento"><Input value={data.responsavel_recebimento} onChange={(event) => setData({ ...data, responsavel_recebimento: event.target.value })} /></Field>
          <Field label="Volume informado"><Input value={data.volume_informado} onChange={(event) => setData({ ...data, volume_informado: event.target.value })} /></Field>
          <Field label="Caminho de origem"><Input value={data.caminho_origem} onChange={(event) => setData({ ...data, caminho_origem: event.target.value })} /></Field>
          <div className="md:col-span-2"><Field label="Observações"><textarea className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.observacoes} onChange={(event) => setData({ ...data, observacoes: event.target.value })} /></Field></div>
          <div className="flex gap-2 md:col-span-2"><Button type="submit" disabled={create.isPending || !activeAgreement}>{create.isPending ? "Salvando..." : "Salvar"}</Button><Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button></div>
          {create.error ? <p className="text-sm text-destructive md:col-span-2">{create.error.message}</p> : null}
        </form>
      ) : null}
      {viewing ? <SessaoDetails sessao={viewing} acordo={acordos.data?.find((item) => item.id === viewing.id_acordo_utilizado)} onClose={() => setViewing(null)} /> : null}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2">
        <p className="text-sm text-muted-foreground">{sessoes.data?.items.length ?? 0} registros de {total} | página {pageIndex + 1} de {totalPages}</p>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" size="sm" disabled={sessoes.isLoading || pageIndex === 0} onClick={() => setPageIndex(0)}>Primeira</Button>
          <Button type="button" variant="outline" size="sm" disabled={sessoes.isLoading || pageIndex === 0} onClick={() => setPageIndex((value) => Math.max(0, value - 1))}>Anterior</Button>
          <Button type="button" variant="outline" size="sm" disabled={sessoes.isLoading || pageIndex >= totalPages - 1} onClick={() => setPageIndex((value) => value + 1)}>Próxima</Button>
          <Button type="button" variant="outline" size="sm" disabled={sessoes.isLoading || pageIndex >= totalPages - 1} onClick={() => setPageIndex(totalPages - 1)}>Última</Button>
          <Label htmlFor="sessoes-page-size" className="text-sm text-muted-foreground">Por página:</Label>
          <select id="sessoes-page-size" className="h-9 rounded-md border bg-background px-2 text-sm" value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPageIndex(0); }}><option value={10}>10</option><option value={20}>20</option><option value={50}>50</option></select>
        </div>
      </div>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader><TableRow><TableHead>Nº</TableHead><TableHead>Título</TableHead><TableHead>Canal</TableHead><TableHead>Status</TableHead><TableHead>Acordo</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader>
          <TableBody>
            {(sessoes.data?.items ?? []).map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.numero_sessao}</TableCell>
                <TableCell>{item.titulo}</TableCell>
                <TableCell>{label(item.canal_submissao)}</TableCell>
                <TableCell>{label(item.status)}</TableCell>
                <TableCell>{acordos.data?.find((acordo) => acordo.id === item.id_acordo_utilizado)?.numero_versao ?? item.id_acordo_utilizado.slice(0, 8)}</TableCell>
                <TableCell><div className="flex justify-end gap-1"><Button type="button" variant="ghost" size="icon" aria-label="Visualizar sessão" onClick={() => setViewing(item)}><Eye className="h-4 w-4" /></Button><Button asChild variant="outline" size="sm"><Link href={`/admissao/sessoes/${item.id}/status`}>Alterar status</Link></Button></div></TableCell>
              </TableRow>
            ))}
            {!sessoes.data?.items.length ? <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{sessoes.isLoading ? "Carregando..." : "Nenhuma sessão registrada."}</TableCell></TableRow> : null}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function Sips({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const sips = useQuery({ queryKey: ["admissao", "sips", processoId], queryFn: () => listSipsProcesso(processoId) });
  const sessoes = useQuery({ queryKey: ["admissao", "sessoes", processoId], queryFn: () => listSessoesSubmissao(processoId) });
  const create = useMutation({ mutationFn: (payload: Record<string, unknown>) => createSipAdmissao(String(payload.sessao_id), payload), onSuccess: () => invalidate(queryClient, processoId) });
  const validate = useMutation({ mutationFn: validarSipAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const reject = useMutation({ mutationFn: rejeitarSipAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const session = sessoes.data?.items[0];
  return <CrudPanel title="Novo SIP" mutationError={create.error?.message} onSubmit={(data) => create.mutate({ sessao_id: session?.id, codigo_sip: data.codigo, titulo: data.titulo, tipo_sip: data.suporte || "DIGITAL", data_recebimento: toDateTime(data.data), caminho_armazenamento_temporario: data.responsavel, observacoes: data.descricao })}>
    {!session ? <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Registre uma sessão antes de adicionar SIPs.</p> : null}
    <div className="overflow-hidden rounded-md border"><Table><TableHeader><TableRow><TableHead>Código</TableHead><TableHead>Título</TableHead><TableHead>Tipo</TableHead><TableHead>Status</TableHead><TableHead>Recebimento</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader><TableBody>{(sips.data ?? []).map((item) => <TableRow key={item.id}><TableCell>{item.codigo_sip}</TableCell><TableCell>{item.titulo}</TableCell><TableCell>{label(item.tipo_sip)}</TableCell><TableCell>{label(item.status)}</TableCell><TableCell>{formatDate(item.data_recebimento)}</TableCell><TableCell><div className="flex justify-end gap-1"><Button type="button" variant="outline" size="sm" disabled={validate.isPending || item.status === "VALIDADO"} onClick={() => validate.mutate(item.id)}><Check className="h-4 w-4" />Validar</Button><Button type="button" variant="outline" size="sm" disabled={reject.isPending || item.status === "REJEITADO"} onClick={() => reject.mutate(item.id)}><X className="h-4 w-4" />Rejeitar</Button></div></TableCell></TableRow>)}{!sips.data?.length ? <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{sips.isLoading ? "Carregando..." : "Nenhum SIP registrado."}</TableCell></TableRow> : null}</TableBody></Table></div>
  </CrudPanel>;
}

function Eventos({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admissao", "eventos", processoId], queryFn: () => listEventosAdmissao(processoId) });
  const mutation = useMutation({ mutationFn: (payload: Record<string, unknown>) => createEventoAdmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  return <CrudPanel title="Novo evento manual" mutationError={mutation.error?.message} onSubmit={(data) => mutation.mutate({ tipo_evento: data.tipo || "APROVACAO", descricao: data.descricao || data.titulo, resultado: "INFORMATIVO", agente: data.responsavel, data_evento: toDateTime(data.data) })}>
    <SimpleTable headers={["Data", "Tipo", "Resultado", "Descrição", "Agente"]} rows={(query.data ?? []).map((item) => [formatDate(item.data_evento), label(item.tipo_evento), label(item.resultado), item.descricao, item.agente || "-"])} loading={query.isLoading} />
  </CrudPanel>;
}

function ReuniaoDetails({ reuniao, onClose, onEdit }: { reuniao: ReuniaoAdmissao; onClose: () => void; onEdit: () => void }) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", reuniao.id],
    ["ID do processo", reuniao.id_processo_admissao],
    ["Número", reuniao.numero_reuniao],
    ["Título", reuniao.titulo],
    ["Tipo de reunião", label(reuniao.tipo_reuniao)],
    ["Data da reunião", formatDate(reuniao.data_reuniao)],
    ["Participantes", reuniao.participantes],
    ["Criado em", formatDate(reuniao.criado_em)],
    ["Atualizado em", formatDate(reuniao.atualizado_em)],
  ];
  return (
    <section className="space-y-4 rounded-md border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-base font-semibold">{reuniao.titulo}</h3>
          <p className="text-sm text-muted-foreground">Reunião {reuniao.numero_reuniao}</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={onEdit}><Edit className="h-4 w-4" />Editar</Button>
          <Button type="button" variant="outline" size="sm" onClick={onClose}>Fechar</Button>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {fields.map(([name, value]) => <Detail key={name} label={name} value={value} />)}
      </div>
      <LongText label="Descrição" value={reuniao.descricao} />
      <LongText label="Deliberações" value={reuniao.deliberacoes} />
      <LongText label="Pendências" value={reuniao.pendencias} />
      <LongText label="Próximos passos" value={reuniao.proximos_passos} />
    </section>
  );
}

function AcordoDetails({
  acordo,
  isLatest,
  isVersioning,
  onClose,
  onEdit,
  onNewVersion,
}: {
  acordo: AcordoAdmissao;
  isLatest: boolean;
  isVersioning: boolean;
  onClose: () => void;
  onEdit: () => void;
  onNewVersion: () => void;
}) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", acordo.id],
    ["ID do processo", acordo.id_processo_admissao],
    ["Versão", acordo.numero_versao],
    ["Título", acordo.titulo],
    ["Status", label(acordo.status)],
    ["Data início vigência", formatDateOnly(acordo.data_inicio_vigencia)],
    ["Data fim vigência", formatDateOnly(acordo.data_fim_vigencia)],
    ["Periodicidade submissão", acordo.periodicidade_submissao],
    ["Documento do acordo", acordo.documento_acordo],
    ["Criado por", acordo.criado_por],
    ["Atualizado por", acordo.atualizado_por],
    ["Criado em", formatDate(acordo.criado_em)],
    ["Atualizado em", formatDate(acordo.atualizado_em)],
  ];
  return (
    <section className="space-y-4 rounded-md border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-base font-semibold">{acordo.titulo}</h3>
          <p className="text-sm text-muted-foreground">Acordo de admissão versão {acordo.numero_versao}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={onEdit}><Edit className="h-4 w-4" />Editar</Button>
          <Button type="button" variant="outline" size="sm" disabled={isVersioning} onClick={onNewVersion}>Nova versão</Button>
          <Button type="button" variant="outline" size="sm" onClick={onClose}>Fechar</Button>
        </div>
      </div>
      {!isLatest ? <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Apenas a última versão do acordo de admissão pode ficar ativa.</p> : null}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {fields.map(([name, value]) => <Detail key={name} label={name} value={value} />)}
      </div>
      <LongText label="Descrição" value={acordo.descricao} />
      <LongText label="Motivo revisão" value={acordo.motivo_revisao} />
      <LongText label="Regras empacotamento" value={acordo.regras_empacotamento} />
      <LongText label="Regras nomenclatura" value={acordo.regras_nomenclatura} />
      <LongText label="Formatos aceitos" value={acordo.formatos_aceitos} />
      <LongText label="Metadados obrigatórios" value={acordo.metadados_obrigatorios} />
      <LongText label="Requisitos fixidez" value={acordo.requisitos_fixidez} />
      <LongText label="Requisitos representação" value={acordo.requisitos_representacao} />
      <LongText label="Política validação" value={acordo.politica_validacao} />
      <LongText label="Política rejeição" value={acordo.politica_rejeicao} />
      <LongText label="Política normalização" value={acordo.politica_normalizacao} />
      <LongText label="Política sigilo" value={acordo.politica_sigilo} />
      <LongText label="Observações" value={acordo.observacoes} />
    </section>
  );
}

function SessaoDetails({ sessao, acordo, onClose }: { sessao: SessaoSubmissao; acordo?: AcordoAdmissao; onClose: () => void }) {
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", sessao.id],
    ["ID do processo", sessao.id_processo_admissao],
    ["Número", sessao.numero_sessao],
    ["Título", sessao.titulo],
    ["Status", label(sessao.status)],
    ["Canal de submissão", label(sessao.canal_submissao)],
    ["Acordo de admissão", acordo ? `Versão ${acordo.numero_versao} - ${acordo.titulo}` : sessao.id_acordo_utilizado],
    ["Tipo de suporte", label(sessao.tipo_suporte)],
    ["Data início", formatDate(sessao.data_inicio)],
    ["Data fim", formatDate(sessao.data_fim)],
    ["Responsável envio", sessao.responsavel_envio],
    ["Responsável recebimento", sessao.responsavel_recebimento],
    ["Volume informado", sessao.volume_informado],
    ["Volume recebido", sessao.volume_recebido],
    ["Caminho origem", sessao.caminho_origem],
    ["Quarentena", sessao.caminho_destino_quarentena],
    ["Criado por", sessao.criado_por],
    ["Atualizado por", sessao.atualizado_por],
    ["Criado em", formatDate(sessao.criado_em)],
    ["Atualizado em", formatDate(sessao.atualizado_em)],
  ];
  return (
    <section className="space-y-4 rounded-md border p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-base font-semibold">{sessao.titulo}</h3>
          <p className="text-sm text-muted-foreground">Sessão {sessao.numero_sessao}</p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={onClose}>Fechar</Button>
      </div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {fields.map(([name, value]) => <Detail key={name} label={name} value={value} />)}
      </div>
      <LongText label="Resultado validação" value={sessao.resultado_validacao} />
      <LongText label="Descrição" value={sessao.descricao} />
      <LongText label="Observações" value={sessao.observacoes} />
    </section>
  );
}

function defaultReuniaoFormData(): ReuniaoFormData {
  return {
    titulo: "",
    tipo_reuniao: "NEGOCIACAO_INICIAL",
    data_reuniao: toDateTimeLocalInput(new Date().toISOString()),
    participantes: "",
    descricao: "",
    deliberacoes: "",
    pendencias: "",
    proximos_passos: "",
  };
}

function defaultAcordoFormData(): AcordoFormData {
  return {
    titulo: "",
    descricao: "",
    status: "RASCUNHO",
    data_inicio_vigencia: "",
    data_fim_vigencia: "",
    motivo_revisao: "",
    regras_empacotamento: "",
    regras_nomenclatura: "",
    formatos_aceitos: "",
    metadados_obrigatorios: "",
    requisitos_fixidez: "",
    requisitos_representacao: "",
    politica_validacao: "",
    politica_rejeicao: "",
    politica_normalizacao: "",
    politica_sigilo: "",
    periodicidade_submissao: "",
    observacoes: "",
    documento_acordo: "",
  };
}

function defaultSessaoFormData(): SessaoFormData {
  return {
    titulo: "",
    data_inicio: toDateTimeLocalInput(new Date().toISOString()),
    canal_submissao: "UPLOAD",
    tipo_suporte: "DIGITAL",
    responsavel_envio: "",
    responsavel_recebimento: "",
    volume_informado: "",
    caminho_origem: "",
    observacoes: "",
  };
}

function acordoToFormData(acordo: AcordoAdmissao): AcordoFormData {
  return {
    titulo: acordo.titulo,
    descricao: acordo.descricao ?? "",
    status: acordo.status,
    data_inicio_vigencia: acordo.data_inicio_vigencia ?? "",
    data_fim_vigencia: acordo.data_fim_vigencia ?? "",
    motivo_revisao: acordo.motivo_revisao ?? "",
    regras_empacotamento: acordo.regras_empacotamento ?? "",
    regras_nomenclatura: acordo.regras_nomenclatura ?? "",
    formatos_aceitos: acordo.formatos_aceitos ?? "",
    metadados_obrigatorios: acordo.metadados_obrigatorios ?? "",
    requisitos_fixidez: acordo.requisitos_fixidez ?? "",
    requisitos_representacao: acordo.requisitos_representacao ?? "",
    politica_validacao: acordo.politica_validacao ?? "",
    politica_rejeicao: acordo.politica_rejeicao ?? "",
    politica_normalizacao: acordo.politica_normalizacao ?? "",
    politica_sigilo: acordo.politica_sigilo ?? "",
    periodicidade_submissao: acordo.periodicidade_submissao ?? "",
    observacoes: acordo.observacoes ?? "",
    documento_acordo: acordo.documento_acordo ?? "",
  };
}

function acordoPayload(data: AcordoFormData): Partial<AcordoAdmissao> {
  const nullable = (value: string) => value.trim() || null;
  return {
    titulo: data.titulo.trim(),
    descricao: nullable(data.descricao),
    status: data.status,
    data_inicio_vigencia: data.data_inicio_vigencia || null,
    data_fim_vigencia: data.data_fim_vigencia || null,
    motivo_revisao: nullable(data.motivo_revisao),
    regras_empacotamento: nullable(data.regras_empacotamento),
    regras_nomenclatura: nullable(data.regras_nomenclatura),
    formatos_aceitos: nullable(data.formatos_aceitos),
    metadados_obrigatorios: nullable(data.metadados_obrigatorios),
    requisitos_fixidez: nullable(data.requisitos_fixidez),
    requisitos_representacao: nullable(data.requisitos_representacao),
    politica_validacao: nullable(data.politica_validacao),
    politica_rejeicao: nullable(data.politica_rejeicao),
    politica_normalizacao: nullable(data.politica_normalizacao),
    politica_sigilo: nullable(data.politica_sigilo),
    periodicidade_submissao: nullable(data.periodicidade_submissao),
    observacoes: nullable(data.observacoes),
    documento_acordo: nullable(data.documento_acordo),
  };
}

function sessaoPayload(data: SessaoFormData): Partial<SessaoSubmissao> {
  const nullable = (value: string) => value.trim() || null;
  return {
    titulo: data.titulo.trim(),
    data_inicio: data.data_inicio ? new Date(data.data_inicio).toISOString() : new Date().toISOString(),
    canal_submissao: data.canal_submissao,
    tipo_suporte: data.tipo_suporte,
    responsavel_envio: nullable(data.responsavel_envio),
    responsavel_recebimento: nullable(data.responsavel_recebimento),
    volume_informado: nullable(data.volume_informado),
    caminho_origem: nullable(data.caminho_origem),
    observacoes: nullable(data.observacoes),
  };
}

function AcordoTextarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <div className="md:col-span-2"><Field label={label}><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></Field></div>;
}

function reuniaoPayload(data: ReuniaoFormData): Partial<ReuniaoAdmissao> {
  const nullable = (value: string) => value.trim() || null;
  return {
    titulo: data.titulo.trim(),
    tipo_reuniao: data.tipo_reuniao,
    data_reuniao: data.data_reuniao ? new Date(data.data_reuniao).toISOString() : new Date().toISOString(),
    participantes: nullable(data.participantes),
    descricao: nullable(data.descricao),
    deliberacoes: nullable(data.deliberacoes),
    pendencias: nullable(data.pendencias),
    proximos_passos: nullable(data.proximos_passos),
  };
}

function toDateInput(value?: string | null) {
  return value ? toDateTimeLocalInput(value) : "";
}

function toDateTimeLocalInput(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function CrudPanel({ title, mutationError, onSubmit, children }: { title: string; mutationError?: string; onSubmit: (data: Record<string, string>) => void; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<Record<string, string>>({ data: new Date().toISOString().slice(0, 10), suporte: "DIGITAL" });
  const isSessao = title === "Nova sessão";
  return <div className="space-y-4"><div className="flex justify-end"><Button type="button" onClick={() => setOpen((value) => !value)}><Plus className="h-4 w-4" />{title}</Button></div>{open ? <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={(event) => { event.preventDefault(); onSubmit(data); setOpen(false); }}><Field label="Título"><Input required value={data.titulo ?? ""} onChange={(event) => setData({ ...data, titulo: event.target.value })} /></Field>{!isSessao ? <Field label="Código SIP"><Input value={data.codigo ?? ""} onChange={(event) => setData({ ...data, codigo: event.target.value })} /></Field> : null}<Field label="Data"><Input type="date" value={data.data ?? ""} onChange={(event) => setData({ ...data, data: event.target.value })} /></Field><Field label={isSessao ? "Canal de submissão" : "Tipo/Status"}>{isSessao ? <select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.tipo ?? "UPLOAD"} onChange={(event) => setData({ ...data, tipo: event.target.value })}>{CANAIS_SUBMISSAO.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select> : <Input placeholder="Ex.: APROVACAO" value={data.tipo ?? ""} onChange={(event) => setData({ ...data, tipo: event.target.value })} />}</Field><Field label="Suporte"><select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.suporte ?? "DIGITAL"} onChange={(event) => setData({ ...data, suporte: event.target.value })}><option value="DIGITAL">Digital</option><option value="FISICO">Físico</option><option value="HIBRIDO">Híbrido</option></select></Field><Field label="Responsável/Caminho"><Input value={data.responsavel ?? ""} onChange={(event) => setData({ ...data, responsavel: event.target.value })} /></Field><div className="md:col-span-2"><Field label="Descrição"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.descricao ?? ""} onChange={(event) => setData({ ...data, descricao: event.target.value })} /></Field></div><div className="flex gap-2 md:col-span-2"><Button type="submit">Salvar</Button><Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button></div>{mutationError ? <p className="text-sm text-destructive md:col-span-2">{mutationError}</p> : null}</form> : null}{children}</div>;
}

function SimpleTable({ headers, rows, loading }: { headers: string[]; rows: Array<Array<React.ReactNode>>; loading: boolean }) {
  return <div className="overflow-hidden rounded-md border"><Table><TableHeader><TableRow>{headers.map((header) => <TableHead key={header}>{header}</TableHead>)}</TableRow></TableHeader><TableBody>{rows.length ? rows.map((row, index) => <TableRow key={index}>{row.map((cell, cellIndex) => <TableCell key={cellIndex}>{cell}</TableCell>)}</TableRow>) : <TableRow><TableCell colSpan={headers.length} className="h-24 text-center text-muted-foreground">{loading ? "Carregando..." : "Nenhum registro encontrado."}</TableCell></TableRow>}</TableBody></Table></div>;
}

function Detail({ label, value }: { label: string; value?: React.ReactNode }) { return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 break-words text-sm">{value || "-"}</div></div>; }
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <div className="space-y-2"><Label>{label}</Label>{children}</div>; }
function LongText({ label, value }: { label: string; value?: string | null }) { return <section className="space-y-1 rounded-md border p-3"><h3 className="text-xs font-medium uppercase text-muted-foreground">{label}</h3><p className="whitespace-pre-wrap break-words text-sm">{value || "-"}</p></section>; }
function label(value?: string | null) { return value ? value.replaceAll("_", " ") : "-"; }
function formatDate(value?: string | null) { return value ? new Date(value).toLocaleString("pt-BR") : "-"; }
function formatDateOnly(value?: string | null) { return value ? new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR") : "-"; }
function toDateTime(value?: string) { return value ? `${value}T09:00:00` : new Date().toISOString(); }
function tabLabel(value: string) {
  if (value === "acordos") return "Acordos de admissão";
  return value.charAt(0).toUpperCase() + value.slice(1);
}
function invalidate(queryClient: ReturnType<typeof useQueryClient>, processoId: string) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ["admissao"] }),
    queryClient.invalidateQueries({ queryKey: ["admissao", "processos", processoId] }),
  ]);
}
