"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Archive,
  BookOpenText,
  Building2,
  Boxes,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Database,
  FileSearch,
  FileText,
  Gauge,
  HardDrive,
  Inbox,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Users,
  Warehouse,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/auth-provider";
import { cn } from "@/lib/utils";

type NavigationLink = {
  href: string;
  label: string;
  icon: LucideIcon;
};

type NavigationGroup = {
  key: string;
  label: string;
  icon: LucideIcon;
  items: NavigationLink[];
};

type NavigationItem = NavigationLink | NavigationGroup;

const navigation: NavigationItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/admissao", label: "Admissão", icon: Inbox },
  {
    key: "gestao-acervos",
    label: "Gestão de Acervos",
    icon: Archive,
    items: [
      { href: "/unidades", label: "Acondicionamentos", icon: Archive },
      { href: "/descricao-arquivistica", label: "Descrição Arquivística", icon: BookOpenText },
      { href: "/entidades-produtoras", label: "Entidades Produtoras", icon: Building2 },
      { href: "/enderecamento", label: "Gestão de Armazém", icon: Warehouse },
      { href: "/instrumentos-pesquisa", label: "Instrumentos de Pesquisa", icon: FileSearch },
      { href: "/modelos-ficha-espelho", label: "Modelos de Ficha Espelho", icon: FileText },
    ],
  },
  {
    key: "pesquisa",
    label: "Pesquisa",
    icon: Search,
    items: [
      { href: "/pesquisa/descricao-arquivistica", label: "Descrição Arquivística", icon: BookOpenText },
      { href: "/pesquisa/instrumentos-pesquisa", label: "Instrumentos de Pesquisa", icon: FileSearch },
    ],
  },
  {
    key: "preservacao-digital",
    label: "Preservação Digital",
    icon: HardDrive,
    items: [{ href: "/midias", label: "Gestão de Mídias", icon: HardDrive }],
  },
  {
    key: "administracao",
    label: "Administração",
    icon: Settings,
    items: [
      { href: "/admin", label: "Administração Geral", icon: Settings },
      { href: "/usuarios", label: "Gestão de Usuários", icon: Users },
      { href: "/eventos", label: "Eventos", icon: Boxes },
    ],
  },
];

function isNavigationGroup(item: NavigationItem): item is NavigationGroup {
  return "items" in item;
}

function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { logout, session } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>("gestao-acervos");
  const claims = session?.claims ?? {};
  const username =
    typeof claims.preferred_username === "string"
      ? claims.preferred_username
      : "Usuário";

  const toggleGroup = (key: string) => {
    setOpenGroup((current) => (current === key ? null : key));
  };

  return (
    <div className="min-h-screen bg-background">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 hidden border-r bg-white transition-[width] duration-200 lg:block",
          collapsed ? "w-20" : "w-72",
        )}
      >
        <div className="relative flex h-16 items-center gap-2 border-b px-4">
          <Link
            href="/dashboard"
            className={cn(
              "flex min-w-0 flex-1 items-center gap-3 rounded-md py-2 transition-colors hover:bg-muted/60",
              collapsed ? "justify-center px-0" : "px-1",
            )}
            aria-label="Thor Gestor"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Database className="h-5 w-5" />
            </div>
            <div className={cn("min-w-0", collapsed && "hidden")}>
              <div className="text-sm font-semibold">Thor Gestor</div>
              <div className="text-xs text-muted-foreground">Arquivos digitais</div>
            </div>
          </Link>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={cn(
              "h-9 w-9 shrink-0",
              collapsed && "absolute -right-4 top-3 border bg-white shadow-sm",
            )}
            aria-label={collapsed ? "Expandir menu principal" : "Recolher menu principal"}
            title={collapsed ? "Expandir menu principal" : "Recolher menu principal"}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        <nav className="space-y-1 overflow-y-auto p-3">
          {navigation.map((item) => {
            const Icon = item.icon;

            if (isNavigationGroup(item)) {
              const isOpen = openGroup === item.key;
              const groupActive = item.items.some((child) => isActivePath(pathname, child.href));

              return (
                <div key={item.key} className="space-y-1">
                  <button
                    type="button"
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      "flex h-10 w-full items-center rounded-md text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                      collapsed ? "justify-center px-0" : "gap-3 px-3",
                      groupActive && "text-foreground",
                    )}
                    aria-expanded={isOpen}
                    onClick={() => toggleGroup(item.key)}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className={cn("min-w-0 flex-1 truncate text-left", collapsed && "sr-only")}>
                      {item.label}
                    </span>
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 shrink-0 transition-transform",
                        collapsed && "hidden",
                        !isOpen && "-rotate-90",
                      )}
                    />
                  </button>
                  {(isOpen || collapsed) && (
                    <div className={cn("space-y-1", collapsed ? "pt-1" : "pl-5")}>
                      {item.items.map((child) => {
                        const ChildIcon = child.icon;
                        const active = isActivePath(pathname, child.href);

                        return (
                          <Link
                            key={`${item.key}-${child.href}`}
                            href={child.href}
                            title={collapsed ? child.label : undefined}
                            className={cn(
                              "flex h-9 items-center rounded-md text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                              collapsed ? "justify-center px-0" : "gap-3 px-3",
                              active && "bg-secondary text-secondary-foreground",
                            )}
                          >
                            <ChildIcon className="h-4 w-4 shrink-0" />
                            <span className={cn("min-w-0 truncate", collapsed && "sr-only")}>{child.label}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            }

            const active = isActivePath(pathname, item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex h-10 items-center rounded-md text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  collapsed ? "justify-center px-0" : "gap-3 px-3",
                  active && "bg-secondary text-secondary-foreground",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className={cn(collapsed && "sr-only")}>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className={cn("transition-[padding-left] duration-200", collapsed ? "lg:pl-20" : "lg:pl-72")}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white/95 px-4 backdrop-blur md:px-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 rounded-md px-2 py-1 transition-colors hover:bg-muted lg:hidden"
          >
            <Database className="h-5 w-5 text-primary" />
            <span className="text-sm font-semibold">Thor Gestor</span>
          </Link>
          <div className="hidden items-center gap-2 rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground md:flex">
            <ShieldCheck className="h-4 w-4 text-primary" />
            Sessão Keycloak ativa
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <div className="text-sm font-medium">{username}</div>
              <div className="text-xs text-muted-foreground">Perfil autenticado</div>
            </div>
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Sair
            </Button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  );
}
