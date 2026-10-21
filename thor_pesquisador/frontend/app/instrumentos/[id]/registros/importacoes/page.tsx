"use client";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ImportacoesLista } from "@/components/importacoes-lista";

export default function ImportacoesPage() {
  const { id } = useParams<{ id: string }>();
  return <AppShell><ImportacoesLista key={id} instrumentoId={id}/></AppShell>;
}
