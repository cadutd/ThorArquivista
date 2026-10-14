"use client";
import { useParams } from "next/navigation";
import { PerfilEditor } from "@/components/perfil-editor";
export default function Page() {const {codigo}=useParams<{codigo:string}>();return <PerfilEditor codigo={codigo}/>;}
