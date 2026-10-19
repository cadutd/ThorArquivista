"use client";
import Link from "next/link";
import { Archive,ArrowUpRight,LogIn,LogOut } from "lucide-react";
import { createContext,useContext,useEffect,useState } from "react";
import { request,logout } from "@/lib/api";
import { PortalConfig,PortalState,defaults,portalStyle } from "@/lib/portal";

const Context=createContext<{config:PortalConfig;identity:PortalState}>({config:defaults,identity:{autenticado:false}});
export function usePortal(){return useContext(Context);}
export function PortalShell({children}:{children:React.ReactNode}) {
  const [config,setConfig]=useState(defaults),[identity,setIdentity]=useState<PortalState>({autenticado:false});
  const [error,setError]=useState("");
  useEffect(()=>{
    let live=true;
    request<PortalConfig>("/publico/configuracao",{cache:"no-store"}).then(value=>{if(live)setConfig(value);}).catch(e=>{if(live)setError(e.message);});
    const check=()=>request<PortalState>("/auth/estado",{cache:"no-store"}).then(value=>{if(live)setIdentity(value);}).catch(()=>{if(live)setIdentity({autenticado:false});});
    void check();
    window.addEventListener("focus",check);
    return()=>{live=false;window.removeEventListener("focus",check);};
  },[]);
  async function sair(){
    try {await logout();window.location.assign("/");}
    catch(e){setError(e instanceof Error?e.message:"Falha ao sair.");}
  }
  return <Context.Provider value={{config,identity}}><div className="portal" style={portalStyle(config.cores)}>
    <a className="portal-skip" href="#conteudo">Ir para o conteudo</a>
    <header className="portal-header"><div className="portal-width portal-header-inner">
      <Link className="portal-brand" href="/"><Archive size={24}/><span>{config.nome_instituicao}</span></Link>
      <nav aria-label="Navegacao publica">
        {identity.area_interna&&<Link href={identity.destino_interno||"/dashboard"}>Area interna<ArrowUpRight size={16}/></Link>}
        {identity.autenticado?<><span className="portal-identity">{identity.visitante?"Visitante autenticado":identity.nome}</span>
          <button className="button secondary" onClick={sair}><LogOut size={16}/>Sair</button></>:
          <Link className="button" href="/login?next=%2Fconsulta"><LogIn size={16}/>Entrar</Link>}
      </nav>
    </div></header>
    {error&&<div className="portal-width"><p className="error" role="alert">{error}</p></div>}
    <main id="conteudo" tabIndex={-1}>{children}</main>
    <footer className="portal-footer"><div className="portal-width"><strong>{config.nome_instituicao}</strong><span>Instrumentos de pesquisa</span></div></footer>
  </div></Context.Provider>;
}
