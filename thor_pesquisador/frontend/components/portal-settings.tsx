"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { ArrowLeft,RotateCcw,Save,X } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission,usePermission } from "./permission";
import { ApiError,request } from "@/lib/api";
import { Colors,PortalConfig,defaults,presets,portalStyle } from "@/lib/portal";
import { colorErrors } from "@/lib/portal-colors.mjs";

const labels:Record<keyof Colors,string>={primaria:"Primaria",secundaria:"Secundaria",destaque:"Destaque",fundo:"Fundo",texto:"Texto"};
export function PortalSettings(){return <AppShell><Permission acao="portal_configuracao_consultar"><Settings/></Permission></AppShell>;}
function Settings(){
  const canEdit=usePermission("portal_configuracao_editar");
  const [form,setForm]=useState<PortalConfig>(defaults),[saved,setSaved]=useState<PortalConfig>(defaults);
  const [loading,setLoading]=useState(true),[loaded,setLoaded]=useState(false),[saving,setSaving]=useState(false),[error,setError]=useState(""),[notice,setNotice]=useState("");
  const [errors,setErrors]=useState<Record<string,string>>({});
  useEffect(()=>{
    let live=true;
    request<PortalConfig>("/publico/configuracao/administracao").then(r=>{if(live){setForm(r);setSaved(r);setLoaded(true);}}).catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[]);
  async function save(e:React.FormEvent){
    e.preventDefault();if(saving)return;
    const invalid=colorErrors(form.cores);
    if(Object.keys(invalid).length){setErrors(invalid);setError("Revise as cores indicadas.");return;}
    setSaving(true);setError("");setNotice("");setErrors({});
    try {
      const result=await request<PortalConfig>("/publico/configuracao/administracao",{method:"PUT",body:JSON.stringify({...form,nome_instituicao:form.nome_instituicao.trim()})});
      setForm(result);setSaved(result);setNotice("Configuracao salva.");
    } catch(e){
      if(e instanceof ApiError&&Array.isArray(e.detail))setErrors(Object.fromEntries(e.detail.map(v=>[v.loc?.slice(1).join("."),v.msg])));
      setError(e instanceof Error?e.message:"Falha ao salvar.");
    } finally{setSaving(false);}
  }
  return <div className="stack">
    <div className="row"><div className="page-heading"><h1>Configuracao do Portal</h1></div>
      <Link className="button secondary" href="/"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="panel stack">
      {loading&&<p role="status">Carregando...</p>}
      {loaded&&<form className="stack" onSubmit={save}>
        <fieldset className="stack conformidade-fields" disabled={saving||!canEdit}>
          <div className="grid">
            <label className="field"><span>Nome da instituicao *</span><input className="input" required minLength={3} maxLength={150} value={form.nome_instituicao} onChange={e=>setForm({...form,nome_instituicao:e.target.value})}/>{errors.nome_instituicao&&<small className="error">{errors.nome_instituicao}</small>}</label>
            <div className="field"><label htmlFor="portal-preset">Paleta</label><select id="portal-preset" className="select" value={Object.keys(presets).find(name=>(Object.keys(labels) as (keyof Colors)[]).every(key=>presets[name][key]===form.cores[key]))||""} onChange={e=>{if(presets[e.target.value])setForm({...form,cores:{...presets[e.target.value]}});}}>
              <option value="">Personalizada</option>{Object.keys(presets).map(name=><option key={name}>{name}</option>)}</select></div>
          </div>
          <div className="grid">{(Object.keys(labels) as (keyof Colors)[]).map(key=><div className="field" key={key}>
            <label htmlFor={"color-"+key}>{labels[key]} *</label><div className="portal-color-field">
              <input type="color" aria-label={"Selecionar cor "+labels[key]} value={/^#[0-9a-f]{6}$/i.test(form.cores[key])?form.cores[key]:"#000000"} onChange={e=>setForm({...form,cores:{...form.cores,[key]:e.target.value}})}/>
              <input className="input" id={"color-"+key} aria-label={labels[key]} required pattern="#[0-9a-fA-F]{6}" maxLength={7} value={form.cores[key]} aria-invalid={!!errors["cores."+key]} onChange={e=>setForm({...form,cores:{...form.cores,[key]:e.target.value}})}/></div>
            {errors["cores."+key]&&<small className="error">{errors["cores."+key]}</small>}
          </div>)}</div>
        </fieldset>
        <section className="stack"><h2>Previa</h2><div className="portal portal-preview stack" style={portalStyle(form.cores)}>
          <h3>{form.nome_instituicao||"Instituicao"}</h3><p>Instrumentos de pesquisa</p>
          <div className="actions"><span className="button">Pesquisar</span><span className="portal-text-link">Instrumentos publicados</span></div>
        </div></section>
        {error&&<p className="error" role="alert">{error}</p>}
        {notice&&<p role="status">{notice}</p>}
        <div className="actions"><Permission acao="portal_configuracao_editar">
          <button className="button" type="submit" disabled={saving}><Save size={16}/>{saving?"Salvando...":"Salvar configuracao"}</button>
          <button className="button secondary" type="button" disabled={saving} onClick={()=>{if(window.confirm("Restaurar as cores padrao?")){setForm({...form,cores:{...defaults.cores}});setNotice("");}}}><RotateCcw size={16}/>Restaurar padrao</button>
        </Permission>
          <button className="button secondary" type="button" disabled={saving} onClick={()=>{setForm(saved);setErrors({});setError("");setNotice("");}}><X size={16}/>Cancelar</button>
        </div>
      </form>}
      {!loaded&&error&&<p className="error" role="alert">{error}</p>}
    </section>
  </div>;
}
