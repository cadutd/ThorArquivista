import { UnidadeEditPage } from "@/features/unidades/unidade-edit-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <UnidadeEditPage unidadeId={Number(id)} />;
}
