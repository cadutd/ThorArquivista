"use client";

import Link from "next/link";
import { ArrowLeft, Edit, FileText, SlidersHorizontal, Trash2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { EditorialPanel } from "@/components/editorial-panel";
import { InstrumentoCardImage } from "@/components/instrumento-card-image";
import { Permission } from "@/components/permission";
import { StatusBadge } from "@/components/status-badge";
import { deleteInstrumento, getInstrumento } from "@/lib/api";
import type { Instrumento } from "@/types/domain";

export default function InstrumentoDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [instrumento, setInstrumento] = useState<Instrumento>();
  const [error, setError] = useState("");
  const [removing, setRemoving] = useState(false);
  useEffect(() => {
    let current = true;
    setInstrumento(undefined); setError("");
    getInstrumento(id).then(data => { if (current) setInstrumento(data); })
      .catch(err => { if (current) setError(err instanceof Error ? err.message : "Falha ao carregar instrumento."); });
    return () => { current = false; };
  }, [id]);
  async function remove() {
    if (!instrumento || removing || !window.confirm('Excluir o instrumento "' + instrumento.nome + '"? Instrumentos com historico devem ser arquivados e nao podem ser excluidos.')) return;
    setRemoving(true); setError("");
    try { await deleteInstrumento(id); router.push("/instrumentos"); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao excluir instrumento."); }
    finally { setRemoving(false); }
  }
  function refresh() {
    getInstrumento(id).then(setInstrumento).catch(err => setError(err.message));
  }
  return <AppShell><div className="stack crud-detail-page">
    <div className="row crud-page-heading">
      <div className="page-heading"><h1>Visualizar instrumento</h1></div>
      <div className="actions">
        <Link className="button secondary" href="/instrumentos"><ArrowLeft size={16}/>Voltar</Link>
        {instrumento && <>
          <Permission acao="instrumentos_editar" instrumentoId={id}>
            <Link className="button secondary" href={`/instrumentos/${id}/editar`} title="Editar instrumento"><Edit size={16}/>Editar</Link>
          </Permission>
          <Permission acao="instrumentos_excluir" instrumentoId={id}>
            <button className="button danger" type="button" title="Excluir instrumento" disabled={removing} onClick={remove}>
              <Trash2 size={16}/>{removing ? "Excluindo..." : "Excluir"}
            </button>
          </Permission>
        </>}
      </div>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {!instrumento && !error && <p role="status">Carregando instrumento...</p>}
    {instrumento && <>
      <section className="panel stack crud-detail-surface">
        <header className="crud-section-heading"><h2>{instrumento.nome}</h2></header>
        <dl className="crud-details">
          <Detail label="ID">{instrumento.id}</Detail>
          <Detail label="Nome">{instrumento.nome}</Detail>
          <Detail label="Tipo">{instrumento.tipo.replaceAll("_", " ")}</Detail>
          <Detail label="Status"><StatusBadge value={instrumento.status}/></Detail>
          <Detail label="Visibilidade"><StatusBadge value={instrumento.visibilidade}/></Detail>
          <Detail label="Versao do schema">{instrumento.schema_version}</Detail>
          <Detail label="Versao editorial">{instrumento.versao_editorial}</Detail>
          <Detail label="Publicacao (ID)">{instrumento.publicacao_id || "-"}</Detail>
          <Detail label="Criado em">{formatDate(instrumento.criado_em)}</Detail>
          <Detail label="Atualizado em">{formatDate(instrumento.atualizado_em)}</Detail>
          <Detail label="Descricao" wide>{instrumento.descricao || "-"}</Detail>
          <Detail label="Imagem do card" wide>
            <div className="instrumento-detail-image">
              <InstrumentoCardImage src={instrumento.imagem_card_id ? "/instrumentos/imagens-card/" + instrumento.imagem_card_id : null}
                alt={"Imagem do instrumento " + instrumento.nome}/>
            </div>
          </Detail>
          <Detail label="Imagem do card (ID)">{instrumento.imagem_card_id || "-"}</Detail>
        </dl>
        <div className="actions">
          <Permission acao="campos_consultar" instrumentoId={id}><Link className="button secondary" href={`/instrumentos/${id}/campos`}><SlidersHorizontal size={16}/>Campos</Link></Permission>
          <Permission acao="registros_consultar" instrumentoId={id}><Link className="button secondary" href={`/instrumentos/${id}/registros`}><FileText size={16}/>Registros</Link></Permission>
        </div>
      </section>
      <EditorialPanel instrumentoId={id} status={instrumento.status} versao={instrumento.versao_editorial} onChange={refresh}/>
    </>}
  </div></AppShell>;
}

function Detail({ label, children, wide }: { label: string; children: React.ReactNode; wide?: boolean }) {
  return <div className={"crud-detail-field" + (wide ? " crud-field-wide" : "")}><dt>{label}</dt><dd>{children}</dd></div>;
}
function formatDate(value: string) {
  return new Date(value).toLocaleString("pt-BR");
}
