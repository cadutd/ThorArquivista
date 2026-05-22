"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Edit, Printer, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { StatusBadge } from "@/components/status-badge";
import { StorageBreadcrumb, StorageLocationPath, StorageStatusBadge } from "@/features/armazenamento/storage-components";
import { storageLabel } from "@/features/armazenamento/storage-labels";
import { listarModelosFichaEspelho } from "@/lib/api/ficha-espelho";
import { deleteUnidade, getUnidade } from "@/lib/api/domain";
import { obterPosicao } from "@/lib/api/storage-addressing";
import type { CopiaDigital, UnidadeAcondicionamento } from "@/types/domain";
import type { PosicaoArmazenamento } from "@/types/storage";

const FICHA_ESPELHO_DIGITAL_BLOCK_MESSAGE = "Apenas unidades que não são digitais podem ter ficha espelho impressa.";

type Props = {
  unidadeId: number;
};

export function UnidadeViewPage({ unidadeId }: Props) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [printDialogOpen, setPrintDialogOpen] = useState(false);
  const query = useQuery({
    queryKey: ["unidades", unidadeId],
    queryFn: () => getUnidade(unidadeId),
    enabled: Number.isFinite(unidadeId),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUnidade,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["unidades"] });
      router.push("/unidades");
    },
  });

  const unidade = query.data;
  const printable = unidade ? canPrintFichaEspelho(unidade) : false;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Visualizar unidade</h1>
          <p className="text-sm text-muted-foreground">
            Consulta completa dos metadados da unidade de acondicionamento.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link href="/unidades">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
          {unidade ? (
            <>
              <Button
                type="button"
                variant="outline"
                disabled={!printable}
                title={printable ? undefined : FICHA_ESPELHO_DIGITAL_BLOCK_MESSAGE}
                onClick={() => setPrintDialogOpen(true)}
              >
                <Printer className="h-4 w-4" />
                Ficha espelho
              </Button>
              <Button asChild variant="outline">
                <Link href={`/unidades/${unidade.id}/editar`}>
                  <Edit className="h-4 w-4" />
                  Editar
                </Link>
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={deleteMutation.isPending}
                onClick={() => {
                  if (window.confirm("Excluir esta unidade de acondicionamento?")) {
                    deleteMutation.mutate(unidade.id);
                  }
                }}
              >
                <Trash2 className="h-4 w-4" />
                {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
              </Button>
            </>
          ) : null}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{unidade?.identificador ?? "Metadados da unidade"}</CardTitle>
          <CardDescription>
            {query.isLoading
              ? "Carregando dados da unidade."
              : unidade
                ? unidade.titulo
                : "Unidade não encontrada."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando unidade...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : unidade ? (
            <UnidadeDetails unidade={unidade} />
          ) : (
            <p className="text-sm text-muted-foreground">Unidade não encontrada.</p>
          )}
          {deleteMutation.error ? <p className="mt-4 text-sm text-destructive">{deleteMutation.error.message}</p> : null}
        </CardContent>
      </Card>

      {unidade ? (
        <PrintDialog
          open={printDialogOpen}
          unidadeId={unidade.id}
          onOpenChange={setPrintDialogOpen}
        />
      ) : null}
    </div>
  );
}

