"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect,useRef,useState } from "react";
import { ArrowLeft,Save } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { InstrumentoLookup } from "./instrumento-lookup";
import { ApiError,request } from "@/lib/api";
import { categories,Policy } from "@/lib/conformidade";

const empty:Policy={id:"",nome:"",categoria:"LOG_TECNICO",dias:30,instrumento_id:null,ativo:true,permitir_expurgo:false,bloqueada:false};

export function PoliticaEditor({id}:{id?:string}) {
  const router=useRouter(),[data,setData]=useState<Policy>(empty),[name,setName]=useState("");
  const [loaded,setLoaded]=useState(!id),[error,setError]=useState(""),[saving,setSaving]=useState(false);
  const [errors,setErrors]=useState<Record<string,string>>({});
  useEffect(()=>{
    let live=true;setLoaded(!id);setError("");setData(empty);setName("");setErrors({});
    if(id) request<Policy>("/retencao/politicas/"+id).then(p=>{if(live){setData(p);setName(p.instrumento_nome||"");setLoaded(true);}})
      .catch(e=>{if(live)setError(e.message);});
    return()=>{live=false;};
  },[id]);
  async function save(){
    if(saving)return;
    if(data.nome.trim().length<3){setErrors({nome:"Informe um nome com pelo menos 3 caracteres."});return;}
    if(data.categoria==="REGISTRO_EXCLUIDO"&&!data.instrumento_id){setErrors({instrumento_id:"Selecione um instrumento."});return;}
    setSaving(true);setError("");setErrors({});
    try {
      const {id:_,instrumento_nome:_name,...values}=data;
      const payload={...values,nome:values.nome.trim()};
      await request("/retencao/politicas"+(id?"/"+id:""),{method:id?"PUT":"POST",body:JSON.stringify(payload)});
      router.push("/retencao/politicas");
    } catch(e) {
      if(e instanceof ApiError&&Array.isArray(e.detail)) setErrors(Object.fromEntries(e.detail.map(v=>[v.loc?.[1],v.msg])));
      setError(e instanceof Error?e.message:"Falha ao salvar.");
    } finally{setSaving(false);}
  }
  return <AppShell><Permission acao={id?"retencao_editar":"retencao_incluir"} anyScope><div className="stack">
    <div className="row"><div className="page-heading"><h1>{id?"Editar politica":"Nova politica"}</h1></div><Link className="button secondary" href="/retencao/politicas"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="panel stack">
      {!loaded&&!error&&<p role="status">Carregando...</p>}
      {loaded&&<form className="stack" onSubmit={e=>{e.preventDefault();save();}}>
        <fieldset className="stack conformidade-fields" disabled={saving}><div className="grid">
          <label className="field"><span>Nome <span className="administracao-required">*</span></span><input className="input" required minLength={3} maxLength={150} value={data.nome} aria-invalid={!!errors.nome} onChange={e=>setData({...data,nome:e.target.value})}/>{errors.nome&&<span className="error">{errors.nome}</span>}</label>
          <label className="field"><span>Categoria <span className="administracao-required">*</span></span><select className="select" required disabled={!!id} value={data.categoria} onChange={e=>setData({...data,categoria:e.target.value,instrumento_id:null})}>{Object.entries(categories).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
          <label className="field"><span>Prazo em dias <span className="administracao-required">*</span></span><input className="input" required type="number" min={1} max={36500} value={data.dias} aria-invalid={!!errors.dias} onChange={e=>setData({...data,dias:Number(e.target.value)})}/>{errors.dias&&<span className="error">{errors.dias}</span>}</label>
          <label className="checkbox-field"><input type="checkbox" checked={data.ativo} onChange={e=>setData({...data,ativo:e.target.checked})}/>Politica ativa</label>
          <label className="checkbox-field"><input type="checkbox" checked={data.permitir_expurgo} onChange={e=>setData({...data,permitir_expurgo:e.target.checked})}/>Autorizar expurgo definitivo</label>
          <label className="checkbox-field"><input type="checkbox" checked={data.bloqueada} onChange={e=>setData({...data,bloqueada:e.target.checked})}/>Bloquear execucoes</label>
        </div>
        {data.categoria==="REGISTRO_EXCLUIDO"&&<><InstrumentoLookup required disabled={!!id} value={data.instrumento_id||""} label={name} acao={id?"retencao_editar":"retencao_incluir"} onChange={(value,label)=>{setData({...data,instrumento_id:value||null});setName(label);}}/>{errors.instrumento_id&&<p className="error">{errors.instrumento_id}</p>}</>}
        </fieldset><div className="actions"><button className="button" disabled={saving}><Save size={16}/>{saving?"Salvando...":"Salvar politica"}</button></div>
      </form>}{error&&<p className="error" role="alert">{error}</p>}
    </section>
  </div></Permission></AppShell>;
}

export function ExportacaoEditor() {
  const router=useRouter(),[instrument,setInstrument]=useState(""),[name,setName]=useState("");
  const [format,setFormat]=useState("JSON"),[scope,setScope]=useState("ADMINISTRATIVO");
  const [saving,setSaving]=useState(false),[error,setError]=useState("");
  const operation=useRef("");
  useEffect(()=>{operation.current=crypto.randomUUID();},[]);
  async function save(){
    if(saving)return;
    if(!instrument){setError("Selecione um instrumento.");return;}
    setSaving(true);setError("");
    try {
      await request("/instrumentos/"+instrument+"/exportacoes",{method:"POST",body:JSON.stringify({
        operacao_id:operation.current,formato:format,escopo:scope})});
      router.push("/exportacoes");
    } catch(e){setError(e instanceof Error?e.message:"Falha ao solicitar.");}
    finally{setSaving(false);}
  }
  return <AppShell><Permission acao="exportacoes_incluir" anyScope><div className="stack">
    <div className="row"><div className="page-heading"><h1>Nova exportacao</h1></div><Link className="button secondary" href="/exportacoes"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="panel stack">
      <form className="stack" onSubmit={e=>{e.preventDefault();save();}}>
        <fieldset className="stack conformidade-fields" disabled={saving}>
          <InstrumentoLookup required value={instrument} label={name} acao="exportacoes_incluir" onChange={(value,label)=>{setInstrument(value);setName(label);operation.current=crypto.randomUUID();}}/>
          <div className="grid">
            <label className="field"><span>Escopo <span className="administracao-required">*</span></span><select className="select" required value={scope} onChange={e=>{setScope(e.target.value);if(e.target.value!=="PUBLICADO"&&format==="PACOTE")setFormat("JSON");operation.current=crypto.randomUUID();}}><option value="ADMINISTRATIVO">Dados administrativos</option><option value="PUBLICADO">Publicacao vigente</option></select></label>
            <label className="field"><span>Formato <span className="administracao-required">*</span></span><select className="select" required value={format} onChange={e=>{setFormat(e.target.value);operation.current=crypto.randomUUID();}}><option value="JSON">JSON</option><option value="CSV">CSV</option>{scope==="PUBLICADO"&&<option value="PACOTE">Pacote de publicacao</option>}</select></label>
          </div>
        </fieldset>{error&&<p className="error" role="alert">{error}</p>}<div className="actions"><button className="button" disabled={saving}><Save size={16}/>{saving?"Solicitando...":"Solicitar exportacao"}</button></div>
      </form>
    </section>
  </div></Permission></AppShell>;
}
