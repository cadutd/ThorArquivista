"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { AccessList } from "./access-list";
import { request } from "@/lib/api";

export function UsuarioEscopos({id}:{id:string}) {
  const [user,setUser] = useState<{id:string;nome:string}>();
  const [error,setError] = useState("");
  useEffect(() => {
    let current = true;
    request<{id:string;nome:string}>("/usuarios/" + id).then(u => {if(current) setUser(u);})
      .catch(e => {if(current) setError(e.message);});
    return () => {current = false;};
  },[id]);
  return <AppShell><Permission acao={"acessos_consultar"}><div className="stack administracao-page">
    <div className="row"><div><h1>Perfis e escopos</h1>{user && <p className="muted">{user.nome}</p>}</div>
      <Link className="button secondary" href={"/usuarios/" + id + "/editar"}><ArrowLeft size={16}/>Voltar</Link></div>
    {error && <p className="error" role="alert">{error}</p>}
    {!user && !error && <p role="status">Carregando...</p>}
    {user && <AccessList usuarioId={user.id}/>}
  </div></Permission></AppShell>;
}
