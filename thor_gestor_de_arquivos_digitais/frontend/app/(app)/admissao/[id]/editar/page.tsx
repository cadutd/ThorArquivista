import { ProcessoAdmissaoEditPage } from "@/features/admissao/processo-admissao-edit-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProcessoAdmissaoEditPage id={id} />;
}
