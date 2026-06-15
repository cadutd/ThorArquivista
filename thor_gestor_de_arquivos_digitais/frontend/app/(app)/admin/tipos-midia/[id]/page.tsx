import { TipoMidiaViewPage } from "@/features/midias/tipos-midia-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TipoMidiaViewPage tipoId={id} />;
}
