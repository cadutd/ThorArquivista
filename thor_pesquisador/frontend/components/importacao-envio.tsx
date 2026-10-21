"use client";
import Link from "next/link";
import { ArrowLeft, FileUp, RefreshCw, Square } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { usePermission } from "./permission";
import { MAX_CHUNK_BYTES, obterLimitesImportacao, progressoImportacao } from "@/lib/importacoes-assincronas";
import type { JobImportacao, LimitesImportacao } from "@/lib/importacoes-assincronas";
import { uploadImportacao } from "@/lib/importacao-upload";

export function tamanhoArquivo(value: number) {
  return (value / 1024 / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + " MiB";
}
export function ImportacaoProgresso({ job }: { job: JobImportacao }) {
  const progress = progressoImportacao(job);
  const envio = job.status === "RECEBENDO";
  return <div className="stack" role="status">
    <label className="field"><span>{envio ? "Arquivo recebido" : "Progresso da fase"}: {envio
      ? tamanhoArquivo(progress.atual) + " de " + tamanhoArquivo(progress.total)
      : progress.atual + " de " + progress.total}</span>
      <progress aria-label="Progresso da importacao" max={100} value={progress.percentual} style={{ width: "100%" }}/></label>
    {job.velocidade != null && <span className="muted">{envio ? tamanhoArquivo(job.velocidade) + "/s" : job.velocidade.toLocaleString("pt-BR") + " registros/s"}</span>}
    {job.estimativa_segundos != null && <span className="muted">Tempo estimado: {Math.ceil(job.estimativa_segundos)} s</span>}
  </div>;
}
export function NovaImportacao({ instrumentoId: id }: { instrumentoId: string }) {
  const canImport = usePermission("registros_incluir", id);
  const router = useRouter(), base = "/instrumentos/" + id + "/registros/importacoes";
  return <div className="stack">
    <div className="row"><div className="page-heading"><h1>Nova importacao</h1></div>
      <Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link></div>
    {canImport ? <ImportacaoEnvio instrumentoId={id} onDone={job => router.push(base + "/" + encodeURIComponent(job.id))}/> :
      <p role="status">Sem permissao para importar registros neste instrumento.</p>}
  </div>;
}
export function ImportacaoEnvio({ instrumentoId: id, job, onDone, onBusy }: {
  instrumentoId: string; job?: JobImportacao; onDone: (job: JobImportacao) => void; onBusy?: (busy: boolean) => void;
}) {
  const canImport = usePermission("registros_incluir", id);
  const [file, setFile] = useState<File>(), [limites, setLimites] = useState<LimitesImportacao>();
  const [progress, setProgress] = useState<JobImportacao | undefined>(job);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [limitsError, setLimitsError] = useState("");
  const [revision, setRevision] = useState(0);
  const controller = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; controller.current?.abort(); };
  }, []);
  useEffect(() => {
    if (!canImport) return;
    const control = new AbortController();
    setLimites(undefined); setLimitsError("");
    obterLimitesImportacao(id, control.signal).then(value => {
      if (!control.signal.aborted) setLimites(value);
    }).catch(err => { if (!control.signal.aborted) setLimitsError(err instanceof Error ? err.message : "Falha ao carregar limites."); });
    return () => control.abort();
  }, [id, canImport, revision]);
  async function enviar(event: React.FormEvent) {
    event.preventDefault();
    if (!file || busy || !canImport || !limites) return;
    if (!file.size) { setError("Selecione um arquivo nao vazio."); return; }
    if (!/\.(csv|json|jsonl|ndjson)$/i.test(file.name)) { setError("Selecione um arquivo CSV, JSON ou JSONL."); return; }
    if (file.size > limites.max_bytes && !job) { setError("Arquivo excede o limite de " + tamanhoArquivo(limites.max_bytes) + "."); return; }
    setBusy(true); onBusy?.(true); setError("");
    const control = new AbortController();
    controller.current = control;
    try {
      const result = await uploadImportacao({ iid: id, file, storage: window.localStorage, signal: control.signal,
        chunkBytes: limites.chunk_bytes, jobId: job?.id, onJob: value => { if (mounted.current) setProgress(value); } });
      if (mounted.current && !control.signal.aborted) onDone(result);
    } catch (err) {
      if (mounted.current) setError(control.signal.aborted ? "Envio interrompido neste navegador." : err instanceof Error ? err.message : "Falha ao enviar arquivo.");
    } finally { if (mounted.current) { setBusy(false); onBusy?.(false); } }
  }
  return <form className="panel stack" onSubmit={enviar}>
    {job && <h2>Continuar envio</h2>}
    {limites && <div className="detail-grid">
      <Fact label="Tamanho maximo" value={tamanhoArquivo(limites.max_bytes)}/>
      <Fact label="Registros por arquivo" value={limites.max_registros.toLocaleString("pt-BR")}/>
      <Fact label="Bloco de envio" value={tamanhoArquivo(Math.min(limites.chunk_bytes, MAX_CHUNK_BYTES))}/>
    </div>}
    {!limites && !limitsError && <p role="status">Carregando limites...</p>}
    {limitsError && <div className="stack"><p className="error" role="alert">{limitsError}</p><div className="actions">
      <button className="button secondary" type="button" onClick={() => setRevision(value => value + 1)}><RefreshCw size={16}/>Tentar novamente</button></div></div>}
    <label className="field"><span>{job ? "Arquivo original CSV, JSON ou JSONL *" : "Arquivo CSV, JSON ou JSONL *"}</span>
      <input className="input" type="file" accept=".csv,.json,.jsonl,.ndjson" required disabled={busy || !canImport}
        onChange={event => { setFile(event.target.files?.[0]); setError(""); }}/></label>
    {progress && <ImportacaoProgresso job={progress}/>}
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions">
      <button className="button" type="submit" disabled={busy || !file || !limites || !canImport}><FileUp size={16}/>{busy ? "Enviando..." : job ? "Continuar envio" : "Enviar arquivo"}</button>
      {busy && <button className="button secondary" type="button" onClick={() => controller.current?.abort()}><Square size={16}/>Interromper envio</button>}
      {!busy && progress && <Link className="button secondary"
        href={"/instrumentos/" + id + "/registros/importacoes/" + encodeURIComponent(progress.id)}>Ver importacao</Link>}
    </div>
  </form>;
}
export function Fact({ label, value }: { label: string; value: string | number }) {
  return <div className="detail-item"><span>{label}</span><strong className="break-text">{value}</strong></div>;
}
