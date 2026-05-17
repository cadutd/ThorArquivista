"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UsuariosPage } from "@/features/usuarios/usuarios-page";
import { listUsuariosPage } from "@/lib/api/usuarios";

export default function UsuariosRoute() {
  const count = useQuery({
    queryKey: ["usuarios", "count"],
    queryFn: () => listUsuariosPage({ limit: 1 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Usuários</h1>
          <p className="text-sm text-muted-foreground">
            Perfis locais vinculados ao provedor de identidade.
          </p>
        </div>
        <Button asChild className="!text-white hover:!text-white">
          <Link href="/usuarios/nova" className="!text-white">
            <Plus className="h-4 w-4" />
            Novo usuário
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cadastro</CardTitle>
          <CardDescription>
            {count.isLoading ? "Carregando registros..." : `${count.data?.total ?? 0} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UsuariosPage />
        </CardContent>
      </Card>
    </div>
  );
}
