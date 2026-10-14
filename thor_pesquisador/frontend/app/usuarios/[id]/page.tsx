"use client";
import { useParams } from "next/navigation";
import { UsuarioAcessos } from "@/components/usuario-acessos";
export default function Page() {const {id}=useParams<{id:string}>();return <UsuarioAcessos id={id} readonly/>;}
