"use client";
import { AppShell } from "@/components/app-shell";
import { Permission } from "@/components/permission";
import { AccessList } from "@/components/access-list";
export default function AccessPage() {
  return <AppShell><Permission acao={"acessos_consultar"}><AccessList/></Permission></AppShell>;
}
