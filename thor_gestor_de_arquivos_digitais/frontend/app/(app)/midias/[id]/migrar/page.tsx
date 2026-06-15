import { MidiaMigracaoPage } from "@/features/midias/midia-migracao-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MidiaMigracaoPage midiaId={Number(id)} />;
}
