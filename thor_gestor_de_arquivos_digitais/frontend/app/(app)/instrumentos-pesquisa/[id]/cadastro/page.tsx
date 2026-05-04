import { DynamicInstrumentCadastroPage } from "@/features/instrumentos-pesquisa/instrumento-cadastro-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <DynamicInstrumentCadastroPage instrumentoId={id} />;
}
