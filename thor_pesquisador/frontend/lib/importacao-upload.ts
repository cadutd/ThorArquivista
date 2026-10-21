import { ApiError } from "./api";
import { acionarImportacao, CHUNK_BYTES, MAX_CHUNK_BYTES, criarImportacao, enviarParteImportacao, obterImportacao } from "./importacoes-assincronas";
import type { JobImportacao } from "./importacoes-assincronas";

type UploadSalvo = { operacao_id: string; jobId?: string; chunkBytes: number };
const chave = (iid: string, file: File) => "thor:importacao:" + JSON.stringify([iid, file.name, file.size, file.lastModified]);
function ler(storage: Storage, key: string): UploadSalvo | undefined {
  try {
    const value = JSON.parse(storage.getItem(key) || "null");
    if (typeof value?.operacao_id === "string" && Number.isInteger(value.chunkBytes) && value.chunkBytes > 0 && value.chunkBytes <= MAX_CHUNK_BYTES)
      return value;
  } catch { /* Um registro local invalido nao deve impedir uma nova importacao. */ }
}
function salvar(storage: Storage, key: string, value: UploadSalvo) {
  try { storage.setItem(key, JSON.stringify(value)); }
  catch { throw new Error("Nao foi possivel salvar a retomada neste navegador. Libere o armazenamento local antes de enviar."); }
}

export async function uploadImportacao({ iid, file, storage, signal, chunkBytes = CHUNK_BYTES, jobId, onJob }: {
  iid: string; file: File; storage: Storage; signal: AbortSignal; chunkBytes?: number; jobId?: string;
  onJob: (job: JobImportacao) => void;
}) {
  const key = chave(iid, file);
  let saved = ler(storage, key);
  if (jobId && saved?.jobId !== jobId) saved = undefined;
  const size = Math.floor(Math.min(MAX_CHUNK_BYTES, chunkBytes));
  if (!Number.isFinite(size) || size < 1) throw new Error("Limite de bloco invalido.");
  saved ??= { operacao_id: crypto.randomUUID(), ...(jobId ? { jobId } : {}), chunkBytes: size };
  if (saved.chunkBytes > size) throw new Error("O limite de bloco mudou. Consulte a importacao antes de retomar o envio.");
  salvar(storage, key, saved);
  let job: JobImportacao;
  if (saved.jobId) {
    try { job = await obterImportacao(iid, saved.jobId, signal); }
    catch (err) {
      if (err instanceof ApiError && err.status === 404) throw new Error("Importacao nao encontrada. Consulte a central; a retomada local foi preservada.");
      throw err;
    }
  } else {
    job = await criarImportacao(iid, { operacao_id: saved.operacao_id, nome_arquivo: file.name, tamanho_bytes: file.size }, signal);
    saved.jobId = job.id;
    salvar(storage, key, saved);
    job = await obterImportacao(iid, job.id, signal);
  }
  if (job.nome_arquivo !== file.name || job.tamanho_bytes !== file.size)
    throw new Error("Selecione o arquivo original, com o mesmo nome e tamanho declarado.");
  onJob(job);
  if (job.status !== "RECEBENDO") return job;
  let offset = job.bytes_recebidos;
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > file.size || (offset < file.size && offset % saved.chunkBytes !== 0))
    throw new Error("Posicao de envio inconsistente. Consulte a importacao antes de retomar.");
  while (offset < file.size) {
    signal.throwIfAborted();
    const end = Math.min(offset + saved.chunkBytes, file.size);
    job = await enviarParteImportacao(iid, job.id, Math.floor(offset / saved.chunkBytes) + 1, file.slice(offset, end), signal);
    onJob(job);
    if (job.status !== "RECEBENDO") return job;
    if (job.bytes_recebidos !== end || job.tamanho_bytes !== file.size)
      throw new Error("O servidor nao confirmou o bloco enviado. Selecione o mesmo arquivo para retomar.");
    offset = job.bytes_recebidos;
  }
  signal.throwIfAborted();
  job = await acionarImportacao(iid, job.id, "finalizar", undefined, signal);
  onJob(job);
  return job;
}
