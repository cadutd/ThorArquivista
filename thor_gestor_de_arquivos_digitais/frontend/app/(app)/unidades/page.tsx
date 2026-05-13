"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UnidadesTable } from "@/features/unidades/unidades-table";
import { listUnidadesPage, type UnidadeFilters } from "@/lib/api/domain";

export default function UnidadesPage() {
  const [filters, setFilters] = useState<UnidadeFilters>({});
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const query = useQuery({
    queryKey: ["unidades", filters, pageIndex, pageSize],
    queryFn: () =>
      listUnidadesPage({
        limit: pageSize,
        offset: pageIndex * pageSize,
        filters,
      }),
  });
  const unidades = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Unidades de Acondicionamento</h1>
          <p className="text-sm text-muted-foreground">
            Cadastro, busca e acompanhamento das unidades físicas e digitais.
          </p>
        </div>
        <Button asChild className="!text-white hover:!text-white">
          <Link href="/unidades/nova" className="!text-white">
            <Plus className="h-4 w-4" />
            Nova unidade
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Acervo</CardTitle>
          <CardDescription>
            {query.isLoading ? "Carregando registros..." : `${total} registros encontrados`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.error ? (
            <p className="text-sm text-destructive">{query.error.message}</p>
          ) : (
            <UnidadesTable
              data={unidades}
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
