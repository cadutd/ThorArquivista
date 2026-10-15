"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { Edit,Eye,Plus,Search,SlidersHorizontal } from "lucide-react";
import { Permission } from "./permission";
import { CrudPagination } from "./crud-pagination";
import { AcessoPopup } from "./acesso-popup";
import { request } from "@/lib/api";
import type { Acesso } from "./acesso-editor";

const empty = {q:"",papel:"",instrumento:"",escopo:""};
export function AccessList({usuarioId,readonly=false,acessoInicial,hideHeading=false}:{
  usuarioId?:string;readonly?:boolean;acessoInicial?:string;hideHeading?:boolean;
}) {
  const [rows,setRows] = useState<Acesso[]>([]);
  const [page,setPage] = useState(0);
  const [size,setSize] = useState(20);
  const [total,setTotal] = useState(0);
  const [draft,setDraft] = useState(empty);
  const [filters,setFilters] = useState(empty);
  const [advanced,setAdvanced] = useState(false);
  const [error,setError] = useState("");
  const [loading,setLoading] = useState(false);
  const [refresh,setRefresh] = useState(0);
  const [selected,setSelected] = useState<string|undefined>(acessoInicial);
  useEffect(() => {
    let current = true;setLoading(true);
    const query = new URLSearchParams({limit:String(size),offset:String(page * size)});
    Object.entries(filters).forEach(([key,value]) => {if(value.trim()) query.set(key,value.trim());});
    if(usuarioId) query.set("usuario_id",usuarioId);
    request<{items:Acesso[];total:number}>("/acessos?" + query)
      .then(result => {if(current) {setRows(result.items);setTotal(result.total);setError("");}})
      .catch(e => {if(current) {setError(e.message);setRows([]);setTotal(0);}})
      .finally(() => {if(current) setLoading(false);});
    return () => {current = false;};
  },[page,size,filters,refresh,usuarioId]);
  function apply() {setFilters({...draft});setPage(0);setRefresh(v => v + 1);}
  function deleted() {
    setSelected(undefined);
    if(rows.length === 1 && page > 0) setPage(v => v - 1);else setRefresh(v => v + 1);
  }
  const pagination = {total,pageIndex:page,pageSize:size,loading,onPageChange:setPage,
    onPageSizeChange:(n:number) => {setSize(n);setPage(0);}};
  return <div className="stack administracao-page concessoes-list">
    {!hideHeading && <div className="row">{usuarioId ? <h2>Concessoes de acesso</h2> : <h1>Concessoes de acesso</h1>}
      {!readonly && <Permission acao="acessos_incluir"><Link className="button"
        href={"/acessos/novo" + (usuarioId ? "?usuario=" + usuarioId : "")}><Plus size={16}/>Novo acesso</Link></Permission>}
    </div>}
    <form className="stack crud-search-form" onSubmit={e => {e.preventDefault();apply();}}>
      <div className="row"><label className="field search-field"><span>Busca simples</span>
        <input className="input" value={draft.q} onChange={e => setDraft({...draft,q:e.target.value})}/></label>
        <div className="actions"><button className="button" disabled={loading}><Search size={16}/>Pesquisar</button>
          <button className="icon-button" type="button" title="Filtros" aria-label="Filtros" aria-expanded={advanced}
            onClick={() => setAdvanced(value => !value)}><SlidersHorizontal size={16}/></button>
          <button className="button secondary" type="button" disabled={loading}
            onClick={() => {setDraft(empty);setFilters(empty);setPage(0);setRefresh(v => v + 1);}}>Limpar</button>
        </div></div>
      {advanced && <div className="grid">
        <label className="field"><span>Perfil (codigo)</span><input className="input" value={draft.papel}
          onChange={e => setDraft({...draft,papel:e.target.value})}/></label>
        <label className="field"><span>Instrumento</span><input className="input" value={draft.instrumento}
          onChange={e => setDraft({...draft,instrumento:e.target.value})}/></label>
        <label className="field"><span>Escopo</span><select className="select" aria-label="Escopo" value={draft.escopo}
          onChange={e => setDraft({...draft,escopo:e.target.value})}><option value="">Todos</option>
          <option value="GLOBAL">Global</option><option value="INSTRUMENTO">Por instrumento</option></select></label>
      </div>}
    </form>
    {error && <p className="error" role="alert">{error}</p>}
    <CrudPagination {...pagination}/>
    <div className="table-wrap"><table className="table concessoes-table" aria-busy={loading}>
      <colgroup><col className="concessoes-user"/><col className="concessoes-profile"/>
        <col className="concessoes-scope"/><col className="concessoes-instrument"/><col className="concessoes-actions"/></colgroup>
      <thead><tr><th>Usuario</th><th>Perfil</th><th>Escopo</th><th>Instrumento</th><th>Acoes</th></tr></thead>
      <tbody>{rows.map(row => <tr key={row.id}><td><a className="crud-record-link" href={"/acessos/" + row.id}
        onClick={e => {e.preventDefault();setSelected(row.id);}}>{row.nome}</a></td>
        <td>{row.perfil_nome || row.papel}</td><td>{row.instrumento_id ? "Por instrumento" : "Global"}</td>
        <td>{row.instrumento_id ? row.instrumento_nome || "-" : "Todos"}</td>
        <td><div className="actions"><button className="icon-button" title="Visualizar" aria-label="Visualizar"
          onClick={() => setSelected(row.id)}><Eye size={16}/></button>
          {!readonly && <Permission acao="acessos_editar"><Link className="icon-button" title="Editar" aria-label="Editar"
            href={"/acessos/" + row.id + "/editar" + (usuarioId ? "?usuario=" + usuarioId : "")}><Edit size={16}/></Link></Permission>}
        </div></td></tr>)}
        {!rows.length && <tr><td colSpan={5}>{loading ? "Carregando..." : error ? "Listagem indisponivel." : "Nenhum registro encontrado."}</td></tr>}
      </tbody></table></div>
    <CrudPagination {...pagination}/>
    {selected && <AcessoPopup key={selected} id={selected} usuarioId={usuarioId} readonly={readonly}
      onClose={() => setSelected(undefined)} onDeleted={deleted}/>}
  </div>;
}
