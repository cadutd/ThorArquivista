"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Database, FileSearch, Gauge, LogOut, Search, ShieldCheck } from "lucide-react";
import { logout } from "@/lib/api";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/instrumentos", label: "Instrumentos", icon: FileSearch },
  { href: "/pesquisa", label: "Pesquisa", icon: Search }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  async function sair() {
    await logout().catch(() => undefined);
    window.location.assign("/login");
  }

  return (
    <div className="app-frame">
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
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link key={item.href} href={item.href} className={`nav-link ${active ? "active" : ""}`}>
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
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
            <button className="button secondary" onClick={sair}>
              <LogOut size={16} />
              Sair
            </button>
          </div>
        </header>
        <main className="container">{children}</main>
      </div>
    </div>
  );
}
