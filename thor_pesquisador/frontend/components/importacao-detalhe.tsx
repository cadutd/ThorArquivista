"use client";
import Link from "next/link";
import { ArrowLeft, Check, Download, RefreshCw, RotateCcw, Search, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePermission } from "./permission";
import { Fact, ImportacaoEnvio, ImportacaoProgresso, tamanhoArquivo } from "./importacao-envio";
import { displayImportacao, ImportacaoMapeamento, sugerirMapeamentos } from "./importacao-mapeamento";
import { acionarImportacao, baixarErrosImportacao, importacaoAtiva, obterImportacao, podeCancelarImportacao, podeRetomarImportacao } from "@/lib/importacoes-assincronas";
import type { AcaoImportacao, JobImportacao } from "@/lib/importacoes-assincronas";
import type { ConfiguracaoImportacao, Mapeamento } from "@/lib/importacoes";

function useImportacao(id: string, jobId: string, enabled: boolean, suspended: boolean) {
  const [job, setJob] = useState<JobImportacao>(), [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const currentJob = useRef<JobImportacao | undefined>(undefined);
  currentJob.current = job;
  const refresh = useCallback(() => setRevision(value => value + 1), []);
  useEffect(() => {
    if (!enabled || suspended) return;
    let live = true, timer: ReturnType<typeof setTimeout> | undefined, request: AbortController | undefined;
    function stop() { clearTimeout(timer); request?.abort(); }
    async function load() {
      if (!live || document.hidden) return;
      request?.abort();
      const control = new AbortController();
      request = control;
      try {
        const value = await obterImportacao(id, jobId, control.signal);
        if (!live || control.signal.aborted) return;
        currentJob.current = value; setJob(value); setError("");
        if (importacaoAtiva(value.status)) timer = setTimeout(load, 3000);
      } catch (err) {
        if (!live || control.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar importacao.");
        if (!currentJob.current || importacaoAtiva(currentJob.current.status)) timer = setTimeout(load, 3000);
      }
    }
    function visibility() {
      stop();
      if (!document.hidden && (!currentJob.current || importacaoAtiva(currentJob.current.status))) void load();
    }
    document.addEventListener("visibilitychange", visibility);
    void load();
    return () => { live = false; stop(); document.removeEventListener("visibilitychange", visibility); };
  }, [id, jobId, enabled, suspended, revision]);
  return { job, setJob, error, refresh };
}
export function ImportacaoDetalhe({ instrumentoId: id, jobId }: { instrumentoId: string; jobId: string }) {
  const canImport = usePermission("registros_incluir", id), canCreateFields = usePermission("campos_incluir", id);
  const [busy, setBusy] = useState(false), [uploadBusy, setUploadBusy] = useState(false), [error, setError] = useState("");
  const { job, setJob, error: loadError, refresh } = useImportacao(id, jobId, canImport, busy || uploadBusy);
  const [mappings, setMappings] = useState<Mapeamento[]>([]), [dirty, setDirty] = useState(false);
  const initialized = useRef(false), actionController = useRef<AbortController | null>(null);
  const base = "/instrumentos/" + id + "/registros/importacoes";
  useEffect(() => () => actionController.current?.abort(), []);
  useEffect(() => {
    if (job?.analise && !initialized.current) {
      setMappings(job.configuracao?.mapeamentos || sugerirMapeamentos(job.analise));
      initialized.current = true;
    }
  }, [job]);
  const hasNewFields = mappings.some(item => item.novo);
  const confirmationNeedsFields = job?.configuracao?.mapeamentos.some(item => item.novo) || false;
  const canMutate = canImport && !busy && !uploadBusy;
  async function action(acao: AcaoImportacao, configuration?: ConfiguracaoImportacao) {
    if (!job || !canMutate) return;
    if (((acao === "validar" && hasNewFields) || (acao === "confirmar" && confirmationNeedsFields)) && !canCreateFields) {
      setError("Sem permissao para criar campos neste instrumento."); return;
    }
    if (acao === "cancelar" && !window.confirm("Cancelar esta importacao?")) return;
    if (acao === "confirmar" && (dirty || job.status !== "AGUARDANDO_CONFIRMACAO" || !job.relatorio || job.relatorio.invalidos > 0)) return;
    if (acao === "confirmar" && !window.confirm("Confirmar a importacao de " + job.relatorio!.total + " registros como rascunho?")) return;
    const control = new AbortController(); actionController.current = control;
    setBusy(true); setError("");
    try {
      const value = await acionarImportacao(id, jobId, acao, configuration, control.signal);
      if (!control.signal.aborted) { setJob(value); if (acao === "validar") setDirty(false); refresh(); }
    } catch (err) {
      if (!control.signal.aborted) setError(err instanceof Error ? err.message : "Falha ao atualizar importacao.");
    } finally { if (!control.signal.aborted) setBusy(false); }
  }
  function validar(event: React.FormEvent) {
    event.preventDefault();
    if (!job?.analise) return;
    const selected = mappings.filter(item => item.destino || item.novo);
    if (!selected.length) { setError("Associe ao menos uma coluna."); return; }
    const keys = selected.map(item => item.destino || item.novo!.chave);
    if (new Set(keys).size !== keys.length) { setError("Associe cada campo a apenas uma coluna."); return; }
    void action("validar", { operacao_id: job.configuracao?.operacao_id || job.id,
      schema_version: job.analise.schema_version, mapeamentos: selected });
  }
  async function download() {
    if (!canMutate) return;
    setBusy(true); setError("");
    try { await baixarErrosImportacao(id, jobId); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao baixar erros."); }
    finally { setBusy(false); }
  }
  if (!canImport) return <section className="stack"><h1>Importacao</h1><p role="status">Sem permissao para importar registros neste instrumento.</p></section>;
  const editable = !!job && ["AGUARDANDO_MAPA", "ERROS_VALIDACAO", "AGUARDANDO_CONFIRMACAO"].includes(job.status);
  const report = job?.relatorio;
  const previewMappings = job?.configuracao?.mapeamentos || [];
  return <div className="stack">
    <div className="row"><div className="page-heading"><h1>Importacao</h1><p className="muted break-text">{job?.nome_arquivo}</p></div>
      <div className="actions"><Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link>
        <button className="icon-button" title="Atualizar importacao" aria-label="Atualizar importacao" disabled={!canMutate} onClick={refresh}><RefreshCw size={16}/></button>
        {job && podeRetomarImportacao(job.status) && <button className="icon-button" title="Retomar importacao" aria-label="Retomar importacao"
          disabled={!canMutate} onClick={() => action("retomar")}><RotateCcw size={16}/></button>}
        {job && podeCancelarImportacao(job.status) && <button className="icon-button danger" title="Cancelar importacao" aria-label="Cancelar importacao"
          disabled={!canMutate} onClick={() => action("cancelar")}><X size={16}/></button>}
      </div>
    </div>
    {(error || loadError) && <p className="error" role="alert">{error || loadError}</p>}
    {!job && !loadError && <p role="status">Carregando importacao...</p>}
    {job && <>
      <section className="panel stack"><h2>Andamento</h2><div className="detail-grid">
        <Fact label="Status" value={job.status.replaceAll("_", " ")}/><Fact label="Fase" value={job.phase || "-"}/>
        <Fact label="Registros" value={job.total}/><Fact label="Importados" value={job.processados}/>
        <Fact label="Analisados / validados na fase" value={job.fase_processados}/><Fact label="Validos" value={job.validos}/>
        <Fact label="Invalidos" value={job.invalidos}/><Fact label="Arquivo" value={tamanhoArquivo(job.tamanho_bytes)}/>
        <Fact label="Criada em" value={new Date(job.criado_em).toLocaleString("pt-BR")}/>
        <Fact label="Atualizada em" value={new Date(job.atualizado_em).toLocaleString("pt-BR")}/>
        <Fact label="Expira em" value={job.expira_em ? new Date(job.expira_em).toLocaleString("pt-BR") : "-"}/>
      </div>
        {importacaoAtiva(job.status) && <ImportacaoProgresso job={job}/>}
        {job.erro && <p className="error" role="alert">{job.erro}</p>}
        {job.status === "CONCLUIDA" && <div className="actions"><Link className="button" href={"/instrumentos/" + id + "/registros"}><Check size={16}/>Ver registros</Link></div>}
      </section>
      {job.status === "RECEBENDO" && <ImportacaoEnvio instrumentoId={id} job={job} onBusy={setUploadBusy} onDone={value => { setJob(value); refresh(); }}/>}
      {editable && job.analise && <form className="panel stack" onSubmit={validar}>
        <ImportacaoMapeamento analise={job.analise} value={mappings} canCreateFields={canCreateFields} disabled={!canMutate}
          onChange={value => { setMappings(value); setDirty(true); setError(""); }}/>
        <div className="actions"><button className="button" type="submit" disabled={!canMutate || (hasNewFields && !canCreateFields)}>
          <Search size={16}/>{busy ? "Aguarde..." : "Validar importacao"}</button></div>
      </form>}
      {report && <section className="panel stack"><h2>Conferencia</h2>
        <div className="detail-grid"><Fact label="Registros" value={report.total}/><Fact label="Validos" value={report.validos}/><Fact label="Invalidos" value={report.invalidos}/></div>
        {report.erros.length > 0 && <div className="table-wrap"><table className="table" aria-label="Erros de importacao">
          <thead><tr><th>Linha</th><th>Campo</th><th>Mensagem</th></tr></thead><tbody>{report.erros.map((item, index) =>
            <tr key={index}><td>{item.linha}</td><td>{item.campo || "-"}</td><td className="break-text">{item.mensagem}</td></tr>)}</tbody>
        </table></div>}
        {report.invalidos > 0 && <div className="actions"><button className="button secondary" type="button" disabled={!canMutate} onClick={download}>
          <Download size={16}/>Baixar erros CSV</button></div>}
        {report.previa.length > 0 && <div className="table-wrap"><table className="table" aria-label="Previa de registros">
          <thead><tr><th>Linha</th>{previewMappings.map(item => <th key={item.origem}>{item.novo?.nome ||
            job.analise?.campos.find(campo => campo.chave === item.destino)?.nome || item.destino}</th>)}</tr></thead>
          <tbody>{report.previa.map(item => <tr key={item.linha}><td>{item.linha}</td>{previewMappings.map(mapping =>
            <td className="break-text" key={mapping.origem}>{displayImportacao(item.dados[mapping.destino || mapping.novo!.chave])}</td>)}</tr>)}</tbody>
        </table></div>}
        {editable && <div className="actions"><button className="button" type="button" onClick={() => action("confirmar")}
          disabled={!canMutate || dirty || job.status !== "AGUARDANDO_CONFIRMACAO" || report.invalidos > 0 || (confirmationNeedsFields && !canCreateFields)}>
          <Check size={16}/>Confirmar importacao</button></div>}
      </section>}
    </>}
  </div>;
}
