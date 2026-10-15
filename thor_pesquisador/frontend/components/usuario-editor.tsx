"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Save, ShieldCheck } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { ApiError, request } from "@/lib/api";

export type Usuario = {
  id:string; nome:string; username:string; cpf:string | null; email:string | null; ativo:boolean;
  observacoes:string | null; perfis:{codigo:string;nome:string;ativo:boolean}[]; total_acessos:number; tem_acesso:boolean;
  govbr_vinculado:boolean; criado_em:string; atualizado_em:string;
};
type UsuarioFormData = {
  nome:string; username:string; cpf:string; email:string; ativo:boolean; observacoes:string;
};
type FieldErrors = Partial<Record<keyof UsuarioFormData,string>>;

export function UsuarioEditor({id}:{id?:string}) {
  const router = useRouter();
  const [user, setUser] = useState<Usuario>();
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState<Usuario>();
  useEffect(() => {
    setUser(undefined);setError("");setFieldErrors({});
    if(!id) return;
    let current = true;
    request<Usuario>("/usuarios/" + id).then(u => {if(current) setUser(u);})
      .catch(e => {if(current) setError(e.message);});
    return () => {current = false;};
  }, [id]);
  async function save(data: UsuarioFormData) {
    setSaving(true);setError("");setFieldErrors({});
    try {
      const saved = await request<Usuario>(id ? "/usuarios/" + id : "/usuarios", {
        method:id ? "PUT" : "POST", body:JSON.stringify(data)});
      if(id) router.push("/usuarios");else setCreated(saved);
    } catch(e) {
      if(e instanceof ApiError && Array.isArray(e.detail)) {
        const errors:FieldErrors = {};
        for(const item of e.detail) {
          const field = item.loc?.[1];
          if(typeof field === "string" && field in data && typeof item.msg === "string")
            errors[field as keyof UsuarioFormData] = item.msg;
        }
        setFieldErrors(errors);
      }
      setError(e instanceof Error ? e.message : "Falha ao salvar usuario.");
    } finally {setSaving(false);}
  }
  function fieldError(field:keyof UsuarioFormData,message:string) {
    setFieldErrors(v => ({...v,[field]:message}));
  }
  return <AppShell><Permission acao={id ? "usuarios_editar" : "usuarios_incluir"}><div className="usuario-editor-page">
    <div className="row usuario-page-heading"><h1>{id ? "Editar usuario" : "Novo usuario"}</h1>
      <Link href="/usuarios" className="button secondary"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="usuario-editor-surface">
      <header><h2>{id ? "Edicao" : "Cadastro"}</h2>{user && <p>{user.nome}</p>}</header>
      <div className="usuario-editor-content">
        {id && !user && !error && <p className="muted" role="status">Carregando usuario...</p>}
        {created && <div className="stack"><p role="status">Usuario cadastrado. Sem acesso concedido.</p>
          <div className="actions"><Permission acao="acessos_incluir"><Link className="button" title="Conceder acesso"
            href={"/acessos/novo?usuario=" + created.id}><ShieldCheck size={16}/>Conceder acesso</Link></Permission>
            <Link className="button secondary" href="/usuarios">Voltar para usuarios</Link></div></div>}
        {!created && (!id || user) && <UsuarioForm key={id || "novo"} initial={user} saving={saving} error={error}
          errors={fieldErrors} onFieldError={fieldError} onSubmit={save}/>}
        {id && !user && error && <p className="error" role="alert">{error}</p>}
      </div>
    </section>
    {user && <Permission acao="acessos_consultar"><div className="actions"><Link href={"/usuarios/" + user.id + "/acessos"} className="button secondary"
      title="Gerenciar perfis e escopos"><ShieldCheck size={16}/>Perfis e escopos</Link></div></Permission>}
  </div></Permission></AppShell>;
}

function UsuarioForm({initial,saving,onSubmit,error,errors,onFieldError}:{
  initial?:Usuario;saving:boolean;error:string;errors:FieldErrors;
  onFieldError:(field:keyof UsuarioFormData,message:string)=>void;
  onSubmit:(data:UsuarioFormData)=>Promise<void>;
}) {
  const [form, setForm] = useState<UsuarioFormData>({
    nome:initial?.nome || "", username:initial?.username || "", cpf:initial?.cpf || "",
    email:initial?.email || "", ativo:initial?.ativo ?? true, observacoes:initial?.observacoes || "",
  });
  function field(key: keyof UsuarioFormData, value:string | boolean) {
    setForm(v => ({...v,[key]:value}));onFieldError(key,"");
  }
  function accessibility(key:keyof UsuarioFormData) {
    return {name:key,"aria-invalid":!!errors[key],"aria-describedby":errors[key] ? "usuario-error-" + key : undefined};
  }
  return <form className="usuario-form" onSubmit={e => {e.preventDefault();onSubmit(form);}}
    onInvalidCapture={e => {
      const control = e.target as HTMLInputElement;
      if(control.name in form) onFieldError(control.name as keyof UsuarioFormData,control.validationMessage);
    }}>
    <fieldset className="usuario-form-fields" disabled={saving}>
      <div className="usuario-form-grid">
        <UsuarioField label="Nome" required field="nome" error={errors.nome}>
          <input className="input" required maxLength={255} {...accessibility("nome")}
            value={form.nome} onChange={e => field("nome",e.target.value)}/>
        </UsuarioField>
        <UsuarioField label="Usuario" required field="username" error={errors.username}>
          <input className="input" required minLength={3} maxLength={150} pattern="[a-zA-Z0-9_.-]+"
            autoComplete="off" {...accessibility("username")} value={form.username} onChange={e => field("username",e.target.value)}/>
        </UsuarioField>
        <UsuarioField label="E-mail" required field="email" error={errors.email}>
          <input className="input" required type="email" maxLength={255} {...accessibility("email")}
            value={form.email} onChange={e => field("email",e.target.value)}/>
        </UsuarioField>
        <UsuarioField label="CPF" required field="cpf" error={errors.cpf}>
          <input className="input" required inputMode="numeric" maxLength={14} {...accessibility("cpf")}
            readOnly={initial?.govbr_vinculado} value={form.cpf} onChange={e => field("cpf",e.target.value)}/>
        </UsuarioField>
        <label className="usuario-active"><input type="checkbox" checked={form.ativo}
          onChange={e => field("ativo",e.target.checked)}/>Usuario ativo</label>
      </div>
      <UsuarioField label="Observacoes" field="observacoes" error={errors.observacoes}>
        <textarea className="textarea" maxLength={4000} rows={4} {...accessibility("observacoes")}
          value={form.observacoes} onChange={e => field("observacoes",e.target.value)}/>
      </UsuarioField>
    </fieldset>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions"><button className="button" disabled={saving}><Save size={16}/>
      {saving ? "Salvando..." : initial ? "Salvar alteracoes" : "Salvar usuario"}</button></div>
  </form>;
}

function UsuarioField({label,required,field,error,children}:{
  label:string;required?:boolean;field:keyof UsuarioFormData;error?:string;children:React.ReactNode;
}) {
  return <div className="usuario-field"><label className="field"><span>{label}
    {required && <> <span className="usuario-required">*</span></>}</span>{children}</label>
    {error && <p className="error usuario-field-error" id={"usuario-error-" + field}>{error}</p>}
  </div>;
}
