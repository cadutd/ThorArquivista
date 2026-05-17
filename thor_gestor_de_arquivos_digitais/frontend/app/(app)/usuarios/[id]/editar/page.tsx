import { UsuarioEditPage } from "@/features/usuarios/usuario-edit-page";

export default async function EditarUsuarioPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <UsuarioEditPage usuarioId={id} />;
}
