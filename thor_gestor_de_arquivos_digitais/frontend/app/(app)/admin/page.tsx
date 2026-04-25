"use client";

import { KeyRound, ServerCog, Settings, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { config } from "@/lib/config";

const adminItems = [
  {
    title: "Keycloak",
    description: "Realm, clientes, papéis e políticas de autenticação.",
    icon: KeyRound,
    value: "thor",
  },
  {
    title: "Usuários",
    description: "Gestão delegada ao provedor de identidade.",
    icon: Users,
    value: "OIDC",
  },
  {
    title: "API",
    description: "Endpoint FastAPI usado pelo frontend.",
    icon: ServerCog,
    value: config.apiBaseUrl,
  },
  {
    title: "Configurações",
    description: "Preferências operacionais e parâmetros futuros.",
    icon: Settings,
    value: "MVP",
  },
];

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Administração</h1>
        <p className="text-sm text-muted-foreground">
          Configurações de autenticação, integração e governança.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        {adminItems.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title}>
              <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>{item.description}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <code className="block rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                  {item.value}
                </code>
              </CardContent>
            </Card>
          );
        })}
      </section>
    </div>
  );
}
