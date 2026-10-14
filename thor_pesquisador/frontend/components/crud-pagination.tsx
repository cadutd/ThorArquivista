"use client";
import { useId } from "react";
import { getPaginationItems } from "@/lib/pagination.mjs";

export function CrudPagination({total, pageIndex, pageSize, loading, onPageChange, onPageSizeChange}: {
  total:number;pageIndex:number;pageSize:number;loading:boolean;onPageChange:(n:number)=>void;onPageSizeChange:(n:number)=>void;
}) {
  const id = useId();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(pageIndex, pages - 1);
  const displayed = Math.max(0, Math.min(pageSize, total - pageIndex * pageSize));
  const sizes = [...new Set([pageSize, 20, 50, 100])].sort((a,b) => a-b);
  const pageItems = getPaginationItems(current + 1, pages);
  return <div className="pagination crud-pagination">
    <span className="muted">{displayed} registros de {total} | p&aacute;gina {current+1} de {pages}</span>
    <div className="actions">
      <button className="button secondary" type="button" title="Primeira pagina" disabled={loading || current === 0} onClick={() => onPageChange(0)}>Primeira</button>
      <button className="button secondary" type="button" title="Pagina anterior" disabled={loading || current === 0} onClick={() => onPageChange(current-1)}>Anterior</button>
      {pageItems.map((page, index) => page === "ellipsis" ?
        <span key={"ellipsis-" + index} className="pagination-ellipsis muted">...</span> :
        <button key={page} type="button" className={"button pagination-page " + (page === current + 1 ? "pagination-page-current" : "secondary")}
          aria-current={page === current + 1 ? "page" : undefined} disabled={loading || page === current + 1}
          onClick={() => onPageChange(page - 1)}>{page}</button>)}
      <button className="button secondary" type="button" title="Proxima pagina" disabled={loading || current >= pages-1} onClick={() => onPageChange(current+1)}>Pr&oacute;xima</button>
      <button className="button secondary" type="button" title="Ultima pagina" disabled={loading || current >= pages-1} onClick={() => onPageChange(pages-1)}>&Uacute;ltima</button>
      <div className="pagination-page-size">
      <label htmlFor={id} className="muted">Por p&aacute;gina:</label>
      <select id={id} aria-label="Registros por pagina" className="select page-size" value={pageSize} disabled={loading}
        onChange={e => onPageSizeChange(Number(e.target.value))}>{sizes.map(n => <option key={n} value={n}>{n}</option>)}</select>
      </div>
    </div>
  </div>;
}
