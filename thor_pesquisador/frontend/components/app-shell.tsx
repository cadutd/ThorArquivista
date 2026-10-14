"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, Database, FileSearch, Gauge, Image, KeyRound, LogOut, Menu, Search, Settings, ShieldCheck, Users, X } from "lucide-react";
import { useState } from "react";
import { ModalFrame } from "./modal-frame";
import { logout } from "@/lib/api";
import { AnyPermission, Permission, PermissionProvider } from "./permission";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge, acao:"dashboard_consultar" },
  { href: "/instrumentos", label: "Instrumentos", icon: FileSearch, acao:"instrumentos_consultar" },
  { href: "/imagens", label: "Imagens", icon: Image, acao:"imagens_consultar" },
  { href: "/pesquisa", label: "Pesquisa", icon: Search, acao:"pesquisa_consultar" },
  { href: "/revisao", label: "Revisao", icon: ShieldCheck, acao:"editorial_consultar" },
  { href: "/consulta", label: "Consulta publica", icon: Search, acao:"consulta_publicada" }
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
        <main className="container">{children}</main>
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
          <AnyPermission acoes={["usuarios_consultar","perfis_consultar","permissoes_consultar","acessos_consultar"]}><details className="admin-navigation"
            open={["/usuarios","/perfis","/permissoes","/acessos"].some(p => pathname.startsWith(p))}>
            <summary className="nav-link"><Settings size={16}/>Administra&#231;&#227;o<ChevronDown size={16}/></summary>
            {[{acao:"usuarios_consultar",href:"/usuarios",label:"Gest\u00e3o de Usu\u00e1rios",icon:Users},
              {acao:"perfis_consultar",href:"/perfis",label:"Perfis",icon:ShieldCheck},
              {acao:"permissoes_consultar",href:"/permissoes",label:"Permiss\u00f5es",icon:KeyRound},
              {acao:"acessos_consultar",href:"/acessos",label:"Concessoes de acesso",icon:KeyRound}].map(item => {
                const Icon=item.icon;return <Permission key={item.href} acao={item.acao}><Link key={item.href} className={"nav-link " + (pathname.startsWith(item.href) ? "active" : "")}
                  href={item.href} onClick={onNavigate}><Icon size={16}/>{item.label}</Link></Permission>;
              })}
          </details></AnyPermission>

  </>;
}
