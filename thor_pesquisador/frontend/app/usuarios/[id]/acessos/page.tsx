"use client";
import { useParams } from "next/navigation";
import { UsuarioEscopos } from "@/components/usuario-escopos";
export default function Page() {const {id}=useParams<{id:string}>();return <UsuarioEscopos id={id}/>;}
