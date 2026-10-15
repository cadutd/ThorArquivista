"use client";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { AccessList } from "@/components/access-list";
export default function ViewAccess() {
  const {id} = useParams<{id:string}>();
  return <AppShell><Permission acao="acessos_consultar"><AccessList acessoInicial={id}/></Permission></AppShell>;
}
