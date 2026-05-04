import { InstrumentoRegistroFormPage } from "@/features/instrumentos-pesquisa/instrumento-registro-form-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <InstrumentoRegistroFormPage instrumentoId={id} />;
}
