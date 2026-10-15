"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { Edit,Trash2 } from "lucide-react";
import { AdministracaoDetails } from "./administracao-details";
import { Permission } from "./permission";
import { me,request } from "@/lib/api";
import type { Acesso } from "./acesso-editor";

export function AcessoPopup({id,usuarioId,readonly=false,onClose,onDeleted}:{
  id:string;usuarioId?:string;readonly?:boolean;onClose:()=>void;onDeleted:()=>void;
}) {
  const [data,setData] = useState<Acesso>();
  const [error,setError] = useState("");
  const [deleting,setDeleting] = useState(false);
  const [actorId,setActorId] = useState<string>();
  useEffect(() => {
    let current = true;
    request<Acesso>("/acessos/" + id).then(value => {if(current) setData(value);})
      .catch(e => {if(current) setError(e.message);});
    me().then(value => {if(current) setActorId(value.id);}).catch(() => {});
    return () => {current = false;};
  },[id]);
  async function remove() {
    if(!window.confirm("Revogar esta concessao de acesso de " + data?.nome + "?")) return;
    setDeleting(true);setError("");
    try {await request("/acessos/" + id,{method:"DELETE"});onDeleted();}
    catch(e) {setError(e instanceof Error ? e.message : "Falha ao revogar acesso.");}
    finally {setDeleting(false);}
  }
  const selfAdmin = !actorId || (data?.usuario_id === actorId && data?.papel === "ADMIN");
  const edit = "/acessos/" + id + "/editar" + (usuarioId ? "?usuario=" + usuarioId : "");
  return <AdministracaoDetails title="Concessao de acesso" onClose={onClose} loading={!data && !error} error={error}
    fields={data ? [["Usuario",data.nome],["Perfil",data.perfil_nome || data.papel],
      ["Codigo do perfil",data.papel],["Escopo",data.instrumento_id ? "Por instrumento" : "Global"],
      ["Instrumento",data.instrumento_id ? data.instrumento_nome || "-" : "Todos"],
      ["Concedido em",data.criado_em ? new Date(data.criado_em).toLocaleString("pt-BR") : "-"]] : []}
    actions={data && !readonly ? <>
      <Permission acao="acessos_editar"><Link className="button secondary" title="Editar acesso" href={edit}>
        <Edit size={16}/>Editar</Link></Permission>
      {!selfAdmin && <Permission acao="acessos_excluir"><button className="button administracao-delete"
        title="Revogar acesso" disabled={deleting} onClick={remove}><Trash2 size={16}/>
        {deleting ? "Revogando..." : "Revogar acesso"}</button></Permission>}
    </> : undefined}/>;
}
