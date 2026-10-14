"use client";
import {useEffect,useRef} from "react";
export function ModalFrame({title,onClose,children,className=""}:{title:string;onClose:()=>void;children:React.ReactNode;className?:string}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{
  const dialog=ref.current;const previous=document.activeElement as HTMLElement|null;
  dialog?.showModal();
  return ()=>{dialog?.close();previous?.focus();};
 },[]);
 return <dialog ref={ref} className={"media-modal native-modal " + className} aria-label={title}
  onClick={e=>{
   if(e.target!==e.currentTarget) return;
   const bounds=e.currentTarget.getBoundingClientRect();
   if(e.clientX<bounds.left||e.clientX>bounds.right||e.clientY<bounds.top||e.clientY>bounds.bottom) onClose();
  }}
  onCancel={e=>{e.preventDefault();onClose();}}>{children}</dialog>;
}
