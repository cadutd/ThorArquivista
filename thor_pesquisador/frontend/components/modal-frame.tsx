"use client";
import {useEffect,useRef} from "react";
export function ModalFrame({title,onClose,children}:{title:string;onClose:()=>void;children:React.ReactNode}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{
  const dialog=ref.current;const previous=document.activeElement as HTMLElement|null;
  dialog?.showModal();
  return ()=>{dialog?.close();previous?.focus();};
 },[]);
 return <dialog ref={ref} className="media-modal native-modal" aria-label={title} onCancel={e=>{e.preventDefault();onClose();}}>{children}</dialog>;
}
