"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { request } from "@/lib/api";
type Access = { permissoes: string[]; escopos: Record<string, string[]> };
const Context = createContext<Access>({ permissoes: [], escopos: {} });
export function PermissionProvider({ children }: { children: React.ReactNode }) {
  const [access, setAccess] = useState<Access>({ permissoes: [], escopos: {} });
  useEffect(() => {
    let current = true;
    request<Access>("/auth/permissoes").then(a => { if(current) setAccess(a); }).catch(() => {});
    return () => { current = false; };
  }, []);
  return <Context.Provider value={access}>{children}</Context.Provider>;
}
export function usePermission(acao: string, instrumentoId?: string, anyScope = false) {
  const access = useContext(Context);
  const permissions = [...access.permissoes, ...(instrumentoId ? access.escopos[instrumentoId] || [] : [])];
  return permissions.includes("*") || permissions.includes(acao) ||
    (anyScope && Object.values(access.escopos).some(p => p.includes(acao)));
}
export function Permission({ acao, instrumentoId, anyScope, children }: {
  acao: string; instrumentoId?: string; anyScope?: boolean; children: React.ReactNode;
}) {
  return usePermission(acao, instrumentoId, anyScope) ? <>{children}</> : null;
}

export function ImagePermission({ owner, acao="imagens_editar", children }: { owner: boolean; acao?: string; children: React.ReactNode }) {
  const admin = usePermission("*");
  const manage = usePermission(acao, undefined, true);
  return admin || (owner && manage) ? <>{children}</> : null;
}

export function AnyPermission({acoes,children}:{acoes:string[];children:React.ReactNode}) {
  const access = useContext(Context);
  return access.permissoes.includes("*") || acoes.some(a => access.permissoes.includes(a)) ? <>{children}</> : null;
}
