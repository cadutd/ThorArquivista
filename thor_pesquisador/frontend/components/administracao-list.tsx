"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Edit, Eye, Plus, Search, SlidersHorizontal } from "lucide-react";
import { AppShell } from "./app-shell";
import { Permission } from "./permission";
import { CrudPagination } from "./crud-pagination";
import { AdministracaoDetails } from "./administracao-details";
import { PerfilPopup } from "./perfil-popup";
import { UsuarioPopup } from "./usuario-popup";
import { request } from "@/lib/api";

type Kind = "usuarios" | "perfis" | "permissoes";
type Row = {id?: string; codigo?: string; nome: string; ativo?: boolean; [key: string]: unknown};
const titles = {usuarios:"Gestao de Usuarios", perfis:"Perfis", permissoes:"Permissoes"};
const columns: Record<Kind, [string, string][]> = {
  usuarios:[["nome","Nome"],["username","Usuario"],["email","E-mail"],["perfis","Perfis"],["tem_acesso","Acesso"],["ativo","Ativo"]],
  perfis:[["nome","Nome"],["codigo","Codigo"],["permissoes","Permissoes"],["ativo","Situacao"],["sistema","Sistema"]],
  permissoes:[["nome","Nome"],["codigo","Codigo"],["modulo","Modulo"],["funcao","Funcao"],["acao","Acao"]],
};

