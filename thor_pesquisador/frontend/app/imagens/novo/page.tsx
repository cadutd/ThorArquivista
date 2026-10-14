"use client";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { Permission } from "@/components/permission";
import { AppShell } from "@/components/app-shell";
import { ImagemForm } from "@/components/imagem-form";
import { vincularImagem } from "@/lib/imagens";
export default function NovaImagem(){
 const router=useRouter();
 return <AppShell><Permission acao="imagens_incluir" anyScope><div className="stack"><div className="row"><div className="page-heading"><h1>Nova imagem</h1></div><Link className="button secondary" href="/imagens"><ArrowLeft size={16}/>Voltar</Link></div><section className="panel"><ImagemForm onSaved={async imagem=>{const p=new URLSearchParams(window.location.search);const i=p.get("instrumento"),r=p.get("registro");if(i&&r){await vincularImagem(i,r,imagem.id);router.push("/instrumentos/"+i+"/registros/"+encodeURIComponent(r)+"?aba=imagens");}else router.push("/imagens");}}/></section></div></Permission></AppShell>;
}
