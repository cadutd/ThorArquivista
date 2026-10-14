"use client";
import { Permission } from "./permission";
import Link from "next/link";
import { useEffect,useState } from "react";
import { Edit,Trash2 } from "lucide-react";
import { request } from "@/lib/api";
import { AdministracaoDetails } from "./administracao-details";
import type { Perfil } from "./perfil-editor";

export function PerfilPopup({codigo,onClose,onDeleted}:{
  codigo:string;onClose:()=>void;onDeleted:()=>void;
}) {
  const [data,setData] = useState<Perfil>();
  const [error,setError] = useState("");
  const [deleting,setDeleting] = useState(false);
  useEffect(() => {
    let current = true;
    request<Perfil>("/perfis/" + encodeURIComponent(codigo)).then(p => {if(current) setData(p);})
      .catch(e => {if(current) setError(e.message);});
    return () => {current = false;};
  },[codigo]);
  async function remove() {
    if(!window.confirm("Excluir este perfil? Perfis vinculados ou padrao serao desativados.")) return;
    setDeleting(true);setError("");
    try {await request("/perfis/" + encodeURIComponent(codigo),{method:"DELETE"});onDeleted();}
    catch(e) {setError(e instanceof Error ? e.message : "Falha ao excluir perfil.");}
    finally {setDeleting(false);}
  }
  return <AdministracaoDetails title="Perfil" onClose={onClose} loading={!data && !error} error={error}
    fields={data ? [["Nome",data.nome],["Codigo",data.codigo],["Ativo",data.ativo ? "Sim" : "Nao"],
      ["Sistema",data.sistema ? "Sim" : "Nao"]] : []} description={data?.descricao}
    actions={data && codigo !== "ADMIN" ? <>
      <Permission acao="perfis_editar"><Link className="button secondary" title="Editar perfil" href={"/perfis/" + encodeURIComponent(codigo) + "/editar"}>
        <Edit size={16}/>Editar</Link></Permission>
      <Permission acao="perfis_excluir"><button className="button administracao-delete" title="Excluir perfil" disabled={deleting} onClick={remove}>
        <Trash2 size={16}/>{deleting ? "Excluindo..." : "Excluir"}</button></Permission>
    </> : undefined}>
    {data && <section className="administracao-permissions"><h3>Permissoes</h3>
      {data.permissoes.length ? <div className="administracao-permission-tags">{data.permissoes.map(p =>
        <span className="administracao-permission-tag" key={p}>{p}</span>)}</div> : <p className="muted">-</p>}
    </section>}
  </AdministracaoDetails>;
}
