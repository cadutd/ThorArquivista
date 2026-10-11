"use client";
import { ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight } from "lucide-react";

export function CrudPagination({total, pageIndex, pageSize, loading, onPageChange, onPageSizeChange}: {
  total:number;pageIndex:number;pageSize:number;loading:boolean;onPageChange:(n:number)=>void;onPageSizeChange:(n:number)=>void;
}) {
  const pages=Math.max(1,Math.ceil(total/pageSize));
  return <div className="pagination">
    <span className="muted">{total ? pageIndex*pageSize+1 : 0}-{Math.min(total,(pageIndex+1)*pageSize)} de {total} | pagina {pageIndex+1} de {pages}</span>
    <div className="actions">
      <select aria-label="Registros por pagina" className="select page-size" value={pageSize} disabled={loading} onChange={e=>onPageSizeChange(Number(e.target.value))}>{[10,20,50,100].map(n=><option key={n} value={n}>{n}/pagina</option>)}</select>
      <button className="icon-button" title="Primeira pagina" aria-label="Primeira pagina" disabled={loading||pageIndex===0} onClick={()=>onPageChange(0)}><ChevronsLeft size={16}/></button>
      <button className="icon-button" title="Pagina anterior" aria-label="Pagina anterior" disabled={loading||pageIndex===0} onClick={()=>onPageChange(pageIndex-1)}><ChevronLeft size={16}/></button>
      {Array.from({length: Math.min(pages,5)},(_,n)=>Math.max(0,Math.min(pageIndex-2,pages-5))+n).map(n=><button key={n} className={n===pageIndex?"button":"button secondary"} aria-current={n===pageIndex?"page":undefined} disabled={loading} onClick={()=>onPageChange(n)}>{n+1}</button>)}
      <button className="icon-button" title="Proxima pagina" aria-label="Proxima pagina" disabled={loading||pageIndex>=pages-1} onClick={()=>onPageChange(pageIndex+1)}><ChevronRight size={16}/></button>
      <button className="icon-button" title="Ultima pagina" aria-label="Ultima pagina" disabled={loading||pageIndex>=pages-1} onClick={()=>onPageChange(pages-1)}><ChevronsRight size={16}/></button>
    </div>
  </div>;
}
