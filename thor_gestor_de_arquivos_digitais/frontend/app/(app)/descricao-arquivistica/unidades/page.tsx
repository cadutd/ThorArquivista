import { DescricaoUnidadesPage } from "@/features/descricao-arquivistica/descricao-unidades-page";
import { Suspense } from "react";

export default function Page() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Carregando associação de unidades...</p>}>
      <DescricaoUnidadesPage />
    </Suspense>
  );
}
