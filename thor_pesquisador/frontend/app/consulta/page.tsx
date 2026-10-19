import { Suspense } from "react";
import { PortalCatalog } from "@/components/portal-catalog";
export default function Consulta(){return <Suspense fallback={<p role="status">Carregando...</p>}><PortalCatalog/></Suspense>;}
