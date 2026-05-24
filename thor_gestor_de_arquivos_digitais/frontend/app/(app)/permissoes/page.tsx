"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PermissoesPage } from "@/features/permissoes/permissoes-page";

export default function PermissoesRoute() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Permissões</h1>
        <p className="text-sm text-muted-foreground">Ações autorizáveis por função do sistema, mantidas exclusivamente por script de carga.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Consulta</CardTitle>
          <CardDescription>Consulte as permissões disponíveis para associação aos perfis.</CardDescription>
        </CardHeader>
        <CardContent><PermissoesPage /></CardContent>
      </Card>
    </div>
  );
}
