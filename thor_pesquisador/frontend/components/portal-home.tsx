"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight,Search } from "lucide-react";
import { request } from "@/lib/api";
import { CatalogItem } from "@/lib/portal";
import { PortalShell,usePortal } from "./portal-shell";
import { PortalCards } from "./portal-cards";

export function PortalHome(){return <PortalShell><Home/></PortalShell>;}
function Home(){
  const {config}=usePortal(),router=useRouter();
  const [q,setQ]=useState(""),[items,setItems]=useState<CatalogItem[]>([]),[popular,setPopular]=useState(false);
  const [loading,setLoading]=useState(true),[error,setError]=useState("");
  useEffect(()=>{
    let live=true;
    request<{items:CatalogItem[];com_acessos:boolean}>("/publico/destaques").then(r=>{if(live){setItems(r.items);setPopular(r.com_acessos);}})
      .catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[]);
  return <>
    <section className="portal-hero"><div className="portal-width">
      <p className="portal-kicker">Instrumentos de pesquisa</p>
      <h1>{config.nome_instituicao}</h1>
      <form className="portal-search" onSubmit={e=>{e.preventDefault();router.push("/consulta?"+new URLSearchParams({q:q.trim()}));}}>
        <label className="portal-search-input"><Search size={21}/><input aria-label="Pesquisar instrumentos" placeholder="Nome ou descricao do instrumento" value={q} onChange={e=>setQ(e.target.value)} maxLength={150}/></label>
        <button className="button" type="submit">Pesquisar<ArrowRight size={18}/></button>
      </form>
    </div></section>
    <section className="portal-width portal-section stack">
      <div className="row"><div className="page-heading"><h2>{popular?"Instrumentos mais acessados":"Instrumentos publicados"}</h2></div>
        <Link className="portal-text-link" href="/consulta">Ver todos<ArrowRight size={16}/></Link></div>
      {loading&&<p role="status">Carregando instrumentos...</p>}
      {error&&<p className="error" role="alert">{error}</p>}
      <PortalCards items={items}/>
      {!loading&&!error&&!items.length&&<p>Nenhum instrumento publicado no momento.</p>}
    </section>
  </>;
}
