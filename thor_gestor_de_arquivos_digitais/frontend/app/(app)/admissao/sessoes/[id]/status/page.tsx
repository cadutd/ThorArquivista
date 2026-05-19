import { SessaoStatusPage } from "@/features/admissao/sessao-status-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SessaoStatusPage id={id} />;
}
