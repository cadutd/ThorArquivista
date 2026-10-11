"use client";
import Link from "next/link";
import { ArrowLeft,Edit,Eye,Image as ImageIcon } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect,useState } from "react";
import { AppShell } from "@/components/app-shell";
import { MediaPreview } from "@/components/media-preview";
import { getImagem,mediaUrl,type Imagem } from "@/lib/imagens";
import { me } from "@/lib/api";
export default function ImagemDetail(){
 const {id}=useParams<{id:string}>();const [imagem,setImagem]=useState<Imagem>();const [error,setError]=useState("");const [preview,setPreview]=useState(false);const [usuario,setUsuario]=useState("");
 useEffect(()=>{getImagem(id).then(setImagem).catch(e=>setError(e.message));me().then(u=>setUsuario(u.id)).catch(()=>{});},[id]);
 return <AppShell><div className="stack"><div className="row"><div className="page-heading"><h1>{imagem?.titulo||"Imagem"}</h1></div><div className="actions"><Link className="button secondary" href="/imagens"><ArrowLeft size={16}/>Voltar</Link>{imagem?.criado_por===usuario&&<Link className="button" href={"/imagens/"+id+"/editar"}><Edit size={16}/>Editar</Link>}</div></div>
 {error?<p className="error">{error}</p>:!imagem?<p className="muted">Carregando...</p>:<section className="panel stack">
  <div className="row"><div className="image-title">{imagem.thumbnail_uri?<img className="image-thumb" src={mediaUrl(imagem.thumbnail_uri)} alt={imagem.titulo}/>:<ImageIcon size={28}/>}<span>{imagem.tipo_referencia} | {imagem.direitos_acesso}</span></div><button className="button secondary" onClick={()=>setPreview(true)}><Eye size={16}/>Visualizar imagem</button></div>
  <p>{imagem.descricao||"-"}</p><div className="detail-grid">{Object.entries({MIME:imagem.mime_type,Tamanho:imagem.tamanho_bytes?imagem.tamanho_bytes+" bytes":null,Dimensoes:imagem.largura?imagem.largura+" x "+imagem.altura:null,"Criado em":new Date(imagem.criado_em).toLocaleString("pt-BR")}).map(([label,value])=><div className="detail-item" key={label}><span>{label}</span><strong>{value||"-"}</strong></div>)}</div>
  <div className="detail-item"><span>Referencia</span><a className="record-link" href={mediaUrl(imagem.uri)} target="_blank" rel="noopener noreferrer">{imagem.tipo_referencia==="UPLOAD"?"Arquivo armazenado":imagem.uri}</a></div><div className="detail-item"><span>SHA-256</span><code className="break-text">{imagem.checksum_sha256||"-"}</code></div><div className="detail-item"><span>Metadados</span><pre className="break-text">{JSON.stringify(imagem.metadados_json,null,2)}</pre></div>
 </section>}
 {preview&&imagem&&<MediaPreview imagem={imagem} onClose={()=>setPreview(false)}/>}
 </div></AppShell>;
}
