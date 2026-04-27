"use client";

import { Archive, ShieldCheck } from "lucide-react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth/auth-provider";
import { SESSION_EXPIRED_REASON } from "@/lib/auth/session";

function LoginContent() {
  const { login } = useAuth();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next");
  const showSessionExpiredMessage =
    searchParams.get("motivo") === SESSION_EXPIRED_REASON;

  return (
    <main className="grid min-h-screen grid-cols-1 bg-background lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex min-h-[45vh] items-end bg-[linear-gradient(rgba(8,47,73,0.72),rgba(8,47,73,0.38)),url('/images/login-digital-archive.png')] bg-cover bg-center p-8 text-white lg:min-h-screen lg:p-12">
        <div className="max-w-2xl">
          <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-md bg-white/15 backdrop-blur">
            <Archive className="h-6 w-6" />
          </div>
          <h1 className="text-4xl font-semibold tracking-normal md:text-5xl">
            Thor Gestor de Arquivos Digitais
          </h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-white/85">
            Preservação, armazenamento e auditoria de unidades digitais em uma
            interface administrativa integrada ao Keycloak.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-center px-4 py-10">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <CardTitle>Acesso autenticado</CardTitle>
            <CardDescription>
              Entre com sua conta do Keycloak para acessar o painel.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {showSessionExpiredMessage ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-900">
                Sua sessão expirou. Entre novamente para continuar.
              </div>
            ) : null}
            <Button className="w-full" onClick={() => void login(nextPath)}>
              Entrar com Keycloak
            </Button>
            <div className="rounded-md border bg-muted p-3 text-xs leading-5 text-muted-foreground">
              Realm padrão: <strong>thor</strong>. Cliente padrão:{" "}
              <strong>thor-api</strong>.
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
