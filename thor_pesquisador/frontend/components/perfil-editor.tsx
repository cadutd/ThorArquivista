"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft,ChevronDown,RefreshCw,Save } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { ApiError,request } from "@/lib/api";

export type Perfil = {codigo:string;nome:string;descricao:string|null;ativo:boolean;permissoes:string[];sistema?:boolean};
type Permissao = {codigo:string;nome:string;modulo:string;funcao:string};
type Field = "codigo"|"nome"|"descricao";
const empty:Perfil = {codigo:"",nome:"",descricao:"",ativo:true,permissoes:[],sistema:false};

export function PerfilEditor({codigo}:{codigo?:string}) {
  const router = useRouter();
  const [data,setData] = useState<Perfil>(empty);
  const [permissions,setPermissions] = useState<Permissao[]>([]);
  const [total,setTotal] = useState(0);
  const [offset,setOffset] = useState(0);
  const [refresh,setRefresh] = useState(0);
  const [loadingPermissions,setLoadingPermissions] = useState(true);
  const [permissionsError,setPermissionsError] = useState("");
  const [loaded,setLoaded] = useState(!codigo);
  const [loadError,setLoadError] = useState("");
  const [error,setError] = useState("");
  const [fieldErrors,setFieldErrors] = useState<Partial<Record<Field,string>>>({});
  const [saving,setSaving] = useState(false);
  useEffect(() => {
    let current = true;
    setData(empty);setLoaded(!codigo);setLoadError("");setError("");setFieldErrors({});
    if(codigo) request<Perfil>("/perfis/" + encodeURIComponent(codigo))
      .then(p => {if(current) {setData(p);setLoaded(true);}})
      .catch(e => {if(current) setLoadError(e.message);});
    return () => {current = false;};
  },[codigo]);
  useEffect(() => {
    let current = true;setLoadingPermissions(true);
    request<{items:Permissao[];total:number}>("/permissoes?limit=100&offset=" + offset)
      .then(r => {if(current) {
        setPermissions(v => Array.from(new Map([...v,...r.items].map(p => [p.codigo,p])).values()));
        setTotal(r.total);setPermissionsError("");
      }}).catch(e => {if(current) setPermissionsError(e.message);})
      .finally(() => {if(current) setLoadingPermissions(false);});
    return () => {current = false;};
  },[offset,refresh]);
  function toggle(value:string) {
    setData(p => ({...p,permissoes:p.permissoes.includes(value) ? p.permissoes.filter(v => v !== value) : [...p.permissoes,value]}));
  }
  function field(key:Field,value:string) {
    setData(v => ({...v,[key]:value}));setFieldErrors(v => ({...v,[key]:""}));
  }
  function accessibility(key:Field) {
    return {name:key,"aria-invalid":!!fieldErrors[key],"aria-describedby":fieldErrors[key] ? "perfil-error-" + key : undefined};
  }
  async function save() {
    setSaving(true);setError("");setFieldErrors({});
    try {
      await request(codigo ? "/perfis/" + encodeURIComponent(codigo) : "/perfis",{
        method:codigo ? "PUT" : "POST",body:JSON.stringify({codigo:data.codigo,nome:data.nome.trim(),
          descricao:data.descricao?.trim() || null,ativo:data.ativo,permissoes:data.permissoes})});
      router.push("/perfis");
    } catch(e) {
      if(e instanceof ApiError && Array.isArray(e.detail)) {
        const errors:Partial<Record<Field,string>> = {};
        for(const item of e.detail) if(["codigo","nome","descricao"].includes(item.loc?.[1]) && typeof item.msg === "string")
          errors[item.loc[1] as Field] = item.msg;
        setFieldErrors(errors);
      }
      setError(e instanceof Error ? e.message : "Falha ao salvar perfil.");
    } finally {setSaving(false);}
  }
  return <AppShell><Permission acao={codigo ? "perfis_editar" : "perfis_incluir"}><div className="administracao-editor-page">
    <div className="row administracao-page-heading"><h1>{codigo ? "Editar perfil" : "Novo perfil"}</h1>
      <Link className="button secondary" href="/perfis"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="administracao-editor-surface">
      <header><h2>{codigo ? "Edicao" : "Cadastro"}</h2>{loaded && codigo && <p>{data.nome}</p>}</header>
      <div className="administracao-editor-content">
        {loadError && <p className="error" role="alert">{loadError}</p>}
        {!loaded && !loadError && <p className="muted" role="status">Carregando perfil...</p>}
        {loaded && <form className="administracao-form" onSubmit={e => {e.preventDefault();save();}}
          onInvalidCapture={e => {
            const input=e.target as HTMLInputElement;
            if(["codigo","nome","descricao"].includes(input.name))
              setFieldErrors(v => ({...v,[input.name]:input.validationMessage}));
          }}>
          <fieldset className="administracao-form-fields" disabled={saving || codigo === "ADMIN"}>
            <div className="administracao-form-grid">
              <PerfilField label="Codigo" field="codigo" required error={fieldErrors.codigo}>
                <input className="input" required minLength={2} maxLength={40} pattern="[A-Z][A-Z0-9_]+"
                  readOnly={!!codigo} {...accessibility("codigo")} value={data.codigo} onChange={e => field("codigo",e.target.value)}/>
              </PerfilField>
              <PerfilField label="Nome" field="nome" required error={fieldErrors.nome}>
                <input className="input" required minLength={3} maxLength={150} {...accessibility("nome")}
                  value={data.nome} onChange={e => field("nome",e.target.value)}/>
              </PerfilField>
              <label className="administracao-active"><input type="checkbox" checked={data.ativo}
                onChange={e => setData(v => ({...v,ativo:e.target.checked}))}/>Perfil ativo</label>
              <label className="administracao-active"><input type="checkbox" checked={!!data.sistema} disabled/>Perfil de sistema</label>
            </div>
            <PerfilField label="Descricao" field="descricao" error={fieldErrors.descricao}>
              <textarea className="textarea" rows={4} maxLength={4000} {...accessibility("descricao")}
                value={data.descricao || ""} onChange={e => field("descricao",e.target.value)}/>
            </PerfilField>
            <section className="administracao-permissions"><h2>Permissoes</h2>
              <p className="muted">{data.permissoes.includes("*") ? total : data.permissoes.length} permissoes selecionadas</p>
              {loadingPermissions && <p className="muted" role="status">Carregando permissoes...</p>}
              {permissionsError && <div className="row"><p className="error" role="alert">{permissionsError}</p>
                <button className="icon-button" type="button" title="Recarregar permissoes" aria-label="Recarregar permissoes"
                  disabled={loadingPermissions} onClick={() => setRefresh(v => v + 1)}><RefreshCw size={16}/></button></div>}
              <div className="administracao-permission-grid">{permissions.map(p =>
                <label className="permission-choice" key={p.codigo}><input type="checkbox" checked={data.permissoes.includes("*") || data.permissoes.includes(p.codigo)}
                  onChange={() => toggle(p.codigo)}/><span><strong>{p.nome}</strong><span className="muted">{p.codigo}</span></span></label>)}</div>
              {permissions.length < total && <button type="button" className="button secondary"
                disabled={loadingPermissions || !!permissionsError} onClick={() => setOffset(v => v + 100)}>
                <ChevronDown size={16}/>Mais permissoes</button>}
            </section>
          </fieldset>
          {error && <p className="error" role="alert">{error}</p>}
          {codigo === "ADMIN" && <p className="muted" role="status">Perfil protegido.</p>}
          <div className="actions"><button className="button" disabled={saving || !loaded || loadingPermissions || !!permissionsError || codigo === "ADMIN"}>
            <Save size={16}/>{saving ? "Salvando..." : codigo ? "Salvar alteracoes" : "Salvar perfil"}</button></div>
        </form>}
      </div>
    </section>
  </div></Permission></AppShell>;
}

function PerfilField({label,field,required,error,children}:{
  label:string;field:Field;required?:boolean;error?:string;children:React.ReactNode;
}) {
  return <div className="administracao-field"><label className="field"><span>{label}
    {required && <> <span className="administracao-required">*</span></>}</span>{children}</label>
    {error && <p className="error administracao-field-error" id={"perfil-error-" + field}>{error}</p>}</div>;
}
