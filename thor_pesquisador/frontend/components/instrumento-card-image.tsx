"use client";
import { useEffect,useState } from "react";
import { API_BASE_URL } from "@/lib/config";

export const DEFAULT_INSTRUMENTO_IMAGE="/images/login-digital-archive.png";
export function InstrumentoCardImage({src}:{src?:string|null}) {
  const [failed,setFailed]=useState(false);
  useEffect(()=>setFailed(false),[src]);
  const url=!src||failed?DEFAULT_INSTRUMENTO_IMAGE:src.startsWith("/")?API_BASE_URL+src:src;
  return <img className="instrumento-cover" src={url} alt="" width={960} height={540}
    loading="lazy" onError={()=>{if(!failed)setFailed(true);}}/>;
}
