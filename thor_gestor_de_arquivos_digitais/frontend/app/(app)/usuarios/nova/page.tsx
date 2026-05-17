"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UsuarioForm } from "@/features/usuarios/usuario-form";

export default function NovoUsuarioPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Novo usuário</h1>
          <p className="text-sm text-muted-foreground">Informe identificação, papel e vínculo opcional com Keycloak.</p>
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
          <CardTitle>Cadastro</CardTitle>
          <CardDescription>Preencha os dados do novo perfil local.</CardDescription>
        </CardHeader>
        <CardContent>
          <UsuarioForm />
        </CardContent>
      </Card>
    </div>
  );
}
