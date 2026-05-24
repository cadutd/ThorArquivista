"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getPerfil } from "@/lib/api/perfis-permissoes";
import { PerfilForm } from "./perfil-form";

export function PerfilEditPage({ perfilId }: { perfilId: string }) {
  const router = useRouter();
  const query = useQuery({
    queryKey: ["perfis", perfilId],
    queryFn: () => getPerfil(perfilId),
    enabled: Boolean(perfilId),
  });
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Editar perfil</h1>
          <p className="text-sm text-muted-foreground">Atualize dados e permissões do perfil.</p>
        </div>
        <Button asChild variant="outline"><Link href="/perfis"><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Edição</CardTitle><CardDescription>{query.data ? query.data.nome : "Carregando dados do perfil."}</CardDescription></CardHeader>
        <CardContent>
          {query.isLoading ? <p className="text-sm text-muted-foreground">Carregando perfil...</p> : null}
          {query.error ? <p className="text-sm text-destructive">{query.error.message}</p> : null}
          {query.data ? <PerfilForm perfil={query.data} onSaved={() => router.push("/perfis")} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}
