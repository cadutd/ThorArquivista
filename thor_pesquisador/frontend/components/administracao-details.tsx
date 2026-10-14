"use client";
import { X } from "lucide-react";
import { ModalFrame } from "./modal-frame";

export function AdministracaoDetails({title,onClose,fields,loading,error,description,children,actions}:{
  title:string;onClose:()=>void;fields:ReadonlyArray<readonly [string,React.ReactNode]>;
  loading?:boolean;error?:string;description?:string|null;children?:React.ReactNode;actions?:React.ReactNode;
}) {
  return <ModalFrame title={title} onClose={onClose} className="administracao-popup">
    <div className="row administracao-popup-header"><h2>{title}</h2>
      <button autoFocus className="administracao-popup-close" title="Fechar" aria-label="Fechar"
        onClick={onClose}><X size={16}/></button></div>
    {loading && <p className="muted" role="status">Carregando...</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {!loading && !!fields.length && <dl className="administracao-details">{fields.map(([label,value]) =>
      <div className="detail-item" key={label}><dt>{label}</dt><dd>{value ?? "-"}</dd></div>)}</dl>}
    {!loading && description && <section className="administracao-notes"><h3>Descricao</h3><p>{description}</p></section>}
    {!loading && children}
    {!loading && actions && <div className="actions administracao-popup-actions">{actions}</div>}
  </ModalFrame>;
}
