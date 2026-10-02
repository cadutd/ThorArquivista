"use client";

import { useState } from "react";
import { Archive, LogIn, ShieldCheck } from "lucide-react";
import { devLogin, getGovbrStart } from "@/lib/api";

export default function LoginPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loginGovbr() {
    setLoading(true);
    setError("");
    try {
      const result = await getGovbrStart();
      window.location.assign(result.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao iniciar login.");
    } finally {
      setLoading(false);
    }
  }

  async function loginDev() {
    setLoading(true);
    setError("");
    try {
      await devLogin();
      window.location.assign("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao entrar em modo desenvolvimento.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-hero">
        <div>
          <div className="brand-mark" style={{ background: "rgba(255,255,255,0.16)", marginBottom: 20 }}>
            <Archive size={24} />
          </div>
          <h1>Thor Pesquisador</h1>
          <p>
            Instrumentos de pesquisa dinâmicos, consulta estruturada e gestão de registros
            em uma interface integrada ao gov.br.
          </p>
        </div>
      </section>

      <section className="login-panel">
        <div className="card" style={{ width: "min(100%, 440px)" }}>
          <div className="card-content stack">
            <div className="metric-icon">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0 }}>Acesso autenticado</h2>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                Entre com sua conta gov.br para acessar o painel.
              </p>
            </div>
            {error ? <p className="error">{error}</p> : null}
            <button className="button" disabled={loading} onClick={loginGovbr}>
              <LogIn size={18} />
              {loading ? "Abrindo..." : "Entrar com GOV.BR"}
            </button>
            <button className="button secondary" disabled={loading} onClick={loginDev}>
              Entrar em desenvolvimento
            </button>
            <div className="panel muted" style={{ fontSize: 12, padding: 12 }}>
              Ambiente local usa login de desenvolvimento. Em homologação e produção, configure as credenciais gov.br.
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
