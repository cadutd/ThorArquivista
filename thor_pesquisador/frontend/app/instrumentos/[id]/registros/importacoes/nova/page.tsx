"use client";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { NovaImportacao } from "@/components/importacao-envio";

export default function NovaImportacaoPage() {
  const { id } = useParams<{ id: string }>();
  return <AppShell><NovaImportacao key={id} instrumentoId={id}/></AppShell>;
}
