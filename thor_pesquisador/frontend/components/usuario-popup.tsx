"use client";
import { Permission } from "./permission";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Edit, Trash2, X } from "lucide-react";
import { ModalFrame } from "./modal-frame";
import type { Usuario } from "./usuario-editor";
import { me, request } from "@/lib/api";

export function UsuarioPopup({id,onClose,onDeleted}:{id:string;onClose:()=>void;onDeleted:()=>void}) {
  const [user,setUser] = useState<Usuario>();
  const [self,setSelf] = useState(true);
  const [error,setError] = useState("");
  const [deleting,setDeleting] = useState(false);
  useEffect(() => {
    let current = true;
    request<Usuario>("/usuarios/" + id).then(u => {if(current) setUser(u);})
      .catch(e => {if(current) setError(e.message);});
    me().then(u => {if(current) setSelf(u.id === id);}).catch(() => {});
    return () => {current = false;};
  }, [id]);
  async function remove() {
    if(!window.confirm("Excluir o usuario " + user?.nome + "?")) return;
    setDeleting(true);setError("");
    try {await request("/usuarios/" + id,{method:"DELETE"});onDeleted();}
    catch(e) {setError(e instanceof Error ? e.message : "Falha ao excluir usuario.");}
    finally {setDeleting(false);}
  }
  const fields = user ? [
    ["Nome",user.nome],["Usuario",user.username],["E-mail",user.email],
    ["Perfil",user.perfil_nome || user.perfil_codigo],["Ativo",user.ativo ? "Sim" : "Nao"],
    ["CPF",user.cpf],["Vinculo gov.br",user.govbr_vinculado ? "Vinculado" : "Nao vinculado"],
    ["Criado em",new Date(user.criado_em).toLocaleString("pt-BR")],
    ["Atualizado em",new Date(user.atualizado_em).toLocaleString("pt-BR")],
  ] : [];
  return <ModalFrame title="Visualizar usuario" onClose={onClose} className="usuario-popup">
    <div className="row usuario-popup-header"><h2>Usuario</h2><button autoFocus className="usuario-popup-close" title="Fechar"
      aria-label="Fechar" onClick={onClose}><X size={16}/></button></div>
    {error && <p className="error" role="alert">{error}</p>}
    {!user && !error && <p role="status">Carregando...</p>}
    {user && <><dl className="usuario-details">{fields.map(([label,value]) =>
      <div className="detail-item" key={label}><dt>{label}</dt><dd>{value || "-"}</dd></div>)}</dl>
      {user.observacoes && <section className="usuario-observacoes"><h3>Observacoes</h3><p>{user.observacoes}</p></section>}
      <div className="actions usuario-popup-actions"><Permission acao="usuarios_editar"><Link className="button secondary" title="Editar usuario" href={"/usuarios/" + id + "/editar"}><Edit size={16}/>Editar</Link></Permission>
        {!self && <Permission acao="usuarios_excluir"><button className="button usuario-delete" title="Excluir usuario" disabled={deleting} onClick={remove}>
          <Trash2 size={16}/>{deleting ? "Excluindo..." : "Excluir"}</button></Permission>}</div></>}
  </ModalFrame>;
}
