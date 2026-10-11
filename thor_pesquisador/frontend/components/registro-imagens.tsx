"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { ArrowLeft,ArrowRight,ChevronLeft,ChevronRight,Eye,Image as ImageIcon,Plus,Save,Search,Star,Unlink,X } from "lucide-react";
import { listImagens,listVinculos,vincularImagem,editarVinculo,reordenarImagens,desvincularImagem,mediaUrl,type Imagem,type VinculoImagem } from "@/lib/imagens";
import { MediaPreview } from "./media-preview";
import { ModalFrame } from "./modal-frame";

export function RegistroImagens({instrumentoId,registroId}:{instrumentoId:string;registroId:string}){
 const [items,setItems]=useState<VinculoImagem[]>([]);const [total,setTotal]=useState(0);const [offset,setOffset]=useState(0);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);const [picker,setPicker]=useState(false);const [preview,setPreview]=useState<Imagem>();
 async function load(){setBusy(true);try{const p=await listVinculos(instrumentoId,registroId,offset);setItems(p.items);setTotal(p.total);setError("");}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar imagens.");}finally{setBusy(false);}}
 useEffect(()=>{load();},[instrumentoId,registroId,offset]);
 async function mutate(action:()=>Promise<unknown>){setBusy(true);try{await action();await load();}catch(e){setError(e instanceof Error?e.message:"Falha ao alterar imagens.");}finally{setBusy(false);}}
 function move(index:number,delta:number){const a=items[index],b=items[index+delta];if(b)mutate(()=>reordenarImagens(instrumentoId,registroId,[{imagem_id:a.imagem_id,ordem:b.ordem},{imagem_id:b.imagem_id,ordem:a.ordem}]));}
 const pageControls=<div className="pagination"><span className="muted">{total?offset+1:0}-{Math.min(total,offset+20)} de {total}</span><div className="actions"><button className="icon-button" title="Pagina anterior" disabled={busy||offset===0} onClick={()=>setOffset(offset-20)}><ChevronLeft size={16}/></button><button className="icon-button" title="Proxima pagina" disabled={busy||offset+20>=total} onClick={()=>setOffset(offset+20)}><ChevronRight size={16}/></button></div></div>;
 return <section className="stack"><div className="row"><h2>Imagens</h2><div className="actions"><button className="button secondary" disabled={busy} onClick={()=>setPicker(true)}><Search size={16}/>Vincular imagem</button><Link className="button" href={"/imagens/novo?"+new URLSearchParams({instrumento:instrumentoId,registro:registroId})}><Plus size={16}/>Nova imagem</Link></div></div>
 {error&&<p className="error" role="alert">{error}</p>}{pageControls}
 <div className="image-gallery">{items.map((v,index)=><ImageTile key={v.imagem_id} v={v} busy={busy} canLeft={index>0} canRight={index<items.length-1} preview={()=>setPreview(v.imagem)} move={delta=>move(index,delta)} update={payload=>mutate(()=>editarVinculo(instrumentoId,registroId,v.imagem_id,payload))} remove={()=>{if(window.confirm("Remover o vinculo desta imagem?"))mutate(async()=>{await desvincularImagem(instrumentoId,registroId,v.imagem_id);if(items.length===1&&offset>0)setOffset(offset-20);});}}/>)}</div>
 {!items.length&&<p className="muted">{busy?"Carregando...":error?"Galeria indisponivel.":"Nenhuma imagem vinculada."}</p>}{pageControls}
 {picker&&<ImagePicker close={()=>setPicker(false)} select={async i=>{await vincularImagem(instrumentoId,registroId,i.id);setPicker(false);await load();}}/>}
 {preview&&<MediaPreview imagem={preview} onClose={()=>setPreview(undefined)}/>}
 </section>;
}
function ImageTile({v,busy,canLeft,canRight,preview,move,update,remove}:{v:VinculoImagem;busy:boolean;canLeft:boolean;canRight:boolean;preview:()=>void;move:(d:number)=>void;update:(p:{legenda?:string|null;principal?:boolean})=>void;remove:()=>void}){
 const [legenda,setLegenda]=useState(v.legenda||"");
 useEffect(()=>setLegenda(v.legenda||""),[v.legenda]);
 return <article className="image-tile"><button className="thumbnail-button" title="Visualizar imagem" onClick={preview}>{v.imagem.thumbnail_uri?<img src={mediaUrl(v.imagem.thumbnail_uri)} alt={v.imagem.titulo} loading="lazy"/>:<ImageIcon size={40}/>}</button>
 <strong>{v.imagem.titulo}</strong><span className="muted">{v.imagem.tipo_referencia} | {v.imagem.direitos_acesso}</span>
 <label className="field"><span>Legenda</span><input className="input" value={legenda} maxLength={4000} disabled={busy} onChange={e=>setLegenda(e.target.value)}/></label>
 <div className="actions">
 <button className="icon-button" title="Salvar legenda" aria-label="Salvar legenda" disabled={busy} onClick={()=>update({legenda:legenda||null})}><Save size={16}/></button>
 <button className="icon-button" title={v.principal?"Remover imagem principal":"Marcar como principal"} aria-pressed={v.principal} disabled={busy} onClick={()=>update({principal:!v.principal})}><Star size={16} fill={v.principal?"currentColor":"none"}/></button>
 <button className="icon-button" title="Mover para esquerda" disabled={busy||!canLeft} onClick={()=>move(-1)}><ArrowLeft size={16}/></button>
 <button className="icon-button" title="Mover para direita" disabled={busy||!canRight} onClick={()=>move(1)}><ArrowRight size={16}/></button>
 <button className="icon-button" title="Visualizar imagem" onClick={preview}><Eye size={16}/></button>
 <button className="icon-button danger" title="Remover vinculo" aria-label="Remover vinculo" disabled={busy} onClick={remove}><Unlink size={16}/></button>
 </div></article>;
}
function ImagePicker({close,select}:{close:()=>void;select:(i:Imagem)=>Promise<void>}){
 const [items,setItems]=useState<Imagem[]>([]);const [total,setTotal]=useState(0);const [page,setPage]=useState(0);const [draft,setDraft]=useState("");const [q,setQ]=useState("");const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 useEffect(()=>{setBusy(true);listImagens({q,limit:"10",offset:String(page*10)}).then(p=>{setItems(p.items);setTotal(p.total);}).catch(e=>setError(e.message)).finally(()=>setBusy(false));},[q,page]);
 async function choose(i:Imagem){setBusy(true);try{await select(i);}catch(e){setError(e instanceof Error?e.message:"Falha ao vincular.");setBusy(false);}}
 return <ModalFrame title="Selecionar imagem" onClose={close}><div className="row"><h2>Selecionar imagem</h2><button autoFocus className="icon-button" title="Fechar" onClick={close}><X size={16}/></button></div>
 <form className="row" onSubmit={e=>{e.preventDefault();setQ(draft);setPage(0);}}><label className="field search-field"><span>Buscar imagem</span><input className="input" value={draft} onChange={e=>setDraft(e.target.value)}/></label><button className="button" disabled={busy}><Search size={16}/>Buscar</button></form>
 {error&&<p className="error">{error}</p>}<div className="table-wrap"><table className="table"><thead><tr><th>Titulo</th><th>Referencia</th><th>Acesso</th><th>Acao</th></tr></thead><tbody>{items.map(i=><tr key={i.id}><td>{i.titulo}</td><td>{i.tipo_referencia}</td><td>{i.direitos_acesso}</td><td><button className="icon-button" title="Vincular imagem" aria-label="Vincular imagem" disabled={busy} onClick={()=>choose(i)}><Plus size={16}/></button></td></tr>)}{!items.length&&<tr><td colSpan={4}>{busy?"Carregando...":"Nenhuma imagem encontrada."}</td></tr>}</tbody></table></div>
 <div className="pagination"><span>{total} imagens | pagina {page+1} de {Math.max(1,Math.ceil(total/10))}</span><div className="actions"><button className="icon-button" title="Pagina anterior" disabled={busy||page===0} onClick={()=>setPage(page-1)}><ChevronLeft size={16}/></button><button className="icon-button" title="Proxima pagina" disabled={busy||(page+1)*10>=total} onClick={()=>setPage(page+1)}><ChevronRight size={16}/></button></div></div>
 </ModalFrame>;
}
