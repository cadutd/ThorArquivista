"use client";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ImportacaoRegistros } from "@/components/importacao-registros";

export default function ImportarRegistrosPage() {
  const { id } = useParams<{ id: string }>();
  return <AppShell><ImportacaoRegistros key={id} instrumentoId={id}/></AppShell>;
}
