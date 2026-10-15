"use client";
import { AcessoCadastro } from "./acesso-cadastro";

export type Acesso = {
  id:string;usuario_id:string;nome:string;username?:string|null;papel:string;perfil_nome?:string;
  instrumento_id:string|null;instrumento_nome?:string;criado_em?:string;
};

export function AcessoEditor({id,usuarioId}:{id?:string;usuarioId?:string}) {
  return <AcessoCadastro id={id} usuarioId={usuarioId}/>;
}
