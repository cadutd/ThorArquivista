import type { CSSProperties } from "react";

export type Colors={primaria:string;secundaria:string;destaque:string;fundo:string;texto:string};
export type PortalConfig={nome_instituicao:string;cores:Colors;versao:number};
export type PortalState={autenticado:boolean;nome?:string;visitante?:boolean;area_interna?:boolean;destino_interno?:string};
export type CatalogItem={id:string;nome:string;tipo:string;descricao?:string|null;imagem_card_url?:string|null};
export const defaults:PortalConfig={nome_instituicao:"Thor Pesquisador",versao:1,cores:{
  primaria:"#0e6496",secundaria:"#235347",destaque:"#8f2453",fundo:"#ffffff",texto:"#17232d"}};
export const types:Record<string,string>={GUIA:"Guia",INVENTARIO:"Inventario",CATALOGO:"Catalogo",INDICE:"Indice",BASE_TEMATICA:"Base tematica",OUTRO:"Outro"};
export const presets:Record<string,Colors>={
  Institucional:defaults.cores,
  Floresta:{primaria:"#246044",secundaria:"#344b63",destaque:"#883550",fundo:"#ffffff",texto:"#17232d"},
  Vinho:{primaria:"#842c4b",secundaria:"#345b63",destaque:"#755100",fundo:"#ffffff",texto:"#241c26"}
};

function hsl(value:string) {
  const hex=/^#[0-9a-f]{6}$/i.test(value)?value:"#0e6496";
  const [r,g,b]=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255);
  const max=Math.max(r,g,b),min=Math.min(r,g,b),delta=max-min,l=(max+min)/2;
  const s=delta===0?0:delta/(1-Math.abs(2*l-1));
  const h=delta===0?0:max===r?60*(((g-b)/delta+6)%6):max===g?60*((b-r)/delta+2):60*((r-g)/delta+4);
  return h.toFixed(2)+" "+(s*100).toFixed(2)+"% "+(l*100).toFixed(2)+"%";
}
export function portalStyle(colors:Colors):CSSProperties {
  return {"--primary":hsl(colors.primaria),"--primary-foreground":hsl(colors.fundo),
    "--secondary":hsl(colors.secundaria),"--accent":hsl(colors.destaque),
    "--background":hsl(colors.fundo),"--card":hsl(colors.fundo),"--foreground":hsl(colors.texto),
    "--card-foreground":hsl(colors.texto),"--muted-foreground":hsl(colors.texto),
    "--ring":hsl(colors.destaque),"--portal-secondary":colors.secundaria,"--portal-accent":colors.destaque} as CSSProperties;
}
