import { ProcessoAdmissaoDetailPage } from "@/features/admissao/processo-admissao-detail-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProcessoAdmissaoDetailPage id={id} />;
}
