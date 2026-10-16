export type Audit = {id:string;fonte:string;acao:string;entidade:string;entidade_id:string|null;instrumento_id:string|null;
  registro_id:string|null;agente:string;usuario_id:string|null;request_id:string|null;operacao_id:string|null;
  criado_em:string;detalhe:Record<string,unknown>};
export type ExportJob = {id:string;agente:string;instrumento_id:string;formato:string;escopo:string;status:string;
  processados:number;tentativa:number;expira_em:string;criado_em:string;atualizado_em:string;erro:string|null;checksum:string|null;tamanho_bytes:number|null};
export type Policy = {id:string;nome:string;categoria:string;dias:number;instrumento_id:string|null;instrumento_nome?:string|null;ativo:boolean;permitir_expurgo:boolean;bloqueada:boolean};
export type RetentionJob = {id:string;politica_id:string;instrumento_id:string|null;status:string;simulacao:boolean;agente:string;processados:number;
  elegiveis:number;bloqueados:number;removidos:number;erro:string|null;criado_em:string};
export const categories:Record<string,string> = {LOG_TECNICO:"Logs tecnicos",ACESSO_CONSULTIVO:"Acessos consultivos",
  EXPORTACAO:"Arquivos de exportacao",SESSAO:"Sessoes expiradas",REGISTRO_EXCLUIDO:"Registros excluidos"};
export const states:Record<string,string> = {PENDENTE:"Pendente",PROCESSANDO:"Processando",CONCLUIDA:"Concluida",
  FALHOU:"Falhou",CANCELADA:"Cancelada",EXPIRADA:"Expirada",DESCARTADA:"Descartada"};
export const date = (v:string) => new Date(v).toLocaleString("pt-BR");
