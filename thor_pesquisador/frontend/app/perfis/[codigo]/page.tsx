"use client";
import { useParams } from "next/navigation";
import { AdministracaoList } from "@/components/administracao-list";
export default function Page() {const {codigo}=useParams<{codigo:string}>();return <AdministracaoList tipo="perfis" perfilInicial={codigo}/>;}
