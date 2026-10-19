import Link from "next/link";
import { ArrowUpRight,BookOpen } from "lucide-react";
import { CatalogItem,types } from "@/lib/portal";
import { InstrumentoCardImage } from "./instrumento-card-image";

export function PortalCards({items}:{items:CatalogItem[]}) {
  return <div className="portal-cards">{items.map(item=><Link key={item.id} href={"/consulta/"+item.id} prefetch={false} className="portal-card">
    <InstrumentoCardImage src={item.imagem_card_url}/>
    <div className="portal-card-type"><BookOpen size={20}/><span>{types[item.tipo]||item.tipo}</span><ArrowUpRight size={18}/></div>
    <h3>{item.nome}</h3>
    {item.descricao&&<p>{item.descricao}</p>}
    <span className="portal-card-action">Consultar instrumento<ArrowUpRight size={16}/></span>
  </Link>)}</div>;
}
