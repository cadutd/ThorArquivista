import { AcessoCadastro } from "@/components/acesso-cadastro";
export default async function NewAccess({searchParams}: {searchParams:Promise<{usuario?:string}>}) {
  const params=await searchParams;return <AcessoCadastro usuarioId={params.usuario}/>;
}
