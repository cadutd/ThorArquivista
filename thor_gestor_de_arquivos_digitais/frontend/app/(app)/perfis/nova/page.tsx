"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PerfilForm } from "@/features/perfis/perfil-form";

export default function NovoPerfilPage() {
  const router = useRouter();
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Novo perfil</h1>
          <p className="text-sm text-muted-foreground">Cadastre um perfil e selecione suas permissões.</p>
        </div>
        <Button asChild variant="outline"><Link href="/perfis"><ArrowLeft className="h-4 w-4" />Voltar</Link></Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Cadastro</CardTitle><CardDescription>Campos obrigatórios são marcados com asterisco.</CardDescription></CardHeader>
        <CardContent><PerfilForm onSaved={() => router.push("/perfis")} /></CardContent>
      </Card>
    </div>
  );
}
