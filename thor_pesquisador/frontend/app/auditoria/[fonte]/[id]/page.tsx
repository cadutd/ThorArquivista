"use client";
import { useParams } from "next/navigation";
import { ConformidadeDetail } from "@/components/conformidade-detail";
export default function Page(){
  const {id,fonte}=useParams<{id:string;fonte:string;}>();
  return <ConformidadeDetail tipo="auditoria" id={id} fonte={fonte}/>;
}
