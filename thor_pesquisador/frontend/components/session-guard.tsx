"use client";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, request } from "@/lib/api";
import { loginPath, SESSION_EXPIRED } from "@/lib/auth-navigation.mjs";

export function SessionGuard({children}:{children:React.ReactNode}) {
  const pathname = usePathname();
  const [verified,setVerified] = useState("");
  const [error,setError] = useState("");
  useEffect(() => {
    if(pathname === "/login") return;
    let current = true, checking = false, redirecting = false, validated = false;
    const controller = new AbortController();
    setError("");
    function login() {
      if(!current || redirecting) return;
      redirecting = true;setVerified("");
      window.location.replace(loginPath(window.location.pathname + window.location.search + window.location.hash));
    }
    async function check() {
      if(checking || redirecting) return;
      checking = true;
      try {
        await request("/auth/me",{signal:controller.signal,cache:"no-store"});
        if(current && !redirecting) {validated = true;setVerified(pathname);setError("");}
      } catch(e) {
        if(!current) return;
        if(e instanceof ApiError && e.status === 401) login();
        else if(!validated) {setVerified("");setError(e instanceof Error ? e.message : "Falha ao verificar sessao.");}
      } finally {checking = false;}
    }
    function focus() {if(document.visibilityState === "visible") void check();}
    window.addEventListener(SESSION_EXPIRED,login);
    window.addEventListener("focus",focus);
    window.addEventListener("pageshow",focus);
    document.addEventListener("visibilitychange",focus);
    const interval = window.setInterval(focus,60000);
    void check();
    return () => {
      current = false;controller.abort();window.clearInterval(interval);
      window.removeEventListener(SESSION_EXPIRED,login);
      window.removeEventListener("focus",focus);window.removeEventListener("pageshow",focus);
      document.removeEventListener("visibilitychange",focus);
    };
  },[pathname]);
  if(pathname === "/login") return <>{children}</>;
  if(error) return <main className="container"><p className="error" role="alert">{error}</p>
    <button className="button secondary" onClick={() => window.location.reload()}>Tentar novamente</button></main>;
  if(verified !== pathname) return <main className="container"><p role="status">Verificando sessao...</p></main>;
  return <>{children}</>;
}
