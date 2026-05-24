import { PerfilEditPage } from "@/features/perfis/perfil-edit-page";

export default async function EditarPerfilPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PerfilEditPage perfilId={id} />;
}
