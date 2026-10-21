"use client";
import { useEffect,useState } from "react";
import { API_BASE_URL } from "@/lib/config";

export const DEFAULT_INSTRUMENTO_IMAGE="/images/login-digital-archive.png";
export function InstrumentoCardImage({src,alt=""}:{src?:string|null;alt?:string}) {
  const [failed,setFailed]=useState(false);
  useEffect(()=>setFailed(false),[src]);
  const url=!src||failed?DEFAULT_INSTRUMENTO_IMAGE:src.startsWith("/")?API_BASE_URL+src:src;
  return <img className="instrumento-cover" src={url} alt={alt} width={960} height={540}
    loading="lazy" onError={()=>{if(!failed)setFailed(true);}}/>;
}
