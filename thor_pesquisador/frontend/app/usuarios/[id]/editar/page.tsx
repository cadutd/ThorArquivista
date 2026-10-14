"use client";
import { useParams } from "next/navigation";
import { UsuarioEditor } from "@/components/usuario-editor";
export default function Page() {const {id}=useParams<{id:string}>();return <UsuarioEditor id={id}/>;}
