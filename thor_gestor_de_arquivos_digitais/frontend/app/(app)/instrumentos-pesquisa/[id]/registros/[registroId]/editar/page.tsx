import { InstrumentoRegistroFormPage } from "@/features/instrumentos-pesquisa/instrumento-registro-form-page";

type PageProps = {
  params: Promise<{ id: string; registroId: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id, registroId } = await params;
  return <InstrumentoRegistroFormPage instrumentoId={id} registroId={registroId} />;
}
