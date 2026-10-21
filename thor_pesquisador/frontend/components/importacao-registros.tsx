"use client";
import Link from "next/link";
import { ArrowLeft, Check, FileUp, Plus, RotateCcw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { usePermission } from "./permission";
import { enviarImportacao, listarImportacoes } from "@/lib/importacoes";
import type { AnaliseImportacao, ConfiguracaoImportacao, Importacao, Mapeamento, NovoCampo, RelatorioImportacao } from "@/lib/importacoes";
import type { TipoCampo } from "@/types/domain";

const tipos: TipoCampo[] = ["TEXTO_CURTO", "TEXTO_LONGO", "NUMERO", "DATA", "BOOLEANO", "LISTA_SIMPLES", "LISTA_MULTIPLA", "URL"];
const nomesTipos: Record<TipoCampo, string> = { TEXTO_CURTO: "Texto curto", TEXTO_LONGO: "Texto longo", NUMERO: "Numero",
  DATA: "Data", BOOLEANO: "Booleano", LISTA_SIMPLES: "Lista simples", LISTA_MULTIPLA: "Lista multipla", URL: "URL" };

export function ImportacaoRegistros({ instrumentoId: id }: { instrumentoId: string }) {
  const canImport = usePermission("registros_incluir", id), canCreateFields = usePermission("campos_incluir", id);
  const [file, setFile] = useState<File>();
  const [analysis, setAnalysis] = useState<AnaliseImportacao>();
  const [mappings, setMappings] = useState<Mapeamento[]>([]);
  const [operation, setOperation] = useState("");
  const [report, setReport] = useState<RelatorioImportacao>();
  const [result, setResult] = useState<Importacao>();
  const [resume, setResume] = useState<Importacao>();
  const [history, setHistory] = useState<Importacao[]>([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [historyError, setHistoryError] = useState("");
  const base = "/instrumentos/" + id + "/registros";

  async function loadHistory() {
    try { const items = await listarImportacoes(id); setHistory(items); setHistoryError(""); return items; }
    catch (err) { setHistoryError(err instanceof Error ? err.message : "Falha ao carregar importacoes."); return []; }
  }
  useEffect(() => {
    if (!canImport) return;
    let live = true;
    listarImportacoes(id).then(items => { if (live) setHistory(items); })
      .catch(err => { if (live) setHistoryError(err.message); });
    return () => { live = false; };
  }, [id, canImport]);

  async function analyze(event: React.FormEvent) {
    event.preventDefault();
    if (!file || busy) return;
    if (file.size > 5 * 1024 * 1024) { setError("Arquivo excede 5 MiB."); return; }
    setBusy(true); setError(""); setReport(undefined); setResult(undefined);
    try {
      const value = await enviarImportacao<AnaliseImportacao>(id, "analisar", file);
      setAnalysis(value); setOperation(resume?.id || crypto.randomUUID());
      setMappings(resume ? resume.configuracao.mapeamentos : value.colunas.map(column => {
        const existing = value.campos.find(field => field.chave === column.chave_sugerida ||
          field.nome.localeCompare(column.origem, "pt-BR", { sensitivity: "base" }) === 0);
        return { origem: column.origem, destino: existing?.chave || "" };
      }));
    } catch (err) { setError(err instanceof Error ? err.message : "Falha ao analisar arquivo."); }
    finally { setBusy(false); }
  }

  function novo(origem: string): NovoCampo {
    const column = analysis!.colunas.find(c => c.origem === origem)!;
    return { nome: origem, chave: column.chave_sugerida, tipo: column.tipo_sugerido, obrigatorio: false };
  }
  function change(index: number, value: Mapeamento) {
    setMappings(previous => previous.map((mapping, position) => position === index ? value : mapping));
    setReport(undefined); setResult(undefined);
  }
  function configuration(): ConfiguracaoImportacao {
    return { operacao_id: operation, schema_version: resume?.configuracao.schema_version || analysis!.schema_version,
      mapeamentos: mappings.filter(mapping => mapping.destino || mapping.novo) };
  }
  async function validate(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !analysis || busy) return;
    if (!configuration().mapeamentos.length) { setError("Associe ao menos uma coluna."); return; }
    setBusy(true); setError(""); setResult(undefined);
    try { setReport(await enviarImportacao<RelatorioImportacao>(id, "validar", file, configuration())); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao validar importacao."); }
    finally { setBusy(false); }
  }
  async function execute() {
    if (!file || !report || report.invalidos || busy) return;
    if (!window.confirm("Confirmar a importacao de " + report.total + " registros como rascunho?")) return;
    setBusy(true); setError("");
    try { setResult(await enviarImportacao<Importacao>(id, "", file, configuration())); }
    catch (err) { setError(err instanceof Error ? err.message : "Falha ao importar. Consulte o resultado nas importacoes recentes."); }
    finally { await loadHistory(); setBusy(false); }
  }
  function retomar(job: Importacao) {
    setResume(job); setAnalysis(undefined); setReport(undefined); setResult(undefined);
    setFile(undefined); setError(""); setMappings(job.configuracao.mapeamentos); setOperation(job.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function reset() {
    setResume(undefined); setFile(undefined); setAnalysis(undefined); setReport(undefined); setResult(undefined);
    setMappings([]); setOperation(""); setError("");
  }
  const step = result ? 3 : report ? 2 : analysis ? 1 : 0;
  if (!canImport) return <section className="stack"><h1>Importar registros</h1><p role="status">Sem permissao para importar registros neste instrumento.</p></section>;
  return <div className="stack">
    <div className="row"><div className="page-heading"><h1>Importar registros</h1><p className="muted">{analysis?.nome}</p></div>
      <Link className="button secondary" href={base}><ArrowLeft size={16}/>Voltar</Link></div>
    <ol className="importacao-steps">{["Arquivo", "Associacao", "Conferencia", "Resultado"].map((label, index) =>
      <li key={label} aria-current={step === index ? "step" : undefined}>{index + 1}. {label}</li>)}</ol>
    {!analysis && <form className="panel stack" onSubmit={analyze}>
      {resume && <div className="row"><p>Retomar importacao: {resume.processados} de {resume.total} registros</p>
        <button className="button secondary" type="button" onClick={reset} disabled={busy}><RotateCcw size={16}/>Nova importacao</button></div>}
      <label className="field"><span>Arquivo CSV ou JSON *</span><input key={resume?.id || operation || "novo"} className="input" type="file" accept=".csv,.json" required disabled={busy}
        onChange={event => { setFile(event.target.files?.[0]); setError(""); }}/></label>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions"><button className="button" disabled={busy || !file} type="submit"><FileUp size={16}/>{busy ? "Analisando..." : "Analisar arquivo"}</button></div>
    </form>}
    {analysis && !result && <>
      <form className="panel stack" onSubmit={validate}>
        <div className="row"><h2>Associacao de campos</h2>
          <div className="actions">
            {canCreateFields && !resume && <button className="button secondary" disabled={busy} type="button" onClick={() => {
              setMappings(previous => previous.map(mapping => mapping.destino || mapping.novo ? mapping : { origem: mapping.origem, novo: novo(mapping.origem) }));
              setReport(undefined);
            }}><Plus size={16}/>Criar campos nao associados</button>}
            <button className="button secondary" type="button" disabled={busy} onClick={reset}><RotateCcw size={16}/>Trocar arquivo</button>
          </div>
        </div>
        <p className="muted">{file?.name} | {analysis.total} registros | {analysis.formato.toUpperCase()} | {analysis.codificacao}</p>
        <fieldset className="registro-fields" disabled={busy || !!resume}>
          <div className="table-wrap"><table className="table importacao-mapping" aria-label="Associacao de campos">
            <thead><tr><th>Coluna do arquivo</th><th>Exemplo</th><th>Associar a</th><th>Novo campo</th></tr></thead>
            <tbody>{mappings.map((mapping, index) => {
              const column = analysis.colunas.find(c => c.origem === mapping.origem);
              return <tr key={mapping.origem}><td className="break-text">{mapping.origem}</td>
                <td className="break-text">{display(column?.amostras[0]).slice(0, 160)}</td>
                <td><select className="select" aria-label={"Associar " + mapping.origem} value={mapping.novo ? "__novo" : mapping.destino || ""}
                  onChange={event => change(index, event.target.value === "__novo" ? { origem: mapping.origem, novo: novo(mapping.origem) } : { origem: mapping.origem, destino: event.target.value })}>
                  <option value="">Ignorar</option>{analysis.campos.map(field => <option key={field.chave} value={field.chave}>{field.nome}</option>)}
                  {canCreateFields && <option value="__novo">Criar novo campo</option>}
                </select></td>
                <td>{mapping.novo ? <div className="stack">
                  <label className="field"><span>Nome *</span><input className="input" aria-label={"Nome do campo " + mapping.origem} required maxLength={255}
                    value={mapping.novo.nome} onChange={e => change(index, { ...mapping, novo: { ...mapping.novo!, nome: e.target.value } })}/></label>
                  <label className="field"><span>Chave *</span><input className="input" aria-label={"Chave do campo " + mapping.origem} required maxLength={100} pattern="[a-zA-Z][a-zA-Z0-9_]*"
                    value={mapping.novo.chave} onChange={e => change(index, { ...mapping, novo: { ...mapping.novo!, chave: e.target.value } })}/></label>
                  <label className="field"><span>Tipo *</span><select className="select" aria-label={"Tipo do campo " + mapping.origem} value={mapping.novo.tipo}
                    onChange={e => change(index, { ...mapping, novo: { ...mapping.novo!, tipo: e.target.value as TipoCampo } })}>
                    {tipos.map(tipo => <option key={tipo} value={tipo}>{nomesTipos[tipo]}</option>)}</select></label>
                  <label className="checkbox-field"><input type="checkbox" checked={mapping.novo.obrigatorio} onChange={e => change(index, { ...mapping, novo: { ...mapping.novo!, obrigatorio: e.target.checked } })}/>Obrigatorio</label>
                </div> : "-"}</td>
              </tr>;
            })}</tbody>
          </table></div>
        </fieldset>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="actions"><button className="button" type="submit" disabled={busy}><Search size={16}/>{busy ? "Validando..." : "Validar importacao"}</button></div>
      </form>
      {report && <section className="panel stack">
        <h2>Conferencia</h2>
        <div className="detail-grid"><Fact label="Registros" value={report.total}/><Fact label="Validos" value={report.validos}/>
          <Fact label="Invalidos" value={report.invalidos}/><Fact label="Novos campos" value={mappings.filter(mapping => mapping.novo).length}/></div>
        {report.erros.length > 0 && <div className="table-wrap"><table className="table" aria-label="Erros de importacao">
          <thead><tr><th>Registro</th><th>Campo</th><th>Erro</th></tr></thead>
          <tbody>{report.erros.map((item, index) => <tr key={index}><td>{item.linha}</td><td>{item.campo || "-"}</td><td className="break-text">{item.mensagem}</td></tr>)}</tbody>
        </table></div>}
        <div className="table-wrap"><table className="table" aria-label="Previa de registros"><thead><tr><th>Registro</th>
          {configuration().mapeamentos.map(mapping => <th key={mapping.origem}>{mapping.novo?.nome || analysis.campos.find(field => field.chave === mapping.destino)?.nome}</th>)}</tr></thead>
          <tbody>{report.previa.map(item => <tr key={item.linha}><td>{item.linha}</td>{configuration().mapeamentos.map(mapping =>
            <td className="break-text" key={mapping.origem}>{display(item.dados[mapping.destino || mapping.novo!.chave])}</td>)}</tr>)}</tbody>
        </table></div>
        <div className="actions"><button className="button" type="button" disabled={busy || report.invalidos > 0} onClick={execute}>
          <FileUp size={16}/>{busy ? "Importando..." : "Confirmar importacao"}</button></div>
      </section>}
    </>}
    {result && <section className="panel stack"><h2>Resultado da importacao</h2>
      <div className="detail-grid"><Fact label="Status" value={result.status}/><Fact label="Importados" value={result.processados}/><Fact label="Total" value={result.total}/></div>
      <div className="actions"><Link className="button" href={base}><Check size={16}/>Ver registros</Link>
        {result.status !== "CONCLUIDA" && <button className="button secondary" type="button" disabled={busy} onClick={() => retomar(result)}><RotateCcw size={16}/>Retomar importacao</button>}
        <button className="button secondary" type="button" disabled={busy} onClick={reset}><Plus size={16}/>Nova importacao</button></div>
    </section>}
    {historyError && <p className="error" role="alert">{historyError}</p>}
    {history.length > 0 && <section className="panel stack"><h2>Importacoes recentes</h2>
      <div className="table-wrap"><table className="table" aria-label="Importacoes recentes"><thead><tr><th>Data</th><th>Status</th><th>Importados</th><th>Acoes</th></tr></thead>
        <tbody>{history.map(job => <tr key={job.id}><td>{new Date(job.criado_em).toLocaleString("pt-BR")}</td><td>{job.status}</td><td>{job.processados} de {job.total}</td>
          <td>{job.status !== "CONCLUIDA" && <button className="icon-button" type="button" title="Retomar importacao" aria-label="Retomar importacao" disabled={busy} onClick={() => retomar(job)}><RotateCcw size={16}/></button>}</td>
        </tr>)}</tbody>
      </table></div>
    </section>}
  </div>;
}

function Fact({ label, value }: { label: string; value: number | string }) {
  return <div className="detail-item"><span>{label}</span><strong>{value}</strong></div>;
}
function display(value: unknown): string {
  if (value === undefined || value === null || value === "") return "-";
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}
