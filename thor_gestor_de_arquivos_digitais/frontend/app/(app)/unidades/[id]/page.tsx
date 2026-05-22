import { UnidadeViewPage } from "@/features/unidades/unidade-view-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <UnidadeViewPage unidadeId={Number(id)} />;
}
