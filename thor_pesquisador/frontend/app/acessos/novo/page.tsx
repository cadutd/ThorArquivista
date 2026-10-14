import { AcessoEditor } from "@/components/acesso-editor";
export default async function NewAccess({searchParams}: {searchParams:Promise<{usuario?:string}>}) {
  const params=await searchParams;return <AcessoEditor usuarioId={params.usuario}/>;
}
