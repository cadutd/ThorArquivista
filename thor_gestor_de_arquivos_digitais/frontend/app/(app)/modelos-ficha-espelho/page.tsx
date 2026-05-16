"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ModelosFichaTable,
  type ModeloFichaFilters,
} from "@/features/ficha-espelho/modelos-ficha-table";
import { listarModelosFichaEspelho } from "@/lib/api/ficha-espelho";

export default function ModelosFichaPage() {
  const [filters, setFilters] = useState<ModeloFichaFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const query = useQuery({
    queryKey: ["fichas-espelho", "modelos", filters, pageIndex, pageSize],
    queryFn: () =>
      listarModelosFichaEspelho({
        limit: pageSize,
        offset: pageIndex * pageSize,
        q: filters.q,
        ativo: filters.ativo === "" ? undefined : filters.ativo,
      }),
  });
  const modelos = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Modelos de Ficha Espelho</h1>
          <p className="text-sm text-muted-foreground">Cadastro, busca e manutenção dos modelos de impressão.</p>
        </div>
        <Button asChild className="!text-white hover:!text-white">
          <Link href="/modelos-ficha-espelho/nova" className="!text-white">
            <Plus className="h-4 w-4" />
            Novo modelo
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Modelos</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${total} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <ModelosFichaTable
              data={modelos}
              filters={filters}
              onSearch={(nextFilters) => {
                setFilters(nextFilters);
                setPageIndex(0);
              }}
              pageIndex={pageIndex}
              pageSize={pageSize}
              total={total}
              isLoading={query.isFetching}
              onPageChange={setPageIndex}
              onPageSizeChange={(nextPageSize) => {
                setPageSize(nextPageSize);
                setPageIndex(0);
              }}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
