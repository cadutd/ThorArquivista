"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Archive, Database, HardDrive, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listMidias, listUnidades } from "@/lib/api/domain";

export default function DashboardPage() {
  const unidades = useQuery({ queryKey: ["unidades"], queryFn: listUnidades });
  const midias = useQuery({ queryKey: ["midias"], queryFn: listMidias });

  const stats = useMemo(() => {
    const unidadeRows = unidades.data ?? [];
    const midiaRows = midias.data ?? [];

    return {
      totalUnidades: unidadeRows.length,
      aipsDigitais: unidadeRows.filter((item) => item.tipo_unidade === "AIP").length,
      midiasAtivas: midiaRows.filter((item) => item.ativo).length,
      alertas: unidadeRows.filter((item) => item.status !== "ATIVA").length,
    };
  }, [midias.data, unidades.data]);

  const chartData = [
    { name: "Físico", total: (unidades.data ?? []).filter((item) => item.tipo_suporte === "FISICO").length },
    { name: "Digital", total: (unidades.data ?? []).filter((item) => item.tipo_suporte === "DIGITAL").length },
    { name: "Híbrido", total: (unidades.data ?? []).filter((item) => item.tipo_suporte === "HIBRIDO").length },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Indicadores operacionais do acervo e da camada de preservação.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total de unidades" value={stats.totalUnidades} icon={Archive} />
        <MetricCard title="AIPs digitais" value={stats.aipsDigitais} icon={Database} />
        <MetricCard title="Mídias ativas" value={stats.midiasAtivas} icon={HardDrive} />
        <MetricCard title="Alertas" value={stats.alertas} icon={AlertTriangle} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Unidades por suporte</CardTitle>
            <CardDescription>Distribuição cadastrada na API.</CardDescription>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="total" fill="#0b6ea8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preservação</CardTitle>
            <CardDescription>Estado geral para acompanhamento diário.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "Token Keycloak aplicado nas chamadas protegidas",
              "Cache de listagens via TanStack Query",
              "Base pronta para eventos e cópias digitais",
            ].map((item) => (
              <div key={item} className="flex items-start gap-3 rounded-md border p-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 text-primary" />
                <span className="text-sm">{item}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon,
}: {
  title: string;
  value: number;
  icon: React.ElementType;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal">{value}</p>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
