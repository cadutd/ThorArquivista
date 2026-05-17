import { EntidadeProdutoraEditPage } from "@/features/entidades-produtoras/entidade-produtora-edit-page";

export default async function EditarEntidadeProdutoraPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EntidadeProdutoraEditPage entidadeId={id} />;
}
