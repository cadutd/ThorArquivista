"use client";
import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { createImagem, updateImagem, uploadImagem, type Imagem, type ImagemPayload } from "@/lib/imagens";

const initial:ImagemPayload={titulo:"",descricao:null,tipo_referencia:"URL",uri:"",thumbnail_uri:null,manifest_iiif_uri:null,direitos_acesso:"INTERNO",metadados_json:{}};
export function ImagemForm({imagem, onSaved}: {imagem?:Imagem;onSaved:(i:Imagem)=>void|Promise<void>}) {
 const [form,setForm]=useState<ImagemPayload>(initial);
 const [file,setFile]=useState<File|null>(null);
 const [metadata,setMetadata]=useState("{}");
 const [error,setError]=useState("");
 const [saving,setSaving]=useState(false);
 const [titleError,setTitleError]=useState("");
 useEffect(()=>{if(imagem){setForm({titulo:imagem.titulo,descricao:imagem.descricao,tipo_referencia:imagem.tipo_referencia,uri:imagem.uri,thumbnail_uri:imagem.thumbnail_uri,manifest_iiif_uri:imagem.manifest_iiif_uri,direitos_acesso:imagem.direitos_acesso,metadados_json:imagem.metadados_json});setMetadata(JSON.stringify(imagem.metadados_json,null,2));}},[imagem]);
 function set<K extends keyof ImagemPayload>(key:K,value:ImagemPayload[K]){setForm(f=>({...f,[key]:value}));}
 async function save(e:React.FormEvent){
  e.preventDefault();setError("");setTitleError("");
  if(!form.titulo.trim()){setTitleError("Informe o titulo da imagem.");return;}
  setSaving(true);
  try{
   const meta=JSON.parse(metadata);
   if(!meta||Array.isArray(meta)||typeof meta!=="object") throw new Error("Metadados devem ser um objeto JSON.");
   let result:Imagem;
   if(form.tipo_referencia==="UPLOAD"&&!imagem){
    if(!file) throw new Error("Selecione um arquivo.");
    const data=new FormData();data.set("arquivo",file);data.set("titulo",form.titulo.trim());data.set("direitos_acesso",form.direitos_acesso);
    if(form.descricao)data.set("descricao",form.descricao);
    data.set("metadados_json",JSON.stringify(meta));
    result=await uploadImagem(data);
   }else{
    const payload={...form,titulo:form.titulo.trim(),uri:form.tipo_referencia==="UPLOAD"?null:form.uri||null,thumbnail_uri:form.tipo_referencia==="UPLOAD"?null:form.thumbnail_uri||null,manifest_iiif_uri:form.tipo_referencia==="UPLOAD"?null:form.manifest_iiif_uri||null,metadados_json:meta};
    if(imagem){
     const {tipo_referencia,...data}=payload;
     result=await updateImagem(imagem.id,data as Omit<ImagemPayload,"tipo_referencia">);
    }else result=await createImagem(payload as ImagemPayload);
   }
   await onSaved(result);
  }catch(e){setError(e instanceof Error?e.message:"Falha ao salvar imagem.");}
  finally{setSaving(false);}
 }
 return <form className="stack" onSubmit={save}>
  <div className="grid">
   <label className="field"><span>Titulo *</span><input className="input" required maxLength={255} value={form.titulo} onChange={e=>set("titulo",e.target.value)}/>{titleError&&<span className="error">{titleError}</span>}</label>
   <label className="field"><span>Tipo de referencia *</span><select className="select" disabled={!!imagem||saving} value={form.tipo_referencia} onChange={e=>set("tipo_referencia",e.target.value as ImagemPayload["tipo_referencia"])}><option value="URL">URL externa</option><option value="UPLOAD">Upload</option><option value="IIIF">Manifest IIIF</option><option value="REPOSITORIO_EXTERNO">Repositorio externo</option></select></label>
   <label className="field"><span>Direitos de acesso *</span><select className="select" value={form.direitos_acesso} onChange={e=>set("direitos_acesso",e.target.value as ImagemPayload["direitos_acesso"])}><option value="INTERNO">Interno</option><option value="RESTRITO">Restrito</option><option value="PUBLICO">Publico</option></select></label>
  </div>
  <label className="field"><span>Descricao</span><textarea className="textarea" value={form.descricao||""} onChange={e=>set("descricao",e.target.value||null)}/></label>
  {form.tipo_referencia==="UPLOAD" ? !imagem&&<label className="field"><span>Arquivo *</span><input className="input" type="file" accept="image/jpeg,image/png,image/tiff,image/webp" required onChange={e=>setFile(e.target.files?.[0]||null)}/></label> :
   <div className="grid">
    <label className="field"><span>{form.tipo_referencia==="IIIF"?"Manifest IIIF *":"URL *"}</span><input className="input" type="url" required value={(form.tipo_referencia==="IIIF"?form.manifest_iiif_uri:form.uri)||""} onChange={e=>set(form.tipo_referencia==="IIIF"?"manifest_iiif_uri":"uri",e.target.value)}/></label>
    <label className="field"><span>URL da miniatura</span><input className="input" type="url" value={form.thumbnail_uri||""} onChange={e=>set("thumbnail_uri",e.target.value||null)}/></label>
   </div>}
  <label className="field"><span>Metadados JSON</span><textarea className="textarea" value={metadata} onChange={e=>setMetadata(e.target.value)}/></label>
  {error&&<p className="error" role="alert">{error}</p>}
  <div><button className="button" disabled={saving} type="submit"><Save size={16}/>{saving?"Salvando...":"Salvar"}</button></div>
 </form>;
}
