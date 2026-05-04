import { InstrumentoRegistrosPage } from "@/features/instrumentos-pesquisa/instrumento-registros-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <InstrumentoRegistrosPage instrumentoId={id} />;
}
