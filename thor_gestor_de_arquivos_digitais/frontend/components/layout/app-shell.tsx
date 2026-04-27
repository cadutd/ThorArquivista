"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Archive,
  BookOpenText,
  Boxes,
  Database,
  Gauge,
  HardDrive,
  MapPinned,
  LogOut,
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
  { href: "/midias", label: "Mídias", icon: HardDrive },
  { href: "/enderecamento", label: "Endereçamento", icon: MapPinned },
  { href: "/eventos", label: "Eventos", icon: Boxes },
  { href: "/admin", label: "Administração", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { logout, session } = useAuth();
  const claims = session?.claims ?? {};
  const username =
    typeof claims.preferred_username === "string"
      ? claims.preferred_username
      : "Usuário";

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r bg-white lg:block">
        <Link
          href="/dashboard"
          className="flex h-16 items-center gap-3 border-b px-5 transition-colors hover:bg-muted/60"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold">Thor Gestor</div>
            <div className="text-xs text-muted-foreground">Arquivos digitais</div>
          </div>
        </Link>
        <nav className="space-y-1 p-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  active && "bg-secondary text-secondary-foreground",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-72">
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
