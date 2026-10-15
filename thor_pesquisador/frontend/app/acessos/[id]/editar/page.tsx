import { AcessoEditor } from "@/components/acesso-editor";
export default async function EditAccess({params,searchParams}:{
  params:Promise<{id:string}>;searchParams:Promise<{usuario?:string}>;
}) {
  const {id} = await params;const query = await searchParams;
  return <AcessoEditor id={id} usuarioId={query.usuario}/>;
}
