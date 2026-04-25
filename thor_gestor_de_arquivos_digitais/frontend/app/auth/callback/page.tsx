"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { completeLogin } from "@/lib/auth/oidc";
import { useAuth } from "@/lib/auth/auth-provider";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthenticatedSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const missingCallbackParams = !code || !state;
  const errorMessage =
    error ??
    (missingCallbackParams
      ? "Retorno do provedor de identidade sem código de autorização."
      : null);

  useEffect(() => {
    if (!code || !state) {
      return;
    }

    completeLogin(code, state)
      .then((session) => {
        setAuthenticatedSession(session);
        router.replace("/dashboard");
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Falha ao autenticar.");
      });
  }, [code, router, setAuthenticatedSession, state]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md rounded-lg border bg-white p-6 text-center shadow-panel">
        <h1 className="text-base font-semibold">
          {errorMessage ? "Autenticação não concluída" : "Concluindo autenticação"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {errorMessage ?? "Validando o retorno do Keycloak e preparando sua sessão."}
        </p>
      </div>
    </main>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={null}>
      <CallbackContent />
    </Suspense>
  );
}
