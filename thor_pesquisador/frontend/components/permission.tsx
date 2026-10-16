"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { request } from "@/lib/api";
type Access = { permissoes: string[]; escopos: Record<string, string[]>; ready:boolean; error:string };
const Context = createContext<Access>({ permissoes: [], escopos: {}, ready:false, error:"" });
export function PermissionProvider({ children }: { children: React.ReactNode }) {
  const [access, setAccess] = useState<Access>({ permissoes: [], escopos: {}, ready:false, error:"" });
  useEffect(() => {
    let current = true;
    request<Access>("/auth/permissoes").then(a => { if(current) setAccess({...a,ready:true,error:""}); }).catch(e => {if(current) setAccess({permissoes:[],escopos:{},ready:true,error:e.message});});
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

export function AnyPermission({acoes,anyScope=false,children}:{acoes:string[];anyScope?:boolean;children:React.ReactNode}) {
  const access = useContext(Context);
  return access.permissoes.includes("*") || acoes.some(a => access.permissoes.includes(a) ||
    (anyScope && Object.values(access.escopos).some(p => p.includes(a)))) ? <>{children}</> : null;
}

export function AccessBoundary({children,publico=false}:{children:React.ReactNode;publico?:boolean}) {
  const access = useContext(Context);
  if(publico) return <>{children}</>;
  if(!access.ready) return <p role="status">Carregando...</p>;
  if(access.error) return <p className="error" role="alert">{access.error}</p>;
  if(!access.permissoes.length && !Object.values(access.escopos).some(p => p.length))
    return <section className="stack"><h1>Acesso nao concedido</h1>
      <p role="status">Sua conta esta ativa, mas ainda nao possui permissoes de acesso.</p></section>;
  return <>{children}</>;
}
