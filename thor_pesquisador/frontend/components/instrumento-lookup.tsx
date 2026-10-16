"use client";
import { useEffect,useState } from "react";
import { createPortal } from "react-dom";
import { Check,Search,X } from "lucide-react";
import { request } from "@/lib/api";
import { CrudPagination } from "./crud-pagination";
import { ModalFrame } from "./modal-frame";

export function InstrumentoLookup({value,label,onChange,acao,required=false,disabled=false}:{
  value:string;label?:string;onChange:(id:string,name:string)=>void;acao:string;required?:boolean;disabled?:boolean;
}) {
  const [open,setOpen]=useState(false),[draft,setDraft]=useState(""),[q,setQ]=useState("");
  const [rows,setRows]=useState<{id:string;nome:string;tipo:string}[]>([]);
  const [page,setPage]=useState(0),[size,setSize]=useState(20),[total,setTotal]=useState(0);
  const [loading,setLoading]=useState(false),[error,setError]=useState("");
  useEffect(() => {
    if(!open) return;
    let live=true;setLoading(true);
    request<{items:typeof rows;total:number}>("/conformidade/instrumentos?"+new URLSearchParams({
      acao,q,limit:String(size),offset:String(page*size)})).then(r=>{if(live){setRows(r.items);setTotal(r.total);setError("");}})
      .catch(e=>{if(live){setError(e.message);setRows([]);setTotal(0);}}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[open,q,page,size,acao]);
  const pagination={total,pageIndex:page,pageSize:size,loading,onPageChange:setPage,onPageSizeChange:(n:number)=>{setSize(n);setPage(0);}};
  return <div className="stack"><label className="field"><span>Instrumento{required&&<span className="administracao-required"> *</span>}</span>
    <div className="instrumento-lookup-control"><input className="input" aria-label="Instrumento selecionado" readOnly required={required} value={label||value}
      onClick={()=>!disabled&&setOpen(true)}/>
      <button className="icon-button" type="button" title="Pesquisar instrumento" aria-label="Pesquisar instrumento" disabled={disabled}
        onClick={()=>setOpen(true)}><Search size={16}/></button>
      {value&&<button className="icon-button" type="button" title="Limpar instrumento" aria-label="Limpar instrumento" disabled={disabled}
        onClick={()=>onChange("","")}><X size={16}/></button>}</div></label>
    {open&&createPortal(<ModalFrame title="Pesquisar instrumento" onClose={()=>setOpen(false)} className="administracao-popup">
      <div className="row"><h2>Pesquisar instrumento</h2><button className="icon-button" type="button" title="Fechar" aria-label="Fechar"
        onClick={()=>setOpen(false)}><X size={16}/></button></div>
      <form className="row" onSubmit={e=>{e.preventDefault();e.stopPropagation();setQ(draft);setPage(0);}}>
        <label className="field search-field"><span>Nome</span><input className="input" value={draft} onChange={e=>setDraft(e.target.value)}/></label>
        <button className="button" disabled={loading}><Search size={16}/>Pesquisar</button></form>
      {error&&<p role="alert" className="error">{error}</p>}<CrudPagination {...pagination}/>
      <div className="table-wrap"><table className="table"><thead><tr><th>Nome</th><th>Tipo</th><th>Acoes</th></tr></thead><tbody>
        {rows.map(i=><tr key={i.id}><td><a className="crud-record-link" href={"#"+i.id} onClick={e=>{e.preventDefault();onChange(i.id,i.nome);setOpen(false);}}>{i.nome}</a></td>
          <td>{i.tipo}</td><td><button className="icon-button" type="button" title="Selecionar" aria-label={"Selecionar "+i.nome}
            onClick={()=>{onChange(i.id,i.nome);setOpen(false);}}><Check size={16}/></button></td></tr>)}
        {!rows.length&&<tr><td colSpan={3}>{loading?"Carregando...":"Nenhum instrumento encontrado."}</td></tr>}</tbody></table></div>
      <CrudPagination {...pagination}/>
    </ModalFrame>,document.body)}
  </div>;
}
