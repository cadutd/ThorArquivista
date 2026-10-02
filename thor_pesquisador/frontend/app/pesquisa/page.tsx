"use client";

import Link from "next/link";
import { FileSearch, Search, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/app-shell";

export default function PesquisaPage() {
  return (
    <AppShell>
      <div className="stack">
        <div className="page-heading">
          <h1>Pesquisa</h1>
          <p>Área consultiva dos instrumentos publicados.</p>
        </div>

        <section className="dashboard-grid">
          <div className="card metric-card">
            <div>
              <div className="metric-title">Busca por instrumentos</div>
              <div className="metric-value" style={{ fontSize: 22 }}>Disponível</div>
            </div>
            <div className="metric-icon">
              <Search size={20} />
            </div>
          </div>
          <div className="card metric-card">
            <div>
              <div className="metric-title">Controle de acesso</div>
              <div className="metric-value" style={{ fontSize: 22 }}>gov.br</div>
            </div>
            <div className="metric-icon">
              <ShieldCheck size={20} />
            </div>
          </div>
        </section>

        <section className="panel row">
          <div className="actions">
            <FileSearch color="var(--primary)" />
            <div>
              <h2 style={{ margin: 0 }}>Instrumentos de pesquisa</h2>
              <p className="muted" style={{ margin: "4px 0 0" }}>
                Use a gestão de instrumentos para consultar registros enquanto o portal público evolui nas próximas fases.
              </p>
            </div>
          </div>
          <Link className="button" href="/instrumentos">Abrir instrumentos</Link>
        </section>
      </div>
    </AppShell>
  );
}
