import { MidiaViewPage } from "@/features/midias/midia-view-page";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MidiaViewPage midiaId={Number(id)} />;
}
