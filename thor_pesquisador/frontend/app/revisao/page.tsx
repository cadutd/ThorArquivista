"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Eye } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { request } from "@/lib/api";
import { CrudPagination } from "@/components/crud-pagination";
type Item = { instrumento_id: string; nome: string; registro_id: string | null; versao: number };
export default function ReviewQueue() {
  const [items, setItems] = useState<Item[]>([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let current = true;
    setLoading(true);
    request<{ items: Item[]; total: number }>("/editorial/fila?limit=" + pageSize + "&offset=" + offset)
      .then(r => { if(current) { setItems(r.items); setTotal(r.total); setError(""); } }).catch(e => { if(current) setError(e.message); })
      .finally(() => { if(current) setLoading(false); });
    return () => { current = false; };
  }, [offset, pageSize]);
  return <AppShell><div className="stack"><h1>Fila de revisao</h1>{error && <p className="error">{error}</p>}
    <div className="table-wrap"><table className="table"><thead><tr><th>Instrumento</th><th>Registro</th><th>Versao</th><th>Acoes</th></tr></thead>
      <tbody>{items.map(i => <tr key={i.instrumento_id + i.registro_id}><td><Link className="crud-record-link" href={"/instrumentos/" + i.instrumento_id + (i.registro_id ? "/registros/" + encodeURIComponent(i.registro_id) : "")}>{i.nome}</Link></td><td>{i.registro_id || "Schema"}</td><td>{i.versao}</td>
        <td><Link className="icon-button" title="Visualizar" href={"/instrumentos/" + i.instrumento_id +
          (i.registro_id ? "/registros/" + encodeURIComponent(i.registro_id) : "")}><Eye size={16}/></Link></td></tr>)}</tbody></table></div>
    <CrudPagination total={total} pageIndex={Math.floor(offset/pageSize)} pageSize={pageSize} loading={loading}
      onPageChange={n => setOffset(n * pageSize)} onPageSizeChange={n => { setPageSize(n); setOffset(0); }}/>
  </div></AppShell>;
}
