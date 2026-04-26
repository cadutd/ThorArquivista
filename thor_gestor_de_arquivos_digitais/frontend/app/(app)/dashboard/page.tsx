"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Archive, Boxes, Database, HardDrive, MapPinned, PackageCheck, ShieldCheck, Warehouse } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardStats } from "@/lib/api/domain";

export default function DashboardPage() {
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardStats,
  });
  const stats = dashboard.data;
  const supportTotals = new Map(
    stats?.unidades_por_suporte.map((item) => [item.tipo_suporte, item.total]) ?? [],
  );
  const chartData = [
    { name: "Físico", total: supportTotals.get("FISICO") ?? 0 },
    { name: "Digital", total: supportTotals.get("DIGITAL") ?? 0 },
    { name: "Híbrido", total: supportTotals.get("HIBRIDO") ?? 0 },
  ];
  const enderecamento = stats?.enderecamento;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Indicadores operacionais do acervo e da camada de preservação.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total de unidades" value={stats?.total_unidades ?? 0} icon={Archive} />
        <MetricCard title="AIPs digitais" value={stats?.aips_digitais ?? 0} icon={Database} />
        <MetricCard title="Mídias ativas" value={stats?.midias_ativas ?? 0} icon={HardDrive} />
        <MetricCard title="Alertas" value={stats?.alertas ?? 0} icon={AlertTriangle} />
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold tracking-normal">Endereçamento</h2>
          <p className="text-sm text-muted-foreground">
            Capacidade e ocupação dos locais de guarda.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Locais de guarda" value={enderecamento?.locais ?? 0} icon={Warehouse} />
          <MetricCard title="Zonas" value={enderecamento?.zonas ?? 0} icon={MapPinned} />
          <MetricCard title="Estantes" value={enderecamento?.estruturas ?? 0} icon={Boxes} />
          <MetricCard title="Posições totais" value={enderecamento?.posicoes ?? 0} icon={PackageCheck} />
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Espaços livres" value={enderecamento?.posicoes_livres ?? 0} icon={PackageCheck} />
          <MetricCard title="Espaços ocupados" value={enderecamento?.posicoes_ocupadas ?? 0} icon={Archive} />
          <MetricCard title="Posições inativas" value={enderecamento?.posicoes_inativas ?? 0} icon={AlertTriangle} />
          <MetricCard title="Taxa de ocupação" value={`${(enderecamento?.taxa_ocupacao ?? 0).toFixed(2)}%`} icon={Database} />
        </div>
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
  value: number | string;
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
