import { InstrumentoBuscaAvancadaPage } from "@/features/instrumentos-pesquisa/instrumento-busca-avancada-page";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  return <InstrumentoBuscaAvancadaPage instrumentoId={id} />;
}
