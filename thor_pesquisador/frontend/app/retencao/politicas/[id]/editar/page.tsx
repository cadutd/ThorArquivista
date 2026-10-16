"use client";
import { useParams } from "next/navigation";
import { PoliticaEditor } from "@/components/conformidade-editor";
export default function Page(){const {id}=useParams<{id:string}>();return <PoliticaEditor id={id}/>;}
