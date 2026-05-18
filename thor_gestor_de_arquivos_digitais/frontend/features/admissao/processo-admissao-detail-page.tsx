"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Edit, Plus, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ativarAcordoAdmissao,
  createAcordoAdmissao,
  createEventoAdmissao,
  createReuniaoAdmissao,
  createSessaoSubmissao,
  createSipAdmissao,
  finalizarSessaoSubmissao,
  getProcessoAdmissao,
  listAcordosAdmissao,
  listEventosAdmissao,
  listReunioesAdmissao,
  listSessoesSubmissao,
  listSipsProcesso,
  novaVersaoAcordoAdmissao,
  rejeitarSipAdmissao,
  validarSipAdmissao,
} from "@/lib/api/admissao";

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
  const mutation = useMutation({ mutationFn: (payload: Record<string, unknown>) => createReuniaoAdmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  return <CrudPanel title="Nova reunião" mutationError={mutation.error?.message} onSubmit={(data) => mutation.mutate({ titulo: data.titulo, tipo_reuniao: data.tipo || "NEGOCIACAO_INICIAL", data_reuniao: toDateTime(data.data), participantes: data.responsavel, deliberacoes: data.descricao })}>
    <SimpleTable headers={["Nº", "Título", "Tipo", "Data", "Participantes"]} rows={(query.data ?? []).map((item) => [item.numero_reuniao, item.titulo, label(item.tipo_reuniao), formatDate(item.data_reuniao), item.participantes || "-"])} loading={query.isLoading} />
  </CrudPanel>;
}

function Acordos({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admissao", "acordos", processoId], queryFn: () => listAcordosAdmissao(processoId) });
  const create = useMutation({ mutationFn: (payload: Record<string, unknown>) => createAcordoAdmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const activate = useMutation({ mutationFn: ativarAcordoAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const version = useMutation({ mutationFn: novaVersaoAcordoAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  return <CrudPanel title="Nova versão de acordo" mutationError={create.error?.message} onSubmit={(data) => create.mutate({ titulo: data.titulo, status: data.tipo || "RASCUNHO", data_inicio_vigencia: data.data || null, regras_empacotamento: data.descricao })}>
    <div className="overflow-hidden rounded-md border"><Table><TableHeader><TableRow><TableHead>Versão</TableHead><TableHead>Título</TableHead><TableHead>Status</TableHead><TableHead>Vigência</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader><TableBody>{(query.data ?? []).map((item) => <TableRow key={item.id}><TableCell>{item.numero_versao}</TableCell><TableCell>{item.titulo}</TableCell><TableCell>{label(item.status)}</TableCell><TableCell>{item.data_inicio_vigencia || "-"}</TableCell><TableCell><div className="flex justify-end gap-1"><Button type="button" variant="outline" size="sm" disabled={activate.isPending || item.status === "ATIVO"} onClick={() => activate.mutate(item.id)}><Check className="h-4 w-4" />Ativar</Button><Button type="button" variant="outline" size="sm" disabled={version.isPending} onClick={() => version.mutate(item.id)}>Nova versão</Button></div></TableCell></TableRow>)}{!query.data?.length ? <TableRow><TableCell colSpan={5} className="h-24 text-center text-muted-foreground">{query.isLoading ? "Carregando..." : "Nenhum acordo registrado."}</TableCell></TableRow> : null}</TableBody></Table></div>
  </CrudPanel>;
}

function Sessoes({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const sessoes = useQuery({ queryKey: ["admissao", "sessoes", processoId], queryFn: () => listSessoesSubmissao(processoId) });
  const acordos = useQuery({ queryKey: ["admissao", "acordos", processoId], queryFn: () => listAcordosAdmissao(processoId) });
  const create = useMutation({ mutationFn: (payload: Record<string, unknown>) => createSessaoSubmissao(processoId, payload), onSuccess: () => invalidate(queryClient, processoId) });
  const finish = useMutation({ mutationFn: finalizarSessaoSubmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const activeAgreement = (acordos.data ?? []).find((item) => item.status === "ATIVO") ?? acordos.data?.[0];
  return <CrudPanel title="Nova sessão" mutationError={create.error?.message} onSubmit={(data) => create.mutate({ titulo: data.titulo, id_acordo_utilizado: activeAgreement?.id, data_inicio: toDateTime(data.data), canal_submissao: data.tipo || "UPLOAD", tipo_suporte: data.suporte || "DIGITAL", responsavel_envio: data.responsavel, observacoes: data.descricao })}>
    {!activeAgreement ? <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Crie ou ative um acordo antes de registrar sessões.</p> : null}
    <div className="overflow-hidden rounded-md border"><Table><TableHeader><TableRow><TableHead>Nº</TableHead><TableHead>Título</TableHead><TableHead>Canal</TableHead><TableHead>Status</TableHead><TableHead>Acordo</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader><TableBody>{(sessoes.data ?? []).map((item) => <TableRow key={item.id}><TableCell>{item.numero_sessao}</TableCell><TableCell>{item.titulo}</TableCell><TableCell>{label(item.canal_submissao)}</TableCell><TableCell>{label(item.status)}</TableCell><TableCell>{item.id_acordo_utilizado.slice(0, 8)}</TableCell><TableCell className="text-right"><Button type="button" variant="outline" size="sm" disabled={finish.isPending || item.status === "FINALIZADA"} onClick={() => finish.mutate(item.id)}>Finalizar</Button></TableCell></TableRow>)}{!sessoes.data?.length ? <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">{sessoes.isLoading ? "Carregando..." : "Nenhuma sessão registrada."}</TableCell></TableRow> : null}</TableBody></Table></div>
  </CrudPanel>;
}

function Sips({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient();
  const sips = useQuery({ queryKey: ["admissao", "sips", processoId], queryFn: () => listSipsProcesso(processoId) });
  const sessoes = useQuery({ queryKey: ["admissao", "sessoes", processoId], queryFn: () => listSessoesSubmissao(processoId) });
  const create = useMutation({ mutationFn: (payload: Record<string, unknown>) => createSipAdmissao(String(payload.sessao_id), payload), onSuccess: () => invalidate(queryClient, processoId) });
  const validate = useMutation({ mutationFn: validarSipAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const reject = useMutation({ mutationFn: rejeitarSipAdmissao, onSuccess: () => invalidate(queryClient, processoId) });
  const session = sessoes.data?.[0];
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

function CrudPanel({ title, mutationError, onSubmit, children }: { title: string; mutationError?: string; onSubmit: (data: Record<string, string>) => void; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<Record<string, string>>({ data: new Date().toISOString().slice(0, 10), suporte: "DIGITAL" });
  return <div className="space-y-4"><div className="flex justify-end"><Button type="button" onClick={() => setOpen((value) => !value)}><Plus className="h-4 w-4" />{title}</Button></div>{open ? <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={(event) => { event.preventDefault(); onSubmit(data); setOpen(false); }}><Field label="Título"><Input required value={data.titulo ?? ""} onChange={(event) => setData({ ...data, titulo: event.target.value })} /></Field><Field label="Código SIP"><Input value={data.codigo ?? ""} onChange={(event) => setData({ ...data, codigo: event.target.value })} /></Field><Field label="Data"><Input type="date" value={data.data ?? ""} onChange={(event) => setData({ ...data, data: event.target.value })} /></Field><Field label="Tipo/Status/Canal"><Input placeholder="Ex.: ATIVO, UPLOAD" value={data.tipo ?? ""} onChange={(event) => setData({ ...data, tipo: event.target.value })} /></Field><Field label="Suporte"><select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={data.suporte ?? "DIGITAL"} onChange={(event) => setData({ ...data, suporte: event.target.value })}><option value="DIGITAL">Digital</option><option value="FISICO">Físico</option><option value="HIBRIDO">Híbrido</option></select></Field><Field label="Responsável/Caminho"><Input value={data.responsavel ?? ""} onChange={(event) => setData({ ...data, responsavel: event.target.value })} /></Field><div className="md:col-span-2"><Field label="Descrição"><textarea className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={data.descricao ?? ""} onChange={(event) => setData({ ...data, descricao: event.target.value })} /></Field></div><div className="flex gap-2 md:col-span-2"><Button type="submit">Salvar</Button><Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button></div>{mutationError ? <p className="text-sm text-destructive md:col-span-2">{mutationError}</p> : null}</form> : null}{children}</div>;
}

function SimpleTable({ headers, rows, loading }: { headers: string[]; rows: Array<Array<React.ReactNode>>; loading: boolean }) {
  return <div className="overflow-hidden rounded-md border"><Table><TableHeader><TableRow>{headers.map((header) => <TableHead key={header}>{header}</TableHead>)}</TableRow></TableHeader><TableBody>{rows.length ? rows.map((row, index) => <TableRow key={index}>{row.map((cell, cellIndex) => <TableCell key={cellIndex}>{cell}</TableCell>)}</TableRow>) : <TableRow><TableCell colSpan={headers.length} className="h-24 text-center text-muted-foreground">{loading ? "Carregando..." : "Nenhum registro encontrado."}</TableCell></TableRow>}</TableBody></Table></div>;
}

function Detail({ label, value }: { label: string; value?: React.ReactNode }) { return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 break-words text-sm">{value || "-"}</div></div>; }
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <div className="space-y-2"><Label>{label}</Label>{children}</div>; }
function LongText({ label, value }: { label: string; value?: string | null }) { return <section className="space-y-1 rounded-md border p-3"><h3 className="text-xs font-medium uppercase text-muted-foreground">{label}</h3><p className="whitespace-pre-wrap break-words text-sm">{value || "-"}</p></section>; }
function label(value?: string | null) { return value ? value.replaceAll("_", " ") : "-"; }
function formatDate(value?: string | null) { return value ? new Date(value).toLocaleString("pt-BR") : "-"; }
function toDateTime(value?: string) { return value ? `${value}T09:00:00` : new Date().toISOString(); }
function tabLabel(value: string) { return value.charAt(0).toUpperCase() + value.slice(1); }
function invalidate(queryClient: ReturnType<typeof useQueryClient>, processoId: string) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ["admissao"] }),
    queryClient.invalidateQueries({ queryKey: ["admissao", "processos", processoId] }),
  ]);
}
