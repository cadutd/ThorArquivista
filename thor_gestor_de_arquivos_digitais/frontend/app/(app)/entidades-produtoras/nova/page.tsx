"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EntidadeProdutoraForm } from "@/features/entidades-produtoras/entidade-produtora-form";

export default function NovaEntidadeProdutoraPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Nova entidade produtora</h1>
          <p className="text-sm text-muted-foreground">Informe identificação, hierarquia, temporalidade, contato e endereço.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/entidades-produtoras">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cadastro</CardTitle>
          <CardDescription>Preencha os dados da nova entidade.</CardDescription>
        </CardHeader>
        <CardContent>
          <EntidadeProdutoraForm onSaved={() => router.push("/entidades-produtoras")} />
        </CardContent>
      </Card>
    </div>
  );
}
