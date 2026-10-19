"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, Database, FileSearch, Gauge, Image, KeyRound, LogOut, Menu, Search, Settings, ShieldCheck, Users, X } from "lucide-react";
import { useState } from "react";
import { ModalFrame } from "./modal-frame";
import { logout } from "@/lib/api";
import { AccessBoundary, AnyPermission, Permission, PermissionProvider } from "./permission";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge, acao:"dashboard_consultar" },
  { href: "/instrumentos", label: "Instrumentos", icon: FileSearch, acao:"instrumentos_consultar" },
  { href: "/imagens", label: "Imagens", icon: Image, acao:"imagens_consultar" },
  { href: "/pesquisa", label: "Pesquisa", icon: Search, acao:"pesquisa_consultar" },
  { href: "/revisao", label: "Revisao", icon: ShieldCheck, acao:"editorial_consultar" },
  { href: "/consulta", label: "Consulta publica", icon: Search, acao:"consulta_publicada" }
];

const administration = [
  {acao:"usuarios_consultar",href:"/usuarios",prefix:"/usuarios",label:"Gestão de Usuários",icon:Users,anyScope:false},
  {acao:"perfis_consultar",href:"/perfis",prefix:"/perfis",label:"Perfis",icon:ShieldCheck,anyScope:false},
  {acao:"permissoes_consultar",href:"/permissoes",prefix:"/permissoes",label:"Permissões",icon:KeyRound,anyScope:false},
  {acao:"acessos_consultar",href:"/acessos",prefix:"/acessos",label:"Concessoes de acesso",icon:KeyRound,anyScope:false},
  {acao:"auditoria_consultar",href:"/auditoria",prefix:"/auditoria",label:"Auditoria",icon:ShieldCheck,anyScope:true},
  {acao:"exportacoes_consultar",href:"/exportacoes",prefix:"/exportacoes",label:"Exportações",icon:Database,anyScope:true},
  {acao:"relatorios_consultar",href:"/relatorios",prefix:"/relatorios",label:"Relatórios",icon:Gauge,anyScope:true},
  {acao:"retencao_consultar",href:"/retencao/politicas",prefix:"/retencao",label:"Retenção",icon:FileSearch,anyScope:true},
  {acao:"portal_configuracao_consultar",href:"/portal/configuracao",prefix:"/portal/configuracao",label:"Configuracao do Portal",icon:Settings,anyScope:false}
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  async function sair() {
    await logout().catch(() => undefined);
    window.location.assign("/login");
  }

  return (
    <PermissionProvider><div className="app-frame">
      <aside className="sidebar">
        <Link href="/dashboard" className="sidebar-brand" aria-label="Thor Pesquisador">
          <div className="brand-mark">
            <Database size={20} />
          </div>
          <div>
            <div className="brand-title">Thor Pesquisador</div>
            <div className="brand-subtitle">Instrumentos dinâmicos</div>
          </div>
        </Link>
        <nav className="sidebar-nav">
          <SidebarNavigation pathname={pathname}/>
        </nav>
      </aside>

      <div className="app-content">
        <header className="app-header">
          <Link href="/dashboard" className="mobile-brand">
            <Database size={20} color="hsl(var(--primary))" />
            Thor Pesquisador
          </Link>
          <div className="header-pill">
            <ShieldCheck size={16} color="hsl(var(--primary))" />
            Sessão gov.br ativa
          </div>
          <div className="header-actions">
            <button className="icon-button mobile-menu-toggle" title="Abrir menu" aria-label="Abrir menu" aria-haspopup="dialog"
              onClick={() => setMenuOpen(true)}><Menu size={16}/></button>
            <button className="button secondary" onClick={sair}>
              <LogOut size={16} />
              Sair
            </button>
          </div>
        </header>
        <main className="container"><AccessBoundary publico={pathname === "/consulta" || pathname.startsWith("/consulta/")}>{children}</AccessBoundary></main>
      </div>
      {menuOpen && <ModalFrame title="Menu" onClose={() => setMenuOpen(false)}>
        <div className="row"><h2>Menu</h2><button autoFocus className="icon-button" title="Fechar menu" aria-label="Fechar menu"
          onClick={() => setMenuOpen(false)}><X size={16}/></button></div>
        <nav aria-label="Navegacao"><SidebarNavigation pathname={pathname} onNavigate={() => setMenuOpen(false)}/></nav>
      </ModalFrame>}
    </div></PermissionProvider>
  );
}

function SidebarNavigation({pathname, onNavigate}: {pathname:string;onNavigate?:()=>void}) {
  return <>
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Permission key={item.href} acao={item.acao} anyScope><Link href={item.href} className={`nav-link ${active ? "active" : ""}`} onClick={onNavigate}>
                <Icon size={16} />
                {item.label}
              </Link></Permission>
            );
          })}
          <AnyPermission acoes={administration.map(item=>item.acao)} anyScope><details className="admin-navigation"
            open={administration.some(item => pathname===item.prefix || pathname.startsWith(item.prefix+"/"))}>
            <summary className="nav-link"><Settings size={16}/>Administra&#231;&#227;o<ChevronDown size={16}/></summary>
            {administration.map(item => {
                const Icon=item.icon;return <Permission key={item.href} acao={item.acao} anyScope={item.anyScope}><Link key={item.href} className={"nav-link " + (pathname===item.prefix || pathname.startsWith(item.prefix+"/") ? "active" : "")}
                  href={item.href} onClick={onNavigate}><Icon size={16}/>{item.label}</Link></Permission>;
              })}
          </details></AnyPermission>

  </>;
}
