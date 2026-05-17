"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getUsuario } from "@/lib/api/usuarios";
import { UsuarioForm } from "./usuario-form";

export function UsuarioEditPage({ usuarioId }: { usuarioId: string }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["usuarios", usuarioId],
    queryFn: () => getUsuario(usuarioId),
    enabled: Boolean(usuarioId),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar usuário</h1>
          <p className="text-sm text-muted-foreground">Atualize o perfil local vinculado ao provedor de identidade.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/usuarios">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Edição</CardTitle>
          <CardDescription>{query.data ? query.data.nome : "Carregando dados do usuário."}</CardDescription>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando usuário...</p>
          ) : query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : query.data ? (
            <UsuarioForm usuario={query.data} onSaved={() => router.push("/usuarios")} />
          ) : (
            <p className="text-sm text-muted-foreground">Usuário não encontrado.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
