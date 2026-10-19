"use client";
import { useState } from "react";
import { ImagePlus,Trash2 } from "lucide-react";
import { imageRequest } from "@/lib/imagens";
import { InstrumentoCardImage } from "./instrumento-card-image";

export function InstrumentoCoverField({value,onChange,onBusy,instrumentoId,disabled}:{
  value?:string|null;onChange:(id:string|null)=>void;onBusy:(value:boolean)=>void;instrumentoId?:string;disabled?:boolean;
}) {
  const [error,setError]=useState("");
  async function upload(file?:File) {
    if(!file)return;
    setError("");onBusy(true);
    try {
      const data=new FormData();data.set("arquivo",file);
      if(instrumentoId)data.set("instrumento_id",instrumentoId);
      const result=await imageRequest<{id:string}>("/instrumentos/imagens-card",{method:"POST",body:data});
      onChange(result.id);
    }catch(e){setError(e instanceof Error?e.message:"Falha ao enviar imagem.");}
    finally{onBusy(false);}
  }
  return <div className="field stack">
    <label className="field"><span>Imagem do card</span><input key={value||"padrao"} className="input" type="file"
      accept="image/jpeg,image/png,image/webp,image/tiff" disabled={disabled}
      onChange={e=>void upload(e.target.files?.[0])}/></label>
    <div className="instrumento-cover-preview"><InstrumentoCardImage src={value?"/instrumentos/imagens-card/"+value:null}/></div>
    <div className="actions"><ImagePlus size={16}/><span className="muted">960 x 540</span>
      {value&&<button className="icon-button danger" type="button" title="Remover imagem do card" aria-label="Remover imagem do card"
        disabled={disabled} onClick={()=>{if(window.confirm("Remover a imagem do card?"))onChange(null);}}><Trash2 size={16}/></button>}</div>
    {error&&<p className="error" role="alert">{error}</p>}
  </div>;
}