function UnidadeDetails({ unidade }: { unidade: UnidadeAcondicionamento }) {
  const posicao = useQuery({
    queryKey: ["posicoes-armazenamento", unidade.id_posicao_armazenamento],
    queryFn: () => obterPosicao(unidade.id_posicao_armazenamento as number),
    enabled: Boolean(unidade.id_posicao_armazenamento),
  });
  const fields: Array<[string, React.ReactNode]> = [
    ["ID", unidade.id],
    ["Identificador", unidade.identificador],
    ["Título", unidade.titulo],
    ["Descrição", unidade.descricao || "-"],
    ["Produtor", unidade.produtor || "-"],
    ["Unidade", unidade.unidade || "-"],
    ["Data-limite", unidade.data_limite || "-"],
    ["Código de classificação", unidade.codigo_classificacao || "-"],
    ["Assunto", unidade.assunto || "-"],
    ["Código de barra", unidade.codigo_barra || "-"],
    ["Informações do pacote", unidade.informacoes_pacote || "-"],
    ["Suporte", <StatusBadge key="suporte" value={unidade.tipo_suporte} />],
    ["Tipo", unidade.tipo_unidade],
    ["Nível de acesso", <StatusBadge key="acesso" value={unidade.nivel_acesso} />],
    ["Status", <StatusBadge key="status" value={unidade.status} />],
    ["Unidade pai", unidade.id_unidade_pai ?? "-"],
    ["Representa", unidade.id_representa ?? "-"],
    ["Criado em", formatDateTime(unidade.criado_em)],
    ["Atualizado em", formatDateTime(unidade.atualizado_em)],
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-md border p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
            <div className="mt-1 text-sm">{value}</div>
          </div>
        ))}
      </section>

      <StoragePositionSection
        idPosicao={unidade.id_posicao_armazenamento}
        isLoading={posicao.isLoading}
        error={posicao.error}
        posicao={posicao.data}
      />

      <section className="space-y-3">
        <h2 className="text-base font-semibold tracking-normal">Metadados digitais</h2>
        {unidade.digital ? (
          <div className="grid gap-3 md:grid-cols-2">
            <DetailCard label="Tamanho" value={unidade.digital.tamanho_bytes ?? "-"} />
            <DetailCard label="Status de fixidez" value={unidade.digital.status_fixidez ?? "-"} />
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhum metadado digital registrado.</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold tracking-normal">Cópias digitais</h2>
        {unidade.copias_digitais?.length ? (
          <div className="space-y-2">
            {unidade.copias_digitais.map((copia) => (
              <CopiaDetails key={copia.id} copia={copia} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma cópia digital vinculada.</p>
        )}
      </section>
    </div>
  );
}

function StoragePositionSection({
  idPosicao,
  isLoading,
  error,
  posicao,
}: {
  idPosicao?: number | null;
  isLoading: boolean;
  error: Error | null;
  posicao?: PosicaoArmazenamento;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-base font-semibold tracking-normal">Posição de armazenamento</h2>
      {!idPosicao ? (
        <p className="text-sm text-muted-foreground">Sem posição de armazenamento atribuída.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando posição de armazenamento...</p>
      ) : error ? (
        <p className="text-sm text-destructive">{error.message}</p>
      ) : posicao ? (
        <div className="space-y-3 rounded-md border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <StorageLocationPath posicao={posicao} />
            <StorageStatusBadge ativo={posicao.ativo} ocupada={posicao.ocupada} />
          </div>
          <StorageBreadcrumb posicao={posicao} />
          <div className="grid gap-3 md:grid-cols-3">
            <DetailCard label="Código" value={posicao.codigo_completo} />
            <DetailCard label="Tipo de posição" value={storageLabel(posicao.tipo_posicao)} />
            <DetailCard label="Capacidade" value={posicao.capacidade_unidades} />
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Posição de armazenamento não encontrada.</p>
      )}
    </section>
  );
}

function PrintDialog({
  open,
  unidadeId,
  onOpenChange,
}: {
  open: boolean;
  unidadeId: number;
  onOpenChange: (open: boolean) => void;
}) {
  const [modeloId, setModeloId] = useState("");
  const modelos = useQuery({
    queryKey: ["fichas-espelho", "modelos", "ativos"],
    queryFn: () => listarModelosFichaEspelho({ ativo: true }),
    enabled: open,
  });
  const selectedModeloId = modeloId || (modelos.data?.items[0] ? String(modelos.data.items[0].id) : "");

  const print = () => {
    if (!selectedModeloId) {
      return;
    }
    const params = new URLSearchParams({
      modeloId: selectedModeloId,
      unidadeIds: String(unidadeId),
    });
    window.open(`/fichas-espelho/imprimir?${params.toString()}`, "_blank", "noopener,noreferrer");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Gerar ficha espelho</DialogTitle>
          <DialogDescription>Escolha o modelo para imprimir esta unidade.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Modelo</Label>
            <select
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              value={selectedModeloId}
              onChange={(event) => setModeloId(event.target.value)}
            >
              <option value="">Selecione</option>
              {(modelos.data?.items ?? []).map((modelo) => (
                <option key={modelo.id} value={modelo.id}>
                  {modelo.nome}
                </option>
              ))}
            </select>
          </div>
          {modelos.error ? <p className="text-sm text-destructive">{modelos.error.message}</p> : null}
          {!modelos.isLoading && !modelos.data?.items.length ? (
            <p className="text-sm text-muted-foreground">Cadastre um modelo ativo em Administração.</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="button" disabled={!selectedModeloId} onClick={print}>
              <Printer className="h-4 w-4" />
              Gerar para impressão
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function CopiaDetails({ copia }: { copia: CopiaDigital }) {
  return (
    <div className="grid gap-2 rounded-md border p-3 text-sm md:grid-cols-2">
      <DetailLine label="Mídia" value={copia.id_midia_armazenamento} />
      <DetailLine label="URI" value={copia.uri_copia} />
      <DetailLine label="Função" value={copia.funcao_copia} />
      <DetailLine label="Status" value={copia.status_copia} />
      <DetailLine label="Algoritmo" value={copia.algoritmo_fixidez ?? "-"} />
      <DetailLine label="Hash" value={copia.hash_fixidez ?? "-"} />
      <DetailLine label="Última verificação" value={formatDateTime(copia.ultima_verificacao_em)} />
      <DetailLine label="Criada em" value={formatDateTime(copia.criada_em)} />
    </div>
  );
}

function DetailCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <div className="mt-1 text-sm">{value}</div>
    </div>
  );
}

function DetailLine({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <span className="text-muted-foreground">{label}: </span>
      <span>{value}</span>
    </div>
  );
}

function canPrintFichaEspelho(unidade: UnidadeAcondicionamento) {
  return unidade.tipo_suporte !== "DIGITAL";
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}