// Same list workflow as the Gestor: draft filters, server pages and row actions.
export function AdministracaoList({tipo,usuarioInicial,perfilInicial}: {tipo: Kind;usuarioInicial?:string;perfilInicial?:string}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(20);
  const [draft, setDraft] = useState<Record<string, string>>({q:""});
  const [filters, setFilters] = useState(draft);
  const [advanced, setAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<Row>();
  const [selectedUser,setSelectedUser] = useState<string | undefined>(usuarioInicial);
  const [selectedProfile,setSelectedProfile] = useState<string | undefined>(perfilInicial);
  useEffect(() => {
    let current = true; setLoading(true);
    const query = new URLSearchParams({limit:String(size), offset:String(page * size)});
    Object.entries(filters).forEach(([key, value]) => { if(value.trim()) query.set(key, value.trim()); });
    request<{items:Row[]; total:number}>("/" + tipo + "?" + query)
      .then(r => { if(current) {setRows(r.items); setTotal(r.total); setError("");} })
      .catch(e => { if(current) {setError(e.message);setRows([]);setTotal(0);} })
      .finally(() => { if(current) setLoading(false); });
    return () => {current = false;};
  }, [tipo, filters, page, size, refresh]);
  function apply() {setFilters({...draft});setPage(0);setRefresh(v => v + 1);}
  function deleted() {
    setSelectedProfile(undefined);setSelectedUser(undefined);
    if(rows.length === 1 && page > 0) setPage(v => v - 1);else setRefresh(v => v + 1);
  }
  const pagination = {total, pageIndex:page, pageSize:size, loading, onPageChange:setPage,
    onPageSizeChange:(n:number) => {setSize(n);setPage(0);}};
  const textFilters = tipo === "usuarios" ? [["nome","Nome"],["username","Usuario"],["email","E-mail"],["cpf","CPF"],["papel","Perfil (codigo)"]] :
    tipo === "permissoes" ? [["modulo","Modulo"],["funcao","Funcao"]] : [];
  const actionLabels:Record<string,string> = {INCLUIR:"Incluir",EDITAR:"Editar",CONSULTAR:"Consultar",EXCLUIR:"Excluir"};
  return <AppShell><Permission acao={tipo + "_consultar"}><div className="stack administracao-page">
    <div className="row"><h1>{titles[tipo]}</h1>{tipo === "perfis" &&
      <Permission acao="perfis_incluir"><Link href="/perfis/novo" className="button"><Plus size={16}/>Novo perfil</Link></Permission>}
      {tipo === "usuarios" && <Permission acao="usuarios_incluir"><Link href="/usuarios/novo" className="button"><Plus size={16}/>Novo usuario</Link></Permission>}</div>
    <form className="stack crud-search-form" onSubmit={e => {e.preventDefault();apply();}}>
      <div className="row"><label className="field search-field"><span>Busca simples</span>
        <input className="input" value={draft.q || ""} onChange={e => setDraft({...draft,q:e.target.value})}/></label>
        <div className="actions"><button className="button" disabled={loading}><Search size={16}/>Pesquisar</button>
          <button type="button" className="icon-button" title="Filtros" aria-label="Filtros" aria-expanded={advanced}
            onClick={() => setAdvanced(v => !v)}><SlidersHorizontal size={16}/></button>
          <button type="button" className="button secondary" disabled={loading}
            onClick={() => {setDraft({q:""});setFilters({q:""});setPage(0);setRefresh(v => v + 1);}}>Limpar</button></div></div>
      {advanced && <div className="grid">{textFilters.map(([key,label]) =>
        <label className="field" key={key}><span>{label}</span><input className="input" value={draft[key] || ""}
          onChange={e => setDraft({...draft,[key]:e.target.value})}/></label>)}
        {tipo !== "permissoes" && <label className="field"><span>Situacao</span><select className="select"
          value={draft.ativo || ""} onChange={e => setDraft({...draft,ativo:e.target.value})}>
          <option value="">Todas</option><option value="true">Ativo</option><option value="false">Inativo</option></select></label>}
        {tipo === "permissoes" && <label className="field"><span>Acao</span><select className="select"
          value={draft.acao || ""} onChange={e => setDraft({...draft,acao:e.target.value})}>
          <option value="">Todas</option>{["CONSULTAR","INCLUIR","EDITAR","EXCLUIR"].map(v => <option key={v}>{v}</option>)}</select></label>}
      </div>}
    </form>
    {error && <p className="error" role="alert">{error}</p>}
    <CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table" aria-busy={loading}><thead><tr>
      {columns[tipo].map(([key,label]) => <th key={key}>{label}</th>)}<th>Acoes</th></tr></thead><tbody>
      {rows.map(row => {const id = String(row.id || row.codigo);const path = "/" + tipo + "/" + encodeURIComponent(id);
        return <tr key={id}>{columns[tipo].map(([key]) => <td key={key}>
          {key === "nome" ? tipo === "usuarios" ?
            <a className="crud-record-link" href={path} onClick={e => {e.preventDefault();setSelectedUser(id);}}>{row.nome}</a> :
            tipo === "permissoes" ?
            <a className="crud-record-link" href={"#permissao-" + row.codigo} onClick={e => {e.preventDefault();setSelected(row);}}>{row.nome}</a> :
            <a className="crud-record-link" href={path} onClick={e => {e.preventDefault();setSelectedProfile(id);}}>{row.nome}</a> :
            key === "ativo" ? row.ativo ? "Ativo" : "Inativo" : key === "sistema" ? row.sistema ? "Sim" : "Nao" :
            key === "perfis" ? Array.isArray(row.perfis) ? row.perfis.map(p => String(p.nome) + (p.ativo ? "" : " (inativo)")).join(", ") || "Nenhum" : "Nenhum" :
            key === "tem_acesso" ? row.tem_acesso ? "Concedido" : "Sem acesso" :
            key === "permissoes" ? Array.isArray(row.permissoes) ? row.permissoes.length : 0 :
            key === "acao" ? actionLabels[String(row.acao)] || String(row.acao) : String(row[key] ?? "-")}
        </td>)}<td><div className="actions">
          {tipo === "usuarios" ? <button className="icon-button" title="Visualizar" aria-label="Visualizar"
            onClick={() => setSelectedUser(id)}><Eye size={16}/></button> :
            tipo === "permissoes" ? <button className="icon-button" title="Visualizar permissao" aria-label="Visualizar permissao"
            onClick={() => setSelected(row)}><Eye size={16}/></button> :
            <button className="icon-button" title="Visualizar" aria-label="Visualizar"
              onClick={() => setSelectedProfile(id)}><Eye size={16}/></button>}
          {tipo !== "permissoes" && row.codigo !== "ADMIN" &&
            <Permission acao={tipo + "_editar"}><Link className="icon-button" title="Editar" aria-label="Editar" href={path + "/editar"}><Edit size={16}/></Link></Permission>}
        </div></td></tr>;})}
      {!rows.length && <tr><td colSpan={columns[tipo].length + 1}>{loading ? "Carregando..." : error ? "Listagem indisponivel." : "Nenhum registro encontrado."}</td></tr>}
    </tbody></table></div><CrudPagination {...pagination}/>
    {tipo === "usuarios" && selectedUser && <UsuarioPopup id={selectedUser} onClose={() => setSelectedUser(undefined)}
      onDeleted={deleted}/>}
    {tipo === "perfis" && selectedProfile && <PerfilPopup key={selectedProfile} codigo={selectedProfile}
      onClose={() => setSelectedProfile(undefined)} onDeleted={deleted}/>}
    {tipo === "permissoes" && selected && <AdministracaoDetails title="Permissao" onClose={() => setSelected(undefined)}
      fields={columns.permissoes.map(([key,label]) => [label,key === "acao"
        ? actionLabels[String(selected.acao)] || String(selected.acao) : String(selected[key] ?? "-")] as const)}/>}
  </div></Permission></AppShell>;
}
