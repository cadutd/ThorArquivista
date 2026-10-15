"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Save, Search, X } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission, usePermission } from "./permission";
import { CrudPagination } from "./crud-pagination";
import { AccessList } from "./access-list";
import { request } from "@/lib/api";
import type { Acesso } from "./acesso-editor";

type Item = {id:string;nome:string;username?:string|null;email?:string|null;tipo?:string;status?:string;permissoes?:string[]};
type Filter = {key:string;label:string;options?:[string,string][]};
const userFilters:Filter[] = [{key:"nome",label:"Nome"},{key:"username",label:"Nome de usuario"},{key:"email",label:"Email"}];
const profileFilters:Filter[] = [{key:"q",label:"Perfil"}];
const instrumentFilters:Filter[] = [
  {key:"nome",label:"Nome"},
  {key:"tipo",label:"Tipo",options:[["GUIA","Guia"],["INVENTARIO","Inventario"],["CATALOGO","Catalogo"],["INDICE","Indice"],["BASE_TEMATICA","Base tematica"],["OUTRO","Outro"]]},
  {key:"status",label:"Status",options:[["RASCUNHO","Rascunho"],["EM_REVISAO","Em revisao"],["APROVADO","Aprovado"],["PUBLICADO","Publicado"],["ARQUIVADO","Arquivado"]]}
];
export function AcessoCadastro({id,usuarioId}:{id?:string;usuarioId?:string}) {
  const router = useRouter();
  const [original,setOriginal] = useState<Acesso>();
  const [user,setUser] = useState<Item>();
  const [profiles,setProfiles] = useState<Item[]>([]);
  const [instruments,setInstruments] = useState<Item[]>([]);
  const [scope,setScope] = useState<"GLOBAL"|"INSTRUMENTO">("GLOBAL");
  const [loading,setLoading] = useState(!!id || !!usuarioId);
  const [saving,setSaving] = useState(false);
  const [error,setError] = useState("");
  const backPath = usuarioId ? "/usuarios/" + usuarioId + "/acessos" : "/acessos";
  useEffect(() => {
    let current = true;
    setOriginal(undefined);setUser(undefined);setProfiles([]);setInstruments([]);setScope("GLOBAL");setError("");
    setLoading(!!id || !!usuarioId);
    async function load() {
      if(id) {
        const access = await request<Acesso>("/acessos/" + id);
        const selectedUser = await request<Item>("/usuarios/" + access.usuario_id);
        const profile = await request<Item>("/perfis/" + encodeURIComponent(access.papel));
        const instrument = access.instrumento_id ? await request<Item>("/instrumentos/" + access.instrumento_id) : undefined;
        if(current) {
          setOriginal(access);setUser(selectedUser);setProfiles([{...profile,id:access.papel}]);
          setScope(access.instrumento_id ? "INSTRUMENTO" : "GLOBAL");setInstruments(instrument ? [instrument] : []);
        }
      } else if(usuarioId) {
        const selectedUser = await request<Item>("/usuarios/" + usuarioId);
        if(current) setUser(selectedUser);
      }
    }
    load().catch(e => {if(current) setError(e.message);}).finally(() => {if(current) setLoading(false);});
    return () => {current = false;};
  },[id,usuarioId]);
  function selectUser(value:Item) {
    if(value.id === user?.id) return;
    setUser(value);setProfiles([]);setInstruments([]);setScope("GLOBAL");setError("");
  }
  function selectProfiles(value:Item[]) {
    setProfiles(value);setError("");
    if(value.some(p => p.id === "ADMIN" || p.permissoes?.includes("*"))) {setScope("GLOBAL");setInstruments([]);}
  }
  const globalOnly = profiles.some(p => p.id === "ADMIN" || p.permissoes?.includes("*"));
  const count = profiles.length * (scope === "GLOBAL" ? 1 : instruments.length);
  const valid = (!id || !!original) && !!user && profiles.length > 0 && count > 0 && count <= 1000 && profiles.length <= 50 && instruments.length <= 100;
  async function save() {
    if(!valid || saving) return;
    setSaving(true);setError("");
    try {
      await request(id ? "/acessos/" + id + "/lote" : "/acessos/lote",{method:id ? "PUT" : "POST",body:JSON.stringify({
        usuario_id:user!.id,perfis:profiles.map(p => p.id),escopo:scope,
        instrumento_ids:scope === "GLOBAL" ? [] : instruments.map(i => i.id)
      })});
      router.push(usuarioId ? "/usuarios/" + user!.id + "/acessos" : "/acessos");
    } catch(e) {setError(e instanceof Error ? e.message : "Falha ao conceder acessos.");}
    finally {setSaving(false);}
  }
  return <AppShell><Permission acao={id ? "acessos_editar" : "acessos_incluir"}><div className="administracao-editor-page concessao-cadastro">
    <div className="row administracao-page-heading"><h1>{id ? "Editar acesso" : "Novo acesso"}</h1><Link href={backPath} className="button secondary"><ArrowLeft size={16}/>Voltar</Link></div>
    <section className="administracao-editor-surface">
      <header><h2>{id ? "Edicao" : "Cadastro"}</h2></header>
      <div className="administracao-editor-content concessao-editor-content">
    {loading && <p role="status">Carregando acesso...</p>}
    <fieldset className="concessao-flow" disabled={saving || loading}>
      <section aria-labelledby="concessao-usuario" className="concessao-step"><h2 id="concessao-usuario">1. Usuario <span className="administracao-required">*</span></h2>
        <Lookup label="Usuarios" path="/usuarios?ativo=true" filters={userFilters} columns={[["nome","Nome"],["username","Nome de usuario"],["email","Email"]]}
          selected={user ? [user] : []} onChange={items => selectUser(items[0])} single/>
        {user && <dl className="administracao-details concessao-selected-user" aria-label="Usuario selecionado">
          {[["Nome",user.nome],["Nome de usuario",user.username],["Email",user.email]].map(([label,value]) =>
            <div className="detail-item" key={label}><dt>{label}</dt><dd>{value || "-"}</dd></div>)}
        </dl>}
      </section>
      {user && <section className="concessao-step" aria-label="Acessos existentes"><h2>2. Acessos existentes</h2>
        <AccessList key={user.id} usuarioId={user.id} readonly hideHeading/>
      </section>}
      <fieldset className="concessao-step" disabled={!user}><legend>3. Perfis <span className="administracao-required">*</span></legend>
        <Lookup key={user?.id || "perfis"} label="Perfis" path="/perfis?ativo=true" filters={profileFilters}
          columns={[["nome","Perfil"],["codigo","Codigo"]]} selected={profiles} onChange={selectProfiles} autoLoad={!!user}/>
        <Selections label="Perfis selecionados" items={profiles} onRemove={id => selectProfiles(profiles.filter(p => p.id !== id))}/>
      </fieldset>
      <fieldset className="concessao-step" disabled={!user || !profiles.length}><legend>4. Escopo <span className="administracao-required">*</span></legend>
        <div className="actions" role="radiogroup" aria-label="Escopo da concessao">
          <label className="concessao-radio"><input type="radio" name="escopo" value="GLOBAL" checked={scope === "GLOBAL"}
            onChange={() => {setScope("GLOBAL");setInstruments([]);setError("");}}/>Global</label>
          <label className="concessao-radio"><input type="radio" name="escopo" value="INSTRUMENTO" checked={scope === "INSTRUMENTO"} disabled={globalOnly}
            onChange={() => {setScope("INSTRUMENTO");setError("");}}/>Por instrumento</label>
        </div>
        <fieldset className="concessao-instruments" disabled={scope === "GLOBAL"}><legend>Instrumentos</legend>
          <Lookup key={(user?.id || "") + scope} label="Instrumentos" path="/instrumentos" filters={instrumentFilters}
            columns={[["nome","Nome"],["tipo","Tipo"],["status","Status"]]} selected={instruments} onChange={items => {setInstruments(items);setError("");}}/>
          <Selections label="Instrumentos selecionados" items={instruments} onRemove={id => setInstruments(instruments.filter(i => i.id !== id))}/>
        </fieldset>
      </fieldset>
      {user && profiles.length > 0 && <section className="concessao-review" aria-label="Resumo da concessao"><h2>Resumo da concessao</h2>
        <dl><dt>Usuario</dt><dd>{user.nome}</dd><dt>Perfis</dt><dd>{profiles.map(p => p.nome).join(", ")}</dd>
          <dt>Escopo</dt><dd>{scope === "GLOBAL" ? "Global" : instruments.map(i => i.nome).join(", ") || "Nenhum instrumento selecionado"}</dd>
          <dt>{id ? "Acessos apos salvar" : "Novos acessos"}</dt><dd>{count}</dd>
          {id && <><dt>Novas concessoes</dt><dd>{Math.max(0,count - 1)}</dd></>}</dl>
        {(count > 1000 || profiles.length > 50 || instruments.length > 100) && <p className="error" role="alert">Limite de 50 perfis, 100 instrumentos e 1000 concessoes por operacao.</p>}
      </section>}
    </fieldset>
    {error && <p className="error" role="alert">{error}</p>}
    <SaveAction editing={!!id} count={count} disabled={!valid || saving || loading} saving={saving} onSave={save}/>
      </div>
    </section>
  </div></Permission></AppShell>;
}
function SaveAction({editing,count,disabled,saving,onSave}:{editing:boolean;count:number;disabled:boolean;saving:boolean;onSave:()=>void}) {
  const canInclude = usePermission("acessos_incluir");
  const blocked = editing && count > 1 && !canInclude;
  return <>{blocked && <p className="error" role="alert">A selecao gera novas concessoes e exige permissao para incluir acessos.</p>}
    <div className="actions"><button className="button" disabled={disabled || blocked} onClick={onSave}><Save size={16}/>
      {saving ? "Salvando..." : editing ? "Salvar alteracoes" : "Salvar acesso"}</button></div></>;
}
function Selections({label,items,onRemove}:{label:string;items:Item[];onRemove:(id:string)=>void}) {
  return <div className="concessao-selections" aria-label={label}><strong>{label}: {items.length}</strong>
    <ul>{items.map(item => <li key={item.id}><span>{item.nome}</span>
      <button className="icon-button" type="button" title={"Remover " + item.nome} aria-label={"Remover " + item.nome} onClick={() => onRemove(item.id)}><X size={16}/></button>
    </li>)}</ul></div>;
}
function Lookup({label,path,filters,columns,selected,onChange,single=false,autoLoad=false}:{
  label:string;path:string;filters:Filter[];columns:[string,string][];selected:Item[];onChange:(items:Item[])=>void;single?:boolean;autoLoad?:boolean;
}) {
  const [draft,setDraft] = useState<Record<string,string>>({});
  const [applied,setApplied] = useState<Record<string,string>|null>(autoLoad ? {} : null);
  const [page,setPage] = useState(0),[size,setSize] = useState(20);
  const [rows,setRows] = useState<Item[]>([]),[total,setTotal] = useState(0);
  const [loading,setLoading] = useState(false),[error,setError] = useState("");
  useEffect(() => {
    if(applied === null) return;
    let current = true;setLoading(true);setError("");setRows([]);
    const params = new URLSearchParams({limit:String(size),offset:String(page*size)});
    for(const [key,value] of Object.entries(applied)) if(value.trim()) params.set(key,value.trim());
    request<{items:Item[];total:number}>(path + (path.includes("?") ? "&" : "?") + params)
      .then(result => {if(current) {setRows(result.items);setTotal(result.total);}})
      .catch(e => {if(current) {setError(e.message);setTotal(0);}})
      .finally(() => {if(current) setLoading(false);});
    return () => {current = false;};
  },[path,applied,page,size]);
  function toggle(item:Item) {
    onChange(single ? [item] : selected.some(i => i.id === item.id) ? selected.filter(i => i.id !== item.id) : [...selected,item]);
  }
  const pagination = <CrudPagination total={total} pageIndex={page} pageSize={size} loading={loading}
    onPageChange={setPage} onPageSizeChange={value => {setSize(value);setPage(0);}}/>;
  return <div className="stack concessao-lookup" role="group" aria-label={"Pesquisa de " + label.toLowerCase()}>
    <form className={"concessao-search administracao-form-grid" + (filters.length === 1 ? " concessao-search-single" : "")} onSubmit={e => {e.preventDefault();setPage(0);setApplied({...draft});}}>
      {filters.map(filter => <label className="field administracao-field" key={filter.key}><span>{filter.label}</span>
        {filter.options ? <select className="select" aria-label={filter.label} value={draft[filter.key] || ""} onChange={e => setDraft({...draft,[filter.key]:e.target.value})}>
          <option value="">Todos</option>{filter.options.map(([value,title]) => <option key={value} value={value}>{title}</option>)}</select>
          : <input className="input" aria-label={filter.label} value={draft[filter.key] || ""} onChange={e => setDraft({...draft,[filter.key]:e.target.value})}/>}</label>)}
      <div className="actions"><button className="button" type="submit" title={"Buscar " + label.toLowerCase()} disabled={loading}><Search size={16}/>Buscar {label.toLowerCase()}</button>
        <button className="button secondary" type="button" disabled={loading} onClick={() => {setDraft({});setPage(0);setApplied({});}}>Limpar</button></div>
    </form>
    {loading && <p role="status">Carregando {label.toLowerCase()}...</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {applied !== null && !error && <>{pagination}<div className="table-wrap"><table className="table concessao-lookup-table" aria-label={label}><thead><tr>
      <th className="concessao-check">Selecionar</th>{columns.map(([key,title]) => <th key={key}>{title}</th>)}
    </tr></thead><tbody>{rows.map(item => <tr key={item.id}>
      <td><input type={single ? "radio" : "checkbox"} name={single ? "usuario-selecionado" : undefined} aria-label={"Selecionar " + item.nome}
        checked={selected.some(i => i.id === item.id)} onChange={() => toggle(item)}/></td>
      {columns.map(([key]) => <td key={key}>{String((item as unknown as Record<string,unknown>)[key] ?? "-")}</td>)}
    </tr>)}{!rows.length && !loading && <tr><td colSpan={columns.length+1} className="muted">Nenhum registro encontrado.</td></tr>}</tbody></table></div>{pagination}</>}
  </div>;
}
