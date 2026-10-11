"use client";
import Link from "next/link";
import { Eye,Edit,Trash2,Plus,Search,SlidersHorizontal,Image as ImageIcon } from "lucide-react";
import { useEffect,useState } from "react";
import { AppShell } from "@/components/app-shell";
import { CrudPagination } from "@/components/crud-pagination";
import { listImagens,deleteImagem,mediaUrl,type Imagem } from "@/lib/imagens";
import { me } from "@/lib/api";

export default function ImagensPage(){
 const [items,setItems]=useState<Imagem[]>([]);const [total,setTotal]=useState(0);const [pageIndex,setPageIndex]=useState(0);const [pageSize,setPageSize]=useState(20);
 const [draft,setDraft]=useState({q:"",tipo:"",direitos:""});const [filters,setFilters]=useState(draft);const [advanced,setAdvanced]=useState(false);
 const [error,setError]=useState("");const [loading,setLoading]=useState(false);const [usuario,setUsuario]=useState("");
 useEffect(()=>{me().then(u=>setUsuario(u.id)).catch(()=>{});},[]);
 async function load(){setLoading(true);try{const result=await listImagens({...filters,limit:String(pageSize),offset:String(pageIndex*pageSize)});setItems(result.items);setTotal(result.total);setError("");}catch(e){setError(e instanceof Error?e.message:"Falha ao carregar.");}finally{setLoading(false);}}
 useEffect(()=>{load();},[filters,pageIndex,pageSize]);
 async function remove(item:Imagem){if(!window.confirm('Excluir a imagem "'+item.titulo+'"?'))return;setLoading(true);try{await deleteImagem(item.id);if(items.length===1&&pageIndex>0)setPageIndex(pageIndex-1);else await load();}catch(e){setError(e instanceof Error?e.message:"Falha ao excluir.");}finally{setLoading(false);}}
 const pagination={total,pageIndex,pageSize,loading,onPageChange:setPageIndex,onPageSizeChange:(n:number)=>{setPageSize(n);setPageIndex(0);}};
 return <AppShell><div className="stack"><div className="row"><div className="page-heading"><h1>Imagens</h1><p>{total} imagens encontradas</p></div><Link className="button" href="/imagens/novo"><Plus size={16}/>Nova imagem</Link></div>
  <section className="panel stack">
   <form className="stack" onSubmit={e=>{e.preventDefault();setFilters(draft);setPageIndex(0);}}>
    <div className="row"><label className="field search-field"><span>Busca simples</span><input className="input" value={draft.q} onChange={e=>setDraft({...draft,q:e.target.value})}/></label><div className="actions"><button className="button" disabled={loading}><Search size={16}/>Buscar</button><button className="icon-button" type="button" title="Busca avancada" aria-expanded={advanced} onClick={()=>setAdvanced(!advanced)}><SlidersHorizontal size={16}/></button><button className="button secondary" type="button" disabled={loading} onClick={()=>{const empty={q:"",tipo:"",direitos:""};setDraft(empty);setFilters(empty);setPageIndex(0);}}>Limpar filtros</button></div></div>
    {advanced&&<div className="grid"><label className="field"><span>Tipo de referencia</span><select className="select" value={draft.tipo} onChange={e=>setDraft({...draft,tipo:e.target.value})}><option value="">Todos</option>{["UPLOAD","URL","IIIF","REPOSITORIO_EXTERNO"].map(v=><option key={v}>{v}</option>)}</select></label><label className="field"><span>Direitos de acesso</span><select className="select" value={draft.direitos} onChange={e=>setDraft({...draft,direitos:e.target.value})}><option value="">Todos</option>{["PUBLICO","INTERNO","RESTRITO"].map(v=><option key={v}>{v}</option>)}</select></label></div>}
   </form>
   {error&&<p className="error" role="alert">{error}</p>}
   <CrudPagination {...pagination}/>
   <div className="table-wrap"><table className="table"><thead><tr><th>Imagem</th><th>Referencia</th><th>Acesso</th><th>Criado em</th><th>Acoes</th></tr></thead><tbody>{items.map(i=><tr key={i.id}><td><div className="image-title">{i.thumbnail_uri?<img className="image-thumb" src={mediaUrl(i.thumbnail_uri)} alt="" loading="lazy"/>:<ImageIcon size={28}/>}<span>{i.titulo}</span></div></td><td>{i.tipo_referencia}</td><td>{i.direitos_acesso}</td><td>{new Date(i.criado_em).toLocaleDateString("pt-BR")}</td><td><div className="actions"><Link className="icon-button" title="Visualizar" aria-label="Visualizar" href={"/imagens/"+i.id}><Eye size={16}/></Link>{i.criado_por===usuario&&<><Link className="icon-button" title="Editar" aria-label="Editar" href={"/imagens/"+i.id+"/editar"}><Edit size={16}/></Link><button className="icon-button danger" title="Excluir" aria-label="Excluir" disabled={loading} onClick={()=>remove(i)}><Trash2 size={16}/></button></>}</div></td></tr>)}{!items.length&&<tr><td colSpan={5} className="muted">{loading?"Carregando...":error?"Listagem indisponivel.":"Nenhuma imagem encontrada."}</td></tr>}</tbody></table></div>
   <CrudPagination {...pagination}/>
  </section>
 </div></AppShell>;
}
