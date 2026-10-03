"use client";

import Link from "next/link";
import { AlertTriangle, Database, FileSearch, ListChecks, Search, Settings2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getDashboardStats } from "@/lib/api";
import type { DashboardStats } from "@/types/domain";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardStats()
      .then((data) => {
        setStats(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar dashboard."));
  }, []);

  return (
    <AppShell>
      <div className="stack">
        <div className="page-heading">
          <h1>Dashboard</h1>
          <p>Indicadores operacionais dos instrumentos de pesquisa e registros dinâmicos.</p>
        </div>

        {error ? (
          <div className="panel row">
            <div className="actions">
              <AlertTriangle color="hsl(var(--destructive))" />
              <span className="error">{error}</span>
            </div>
            <Link className="button secondary" href="/login">Entrar novamente</Link>
          </div>
        ) : null}

        <section className="dashboard-grid">
          <MetricCard title="Instrumentos" value={stats?.total_instrumentos ?? 0} icon={FileSearch} />
          <MetricCard title="Publicados" value={stats?.instrumentos_publicados ?? 0} icon={ShieldCheck} />
          <MetricCard title="Rascunhos" value={stats?.instrumentos_rascunho ?? 0} icon={Settings2} />
          <MetricCard title="Registros" value={stats?.total_registros ?? 0} icon={Database} />
        </section>

        <section className="dashboard-grid">
          <MetricCard title="Campos configurados" value={stats?.total_campos ?? 0} icon={ListChecks} />
          <MetricCard title="Registros ativos" value={stats?.registros_ativos ?? 0} icon={Search} />
          <MetricCard title="Registros inativos" value={stats?.registros_inativos ?? 0} icon={AlertTriangle} />
          <MetricCard title="Falhas de indexacao" value={stats?.indexacao_jobs_falhos ?? 0} icon={AlertTriangle} />
        </section>

        <section className="card">
          <div className="card-content stack">
            <div className="row">
              <div>
                <h2 style={{ margin: 0 }}>Instrumentos por tipo</h2>
                <p className="muted" style={{ margin: "4px 0 0" }}>Distribuição cadastrada na API.</p>
              </div>
              <Link className="button" href="/instrumentos">Gerenciar instrumentos</Link>
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.instrumentos_por_tipo ?? []).map((item) => (
                    <tr key={item.tipo}>
                      <td>{item.tipo}</td>
                      <td>{item.total}</td>
                    </tr>
                  ))}
                  {!stats?.instrumentos_por_tipo.length ? (
                    <tr>
                      <td colSpan={2} className="muted">Nenhum instrumento cadastrado.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-content stack">
            <div>
              <h2 style={{ margin: 0 }}>Indexacao</h2>
              <p className="muted" style={{ margin: "4px 0 0" }}>Jobs recentes de reindexacao e busca avancada.</p>
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Status</th>
                    <th>Processados</th>
                    <th>Erro</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.indexacao_jobs_recentes ?? []).map((job) => (
                    <tr key={job.id}>
                      <td>{job.tipo}</td>
                      <td>{job.status}</td>
                      <td>{job.processados}/{job.total_estimado}</td>
                      <td>{job.erro ?? ""}</td>
                    </tr>
                  ))}
                  {!stats?.indexacao_jobs_recentes.length ? (
                    <tr>
                      <td colSpan={4} className="muted">Nenhum job de indexacao recente.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon
}: {
  title: string;
  value: number | string;
  icon: React.ElementType;
}) {
  return (
    <div className="card metric-card">
      <div>
        <div className="metric-title">{title}</div>
        <div className="metric-value">{value}</div>
      </div>
      <div className="metric-icon">
        <Icon size={20} />
      </div>
    </div>
  );
}
