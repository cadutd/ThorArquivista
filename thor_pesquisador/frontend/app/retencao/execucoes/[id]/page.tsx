"use client";
import { useParams } from "next/navigation";
import { ConformidadeDetail } from "@/components/conformidade-detail";
export default function Page(){
  const {id}=useParams<{id:string;}>();
  return <ConformidadeDetail tipo="execucoes" id={id}/>;
}
