"use client";
import { useParams } from "next/navigation";
import { AcessoEditor } from "@/components/acesso-editor";
export default function ViewAccess() { const {id} = useParams<{id: string}>(); return <AcessoEditor id={id} readonly/>; }
