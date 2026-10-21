"use client";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ImportacaoDetalhe } from "@/components/importacao-detalhe";

export default function ImportacaoPage() {
  const { id, jobId } = useParams<{ id: string; jobId: string }>();
  return <AppShell><ImportacaoDetalhe key={id + ":" + jobId} instrumentoId={id} jobId={jobId}/></AppShell>;
}
