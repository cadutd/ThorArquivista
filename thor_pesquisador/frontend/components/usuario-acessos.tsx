"use client";
import { AdministracaoList } from "./administracao-list";
import { UsuarioEditor } from "./usuario-editor";

export function UsuarioAcessos({id,readonly=false}:{id:string;readonly?:boolean}) {
  return readonly ? <AdministracaoList tipo="usuarios" usuarioInicial={id}/> : <UsuarioEditor id={id}/>;
}
