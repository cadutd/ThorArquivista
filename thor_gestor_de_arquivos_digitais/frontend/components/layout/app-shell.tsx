"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Archive,
  BookOpenText,
  Boxes,
  ChevronLeft,
  ChevronRight,
  Database,
  FileSearch,
  Gauge,
  HardDrive,
  LogOut,
  MapPinned,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/auth-provider";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/unidades", label: "Unidades", icon: Archive },
  { href: "/descricao-arquivistica", label: "Descrição Arquivística", icon: BookOpenText },
  { href: "/instrumentos-pesquisa", label: "Instrumentos de Pesquisa", icon: FileSearch },
  { href: "/midias", label: "Mídias", icon: HardDrive },
  { href: "/enderecamento", label: "Endereçamento", icon: MapPinned },
  { href: "/eventos", label: "Eventos", icon: Boxes },
  { href: "/admin", label: "Administração", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { logout, session } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const claims = session?.claims ?? {};
  const username =
    typeof claims.preferred_username === "string"
      ? claims.preferred_username
      : "Usuário";

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

        <nav className="space-y-1 p-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);

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
