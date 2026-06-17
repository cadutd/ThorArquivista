"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRightLeft, Edit, FileJson, Upload } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { MidiaForm } from "@/features/midias/midia-form";
import {
  getMidia,
  getVerificacaoIntegridadeMidia,
  importarRelatorioVerificacaoIntegridade,
  listEventosMidia,
  listVerificacoesIntegridadeMidia,
  registrarVerificacaoIntegridadeManual,
} from "@/lib/api/domain";
import type {
  EventoMidiaArmazenamento,
  EventoPreservacao,
  MidiaArmazenamento,
  ResultadoVerificacaoIntegridade,
  VerificacaoIntegridadeMidia,
} from "@/types/domain";

export function MidiaViewPage({ midiaId }: { midiaId: number }) {
  const query = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const eventosQuery = useQuery({
    queryKey: ["midias", midiaId, "eventos"],
    queryFn: () => listEventosMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const verificacoesQuery = useQuery({
    queryKey: ["midias", midiaId, "verificacoes-integridade"],
    queryFn: () => listVerificacoesIntegridadeMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });
  const midia = query.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar midia</h1>
          <p className="text-sm text-muted-foreground">Consulta dos metadados da midia de armazenamento.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {midia ? (
            <Button asChild variant="outline">
              <Link href={`/midias/${midia.id}/migrar`}>
                <ArrowRightLeft className="h-4 w-4" />
                Migrar midia
              </Link>
            </Button>
          ) : null}
          {midia ? (
            <Button asChild variant="outline">
              <Link href={`/midias/${midia.id}/editar`}>
                <Edit className="h-4 w-4" />
                Editar
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="outline">
            <Link href="/midias">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
        </div>
      </div>

      <Tabs defaultValue="dados">
        <TabsList>
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="integridade">Verificacoes de integridade</TabsTrigger>
          <TabsTrigger value="historico">Historico de eventos</TabsTrigger>
        </TabsList>
        <TabsContent value="dados">
          <Card>
            <CardHeader>
              <CardTitle>{midia?.nome ?? "Midia de armazenamento"}</CardTitle>
              <CardDescription>
                {query.isLoading
                  ? "Carregando dados da midia."
                  : midia
                    ? midia.tipo_midia?.nome ?? "Tipo nao informado"
                    : "Midia nao encontrada."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {query.isLoading ? (
                <p className="text-sm text-muted-foreground">Carregando midia...</p>
              ) : query.error ? (
                <p className="text-sm text-destructive">{query.error.message}</p>
              ) : midia ? (
                <MidiaDetails midia={midia} />
              ) : (
                <p className="text-sm text-muted-foreground">Midia nao encontrada.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="historico">
          <Card>
            <CardHeader>
              <CardTitle>Historico de eventos</CardTitle>
              <CardDescription>Eventos PREMIS registrados diretamente sobre esta midia.</CardDescription>
            </CardHeader>
            <CardContent>
              {eventosQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Carregando eventos...</p>
              ) : eventosQuery.error ? (
                <p className="text-sm text-destructive">{eventosQuery.error.message}</p>
              ) : (
                <EventosMidiaTable data={eventosQuery.data ?? []} />
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="integridade">
          <VerificacoesIntegridadePanel
            midiaId={midiaId}
            data={verificacoesQuery.data?.items ?? []}
            isLoading={verificacoesQuery.isLoading}
            error={verificacoesQuery.error?.message}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export function MidiaEditPage({ midiaId }: { midiaId: number }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["midias", midiaId],
    queryFn: () => getMidia(midiaId),
    enabled: Number.isFinite(midiaId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar midia</h1>
          <p className="text-sm text-muted-foreground">Atualize os metadados da midia de armazenamento.</p>
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
          <CardTitle>Dados da midia</CardTitle>
          <CardDescription>Campos obrigatorios sao validados antes do salvamento.</CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando midia...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <MidiaForm midia={query.data} onCreated={() => router.push(`/midias/${midiaId}`)} />
          ) : (
            <p className="text-sm text-muted-foreground">Midia nao encontrada.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MidiaDetails({ midia }: { midia: MidiaArmazenamento }) {
  const fields: Array<[string, ReactNode]> = [
    ["ID", midia.id],
    ["Nome", midia.nome],
    ["Tipo", midia.tipo_midia?.nome ?? "-"],
    ["Status", <StatusBadge key="status" value={midia.status ?? (midia.ativo ? "ATIVA" : "DESATIVADA")} />],
    ["Descricao", midia.descricao || "-"],
    ["Aquisicao", formatDate(midia.data_aquisicao)],
    ["Inicio de uso", formatDate(midia.data_inicio_uso)],
    ["Validade", formatDate(midia.data_validade)],
    ["Ultima checagem", formatDateTime(midia.ultima_checagem_integridade)],
    ["Proxima checagem", formatDateTime(midia.proxima_checagem_integridade)],
    ["Capacidade total", formatBytes(midia.capacidade_total_bytes)],
    ["Capacidade utilizada", formatBytes(midia.capacidade_utilizada_bytes)],
    ["Identificador fisico", midia.identificador_fisico || "-"],
    ["Midia de origem", midia.midia_origem_id ? <Link key="origem" href={`/midias/${midia.midia_origem_id}`} className="text-primary hover:underline">{midia.midia_origem_id}</Link> : "-"],
    ["Data de desativacao", formatDateTime(midia.data_desativacao)],
    ["Motivo de desativacao", midia.motivo_desativacao || "-"],
    ["Posicao de armazenamento", midia.id_posicao_armazenamento ?? "-"],
    ["Criado em", formatDateTime(midia.criado_em)],
    ["Atualizado em", formatDateTime(midia.atualizado_em)],
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2">
      {fields.map(([label, value]) => (
        <div key={label} className="rounded-md border p-3">
          <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
          <div className="mt-1 text-sm">{value}</div>
        </div>
      ))}
    </section>
  );
}

function EventosMidiaTable({ data }: { data: EventoMidiaArmazenamento[] }) {
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Resultado</TableHead>
            <TableHead>Agente</TableHead>
            <TableHead>Detalhe</TableHead>
            <TableHead>PREMIS</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((evento) => (
              <TableRow key={evento.id}>
                <TableCell>{formatDateTime(evento.data_evento ?? evento.criado_em)}</TableCell>
                <TableCell>{evento.tipo_evento}</TableCell>
                <TableCell>
                  <StatusBadge value={evento.resultado} />
                </TableCell>
                <TableCell>{evento.agente || "-"}</TableCell>
                <TableCell className="max-w-md">{evento.detalhe || "-"}</TableCell>
                <TableCell>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="icon" title="Visualizar JSON PREMIS" aria-label="Visualizar JSON PREMIS">
                        <FileJson className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl">
                      <DialogHeader>
                        <DialogTitle>JSON PREMIS</DialogTitle>
                        <DialogDescription>Estrutura PREMIS registrada para o evento {evento.id}.</DialogDescription>
                      </DialogHeader>
                      <pre className="max-h-[60vh] overflow-auto rounded-md bg-muted p-3 text-xs">
                        {JSON.stringify(evento.premis_json ?? {}, null, 2)}
                      </pre>
                    </DialogContent>
                  </Dialog>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                Nenhum evento encontrado para esta midia.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function VerificacoesIntegridadePanel({
  midiaId,
  data,
  isLoading,
  error,
}: {
  midiaId: number;
  data: VerificacaoIntegridadeMidia[];
  isLoading: boolean;
  error?: string;
}) {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [manual, setManual] = useState({
    resultado: "SUCESSO" as ResultadoVerificacaoIntegridade,
    software_utilizado: "",
    versao_software: "",
    total_aips_verificados: "",
    total_sucesso: "",
    total_falha: "",
    total_alerta: "",
    observacoes: "",
  });
  const [importacao, setImportacao] = useState({
    ferramenta: "Thor Caixa de Ferramentas",
    versao: "",
    observacoes: "",
    relatorio: "",
  });

  const detalheQuery = useQuery({
    queryKey: ["midias", midiaId, "verificacoes-integridade", selectedId],
    queryFn: () => getVerificacaoIntegridadeMidia(midiaId, selectedId ?? ""),
    enabled: Boolean(selectedId),
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["midias", midiaId] }),
      queryClient.invalidateQueries({ queryKey: ["midias", midiaId, "eventos"] }),
      queryClient.invalidateQueries({ queryKey: ["midias", midiaId, "verificacoes-integridade"] }),
      queryClient.invalidateQueries({ queryKey: ["midias", "integridade"] }),
    ]);
  };

  const manualMutation = useMutation({
    mutationFn: () =>
      registrarVerificacaoIntegridadeManual(midiaId, {
        resultado: manual.resultado,
        software_utilizado: manual.software_utilizado || null,
        versao_software: manual.versao_software || null,
        total_aips_verificados: toNumber(manual.total_aips_verificados),
        total_sucesso: toNumber(manual.total_sucesso),
        total_falha: toNumber(manual.total_falha),
        total_alerta: toNumber(manual.total_alerta),
        observacoes: manual.observacoes || null,
        relatorio_json: { origem_registro: "manual" },
      }),
    onSuccess: async () => {
      setManual({
        resultado: "SUCESSO",
        software_utilizado: "",
        versao_software: "",
        total_aips_verificados: "",
        total_sucesso: "",
        total_falha: "",
        total_alerta: "",
        observacoes: "",
      });
      await invalidate();
    },
  });

  const importMutation = useMutation({
    mutationFn: () =>
      importarRelatorioVerificacaoIntegridade(midiaId, {
        ferramenta: importacao.ferramenta || null,
        versao: importacao.versao || null,
        observacoes: importacao.observacoes || null,
        relatorio_json: JSON.parse(importacao.relatorio) as Record<string, unknown>,
      }),
    onSuccess: async () => {
      setImportacao({
        ferramenta: "Thor Caixa de Ferramentas",
        versao: "",
        observacoes: "",
        relatorio: "",
      });
      await invalidate();
    },
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Registrar checagem manual</CardTitle>
          <CardDescription>Use quando o resultado veio de ferramenta externa e sera registrado diretamente.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Field label="Resultado">
              <select
                className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={manual.resultado}
                onChange={(event) => setManual((current) => ({ ...current, resultado: event.target.value as ResultadoVerificacaoIntegridade }))}
              >
                <option value="SUCESSO">SUCESSO</option>
                <option value="FALHA">FALHA</option>
                <option value="ALERTA">ALERTA</option>
                <option value="INCONCLUSIVO">INCONCLUSIVO</option>
              </select>
            </Field>
            <Field label="Software">
              <Input value={manual.software_utilizado} onChange={(event) => setManual((current) => ({ ...current, software_utilizado: event.target.value }))} />
            </Field>
            <Field label="Versao">
              <Input value={manual.versao_software} onChange={(event) => setManual((current) => ({ ...current, versao_software: event.target.value }))} />
            </Field>
            <Field label="AIPs verificados">
              <Input type="number" min={0} value={manual.total_aips_verificados} onChange={(event) => setManual((current) => ({ ...current, total_aips_verificados: event.target.value }))} />
            </Field>
            <Field label="Sucesso">
              <Input type="number" min={0} value={manual.total_sucesso} onChange={(event) => setManual((current) => ({ ...current, total_sucesso: event.target.value }))} />
            </Field>
            <Field label="Falha">
              <Input type="number" min={0} value={manual.total_falha} onChange={(event) => setManual((current) => ({ ...current, total_falha: event.target.value }))} />
            </Field>
            <Field label="Alerta">
              <Input type="number" min={0} value={manual.total_alerta} onChange={(event) => setManual((current) => ({ ...current, total_alerta: event.target.value }))} />
            </Field>
            <Field label="Observacoes">
              <Input value={manual.observacoes} onChange={(event) => setManual((current) => ({ ...current, observacoes: event.target.value }))} />
            </Field>
          </div>
          {manualMutation.error ? <p className="mt-3 text-sm text-destructive">{manualMutation.error.message}</p> : null}
          <Button type="button" className="mt-4" disabled={manualMutation.isPending} onClick={() => manualMutation.mutate()}>
            {manualMutation.isPending ? "Registrando..." : "Registrar checagem"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Importar relatorio de verificacao</CardTitle>
          <CardDescription>Relatorios JSON gerados por ferramentas homologadas, incluindo Thor Caixa de Ferramentas.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            <Field label="Ferramenta">
              <Input value={importacao.ferramenta} onChange={(event) => setImportacao((current) => ({ ...current, ferramenta: event.target.value }))} />
            </Field>
            <Field label="Versao">
              <Input value={importacao.versao} onChange={(event) => setImportacao((current) => ({ ...current, versao: event.target.value }))} />
            </Field>
            <Field label="Arquivo JSON">
              <Input
                type="file"
                accept="application/json,.json"
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    const relatorio = await file.text();
                    setImportacao((current) => ({ ...current, relatorio }));
                  }
                }}
              />
            </Field>
          </div>
          <Field label="Observacoes">
            <Input value={importacao.observacoes} onChange={(event) => setImportacao((current) => ({ ...current, observacoes: event.target.value }))} />
          </Field>
          <textarea
            className="min-h-40 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={importacao.relatorio}
            onChange={(event) => setImportacao((current) => ({ ...current, relatorio: event.target.value }))}
            placeholder='{"resultado_midia":"SUCESSO","total_aips_verificados":0,"falhas":[]}'
          />
          {importMutation.error ? <p className="text-sm text-destructive">{importMutation.error.message}</p> : null}
          <Button type="button" disabled={importMutation.isPending || !importacao.relatorio.trim()} onClick={() => importMutation.mutate()}>
            <Upload className="h-4 w-4" />
            {importMutation.isPending ? "Importando..." : "Confirmar importacao"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Relatorios anteriores</CardTitle>
          <CardDescription>{isLoading ? "Carregando..." : `${data.length} verificacoes registradas`}</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? <p className="text-sm text-destructive">{error}</p> : <VerificacoesTable data={data} onSelect={setSelectedId} />}
        </CardContent>
      </Card>

      {detalheQuery.data ? <VerificacaoDetalhe verificacao={detalheQuery.data} /> : null}
    </div>
  );
}

function VerificacoesTable({
  data,
  onSelect,
}: {
  data: VerificacaoIntegridadeMidia[];
  onSelect: (id: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Resultado</TableHead>
            <TableHead>Software</TableHead>
            <TableHead>AIPs</TableHead>
            <TableHead>Falhas</TableHead>
            <TableHead>Alertas</TableHead>
            <TableHead>Relatorio</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length ? (
            data.map((verificacao) => (
              <TableRow key={verificacao.id}>
                <TableCell>{formatDateTime(verificacao.data_fim ?? verificacao.data_inicio)}</TableCell>
                <TableCell>
                  <StatusBadge value={verificacao.resultado} />
                </TableCell>
                <TableCell>{verificacao.software_utilizado || "-"}</TableCell>
                <TableCell>{verificacao.total_aips_verificados}</TableCell>
                <TableCell>{verificacao.total_falha}</TableCell>
                <TableCell>{verificacao.total_alerta}</TableCell>
                <TableCell>
                  <Button type="button" variant="outline" size="sm" onClick={() => onSelect(verificacao.id)}>
                    Visualizar
                  </Button>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                Nenhuma verificacao registrada para esta midia.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function VerificacaoDetalhe({ verificacao }: { verificacao: VerificacaoIntegridadeMidia }) {
  const falhas = Array.isArray(verificacao.relatorio_json?.falhas) ? verificacao.relatorio_json.falhas : [];
  const alertas = Array.isArray(verificacao.relatorio_json?.alertas) ? verificacao.relatorio_json.alertas : [];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Detalhe da verificacao</CardTitle>
        <CardDescription>Falhas, alertas, relatorio JSON e eventos gerados nas unidades relacionadas.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Resultado" value={<StatusBadge value={verificacao.resultado} />} />
          <Metric label="AIPs" value={verificacao.total_aips_verificados} />
          <Metric label="Falhas" value={verificacao.total_falha} />
          <Metric label="Alertas" value={verificacao.total_alerta} />
        </div>
        <FalhasTable title="Falhas por AIP" data={falhas} />
        <FalhasTable title="Alertas por AIP" data={alertas} />
        <EventosUnidadesTable data={verificacao.eventos_unidades ?? []} />
        <pre className="max-h-96 overflow-auto rounded-md bg-muted p-3 text-xs">
          {JSON.stringify(verificacao.relatorio_json ?? {}, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}

function FalhasTable({ title, data }: { title: string; data: unknown[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>AIP</TableHead>
              <TableHead>Identificador</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Resultado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length ? (
              data.map((item, index) => {
                const row = item as Record<string, unknown>;
                return (
                  <TableRow key={`${row.aip_id ?? row.identificador ?? index}`}>
                    <TableCell>{String(row.aip_id ?? row.id_aip ?? "-")}</TableCell>
                    <TableCell>{String(row.identificador ?? row.codigo_aip ?? "-")}</TableCell>
                    <TableCell>{String(row.tipo_falha ?? row.tipo_alerta ?? row.tipo ?? "-")}</TableCell>
                    <TableCell>{String(row.resultado ?? "-")}</TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="h-16 text-center text-muted-foreground">
                  Nenhum registro.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function EventosUnidadesTable({ data }: { data: EventoPreservacao[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Eventos gerados nas unidades</h3>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Unidade</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Resultado</TableHead>
              <TableHead>Detalhe</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length ? (
              data.map((evento) => (
                <TableRow key={evento.id}>
                  <TableCell>
                    <Link href={`/unidades/${evento.id_unidade_acondicionamento}`} className="text-primary hover:underline">
                      {evento.id_unidade_acondicionamento}
                    </Link>
                  </TableCell>
                  <TableCell>{evento.tipo_evento}</TableCell>
                  <TableCell>
                    <StatusBadge value={evento.resultado} />
                  </TableCell>
                  <TableCell>{evento.detalhe || "-"}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="h-16 text-center text-muted-foreground">
                  Nenhum evento de unidade relacionado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}

function toNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(value));
}

function formatBytes(value?: number | null) {
  if (value === undefined || value === null) return "-";
  return new Intl.NumberFormat("pt-BR").format(value);
}
