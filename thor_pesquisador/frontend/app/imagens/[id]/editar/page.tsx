"use client";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect,useState } from "react";
import { Permission } from "@/components/permission";
import { AppShell } from "@/components/app-shell";
import { ImagemForm } from "@/components/imagem-form";
import { getImagem,type Imagem } from "@/lib/imagens";
export default function EditarImagem(){
 const {id}=useParams<{id:string}>();const router=useRouter();
 const [imagem,setImagem]=useState<Imagem>();const [error,setError]=useState("");
 useEffect(()=>{getImagem(id).then(setImagem).catch(e=>setError(e.message));},[id]);
 return <AppShell><Permission acao="imagens_editar" anyScope><div className="stack"><div className="row"><div className="page-heading"><h1>Editar imagem</h1></div><Link className="button secondary" href="/imagens"><ArrowLeft size={16}/>Voltar</Link></div><section className="panel">{error?<p className="error">{error}</p>:imagem?<ImagemForm imagem={imagem} onSaved={()=>router.push("/imagens")}/>:<p className="muted">Carregando...</p>}</section></div></Permission></AppShell>;
}
