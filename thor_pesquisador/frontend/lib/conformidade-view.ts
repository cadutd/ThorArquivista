import { Audit,ExportJob,Policy,RetentionJob,categories,date,states } from "./conformidade";

export type Kind="auditoria"|"exportacoes"|"politicas"|"execucoes";
export type Row=Audit|ExportJob|Policy|RetentionJob;
export const config={
  auditoria:{title:"Auditoria",path:"/auditoria",permission:"auditoria_consultar",columns:[["criado_em","Data"],["acao","Acao"],["entidade","Entidade"],["agente","Usuario"],["fonte","Origem"]]},
  exportacoes:{title:"Exportacoes",path:"/exportacoes",permission:"exportacoes_consultar",columns:[["criado_em","Solicitacao"],["formato","Formato"],["escopo","Escopo"],["status","Situacao"],["processados","Registros"],["agente","Solicitante"]]},
  politicas:{title:"Politicas de retencao",path:"/retencao/politicas",permission:"retencao_consultar",columns:[["nome","Nome"],["categoria","Categoria"],["dias","Prazo (dias)"],["ativo","Situacao"],["bloqueada","Bloqueada"]]},
  execucoes:{title:"Execucoes de retencao",path:"/retencao/execucoes",permission:"retencao_consultar",columns:[["criado_em","Solicitacao"],["simulacao","Modo"],["status","Situacao"],["processados","Analisados"],["elegiveis","Elegiveis"],["bloqueados","Bloqueados"],["removidos","Removidos"]]},
} as const;

export function display(key:string,value:unknown) {
  if(value==null) return "-";
  if(["criado_em","atualizado_em","expira_em","corte_em"].includes(key)) return date(String(value));
  if(key==="categoria") return categories[String(value)]||String(value);
  if(key==="status") return states[String(value)]||String(value);
  if(key==="ativo") return value?"Ativo":"Inativo";
  if(key==="simulacao") return value?"Simulacao":"Execucao";
  if(typeof value==="boolean") return value?"Sim":"Nao";
  return typeof value==="object"?JSON.stringify(value,null,2):String(value);
}


export function detailPath(tipo:Kind,row:Row) {
  return config[tipo].path+"/"+("fonte" in row?encodeURIComponent(row.fonte)+"/":"")+encodeURIComponent(row.id);
}
