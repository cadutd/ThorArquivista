"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Save } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  alterarStatusSessaoSubmissao,
  getSessaoSubmissao,
  listAcordosAdmissao,
  type SessaoStatusPayload,
  type StatusSessaoSubmissao,
} from "@/lib/api/admissao";

const TRANSICOES: Record<StatusSessaoSubmissao, StatusSessaoSubmissao[]> = {
  INICIADA: ["EM_TRANSFERENCIA", "CANCELADA"],
  EM_TRANSFERENCIA: ["RECEBIDA", "CANCELADA"],
  RECEBIDA: ["EM_QUARENTENA", "CANCELADA"],
  EM_QUARENTENA: ["EM_VALIDACAO", "CANCELADA"],
  EM_VALIDACAO: ["VALIDADA", "REJEITADA", "CANCELADA"],
  VALIDADA: ["NORMALIZANDO", "CANCELADA"],
  REJEITADA: ["FINALIZADA", "CANCELADA"],
  NORMALIZANDO: ["NORMALIZADA", "CANCELADA"],
  NORMALIZADA: ["FINALIZADA", "CANCELADA"],
  FINALIZADA: [],
  CANCELADA: [],
};

export function SessaoStatusPage({ id }: { id: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const sessao = useQuery({ queryKey: ["admissao", "sessoes", id], queryFn: () => getSessaoSubmissao(id) });
  const acordos = useQuery({
    queryKey: ["admissao", "acordos", sessao.data?.id_processo_admissao],
    queryFn: () => listAcordosAdmissao(sessao.data?.id_processo_admissao ?? ""),
    enabled: Boolean(sessao.data?.id_processo_admissao),
  });
  const [status, setStatus] = useState<StatusSessaoSubmissao | "">("");
  const [volumeRecebido, setVolumeRecebido] = useState("");
  const [resultadoValidacao, setResultadoValidacao] = useState("");
  const proximos = useMemo(() => (sessao.data ? TRANSICOES[sessao.data.status] : []), [sessao.data]);
  const acordo = acordos.data?.find((item) => item.id === sessao.data?.id_acordo_utilizado);

  useEffect(() => {
    setStatus(proximos[0] ?? "");
  }, [proximos]);

  const mutation = useMutation({
    mutationFn: (payload: SessaoStatusPayload) => alterarStatusSessaoSubmissao(id, payload),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ["admissao"] });
      router.push(`/admissao/${updated.id_processo_admissao}`);
    },
  });

  if (sessao.isLoading) return <p className="rounded-md border p-4 text-sm text-muted-foreground">Carregando sessão...</p>;
  if (sessao.error) return <p className="rounded-md border p-4 text-sm text-destructive">{sessao.error.message}</p>;
  if (!sessao.data) return null;

  const requiresVolume = status === "RECEBIDA";
  const requiresResultado = status === "VALIDADA" || status === "REJEITADA";
  const canSubmit = Boolean(status) && (!requiresVolume || volumeRecebido.trim()) && (!requiresResultado || resultadoValidacao.trim());

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!status) return;
    mutation.mutate({
      status,
      volume_recebido: requiresVolume ? volumeRecebido.trim() : undefined,
      resultado_validacao: requiresResultado ? resultadoValidacao.trim() : undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Alterar status da sessão</h1>
          <p className="text-sm text-muted-foreground">{sessao.data.titulo}</p>
        </div>
        <Button asChild variant="outline"><Link href={`/admissao/${sessao.data.id_processo_admissao}`}><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
      </div>

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <Detail label="Sessão" value={sessao.data.numero_sessao} />
        <Detail label="Status atual" value={label(sessao.data.status)} />
        <Detail label="Acordo de admissão" value={acordo ? `Versão ${acordo.numero_versao} - ${acordo.titulo}` : sessao.data.id_acordo_utilizado} />
        <Detail label="Canal" value={label(sessao.data.canal_submissao)} />
        <Detail label="Volume informado" value={sessao.data.volume_informado} />
        <Detail label="Volume recebido" value={sessao.data.volume_recebido} />
      </div>

      {proximos.length ? (
        <form className="grid gap-3 rounded-md border p-4 md:grid-cols-2" onSubmit={submit}>
          <Field label="Novo status">
            <select required className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={status} onChange={(event) => setStatus(event.target.value as StatusSessaoSubmissao)}>
              {proximos.map((value) => <option key={value} value={value}>{label(value)}</option>)}
            </select>
          </Field>
          {requiresVolume ? <Field label="Volume recebido"><Input required value={volumeRecebido} onChange={(event) => setVolumeRecebido(event.target.value)} /></Field> : null}
          {requiresResultado ? <div className="md:col-span-2"><Field label="Resultado da validação"><textarea required className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm" value={resultadoValidacao} onChange={(event) => setResultadoValidacao(event.target.value)} /></Field></div> : null}
          <div className="flex gap-2 md:col-span-2">
            <Button type="submit" disabled={mutation.isPending || !canSubmit}><Save className="h-4 w-4" />{mutation.isPending ? "Salvando..." : "Salvar status"}</Button>
            <Button asChild type="button" variant="outline"><Link href={`/admissao/${sessao.data.id_processo_admissao}`}>Cancelar</Link></Button>
          </div>
          {mutation.error ? <p className="text-sm text-destructive md:col-span-2">{mutation.error.message}</p> : null}
        </form>
      ) : (
        <p className="rounded-md border p-4 text-sm text-muted-foreground">Esta sessão não possui transições de status disponíveis.</p>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value?: React.ReactNode }) {
  return <div className="rounded-md border p-3"><p className="text-xs font-medium uppercase text-muted-foreground">{label}</p><div className="mt-1 break-words text-sm">{value || "-"}</div></div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}

function label(value?: string | null) {
  return value ? value.replaceAll("_", " ") : "-";
}
