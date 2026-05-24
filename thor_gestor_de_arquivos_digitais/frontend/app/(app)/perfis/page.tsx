"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PerfisPage } from "@/features/perfis/perfis-page";

export default function PerfisRoute() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Perfis</h1>
          <p className="text-sm text-muted-foreground">Agrupe permissões e associe usuários a perfis operacionais.</p>
        </div>
        <Button asChild className="!text-white hover:!text-white"><Link href="/perfis/nova" className="!text-white"><Plus className="h-4 w-4" />Novo perfil</Link></Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Cadastro</CardTitle><CardDescription>Consulte e mantenha perfis de acesso.</CardDescription></CardHeader>
        <CardContent><PerfisPage /></CardContent>
      </Card>
    </div>
  );
}
