import assert from "node:assert/strict";
import { registerHooks } from "node:module";
import { readFileSync } from "node:fs";
import test from "node:test";

// O loader substitui somente o transporte; os contratos e o upload executam codigo real.
const root = new URL("../../", import.meta.url);
const source = path => readFileSync(new URL(path, root), "utf8");
const calls = [];
class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
globalThis.__thorAsyncTest = { ApiError, request: async (...args) => { calls.push(args); return {}; },
  downloadFile: async (...args) => calls.push(args) };
const transport = new URL("mock-async-api.mjs", import.meta.url).href;
const uploadTransport = new URL("mock-async-upload.mjs", import.meta.url).href;
const hook = registerHooks({
  resolve(specifier, context, next) {
    if (context.parentURL?.includes("/lib/importacoes-assincronas.ts") && specifier === "./api")
      return { url: transport, shortCircuit: true };
    if (context.parentURL?.includes("/lib/importacao-upload.ts")) {
      if (specifier === "./api") return { url: transport, shortCircuit: true };
      if (specifier === "./importacoes-assincronas") return { url: uploadTransport, shortCircuit: true };
    }
    return next(specifier, context);
  },
  load(url, context, next) {
    if (url === transport) return { format: "module", shortCircuit: true, source:
      "export const ApiError = globalThis.__thorAsyncTest.ApiError; export const request = (...a) => globalThis.__thorAsyncTest.request(...a); export const downloadFile = (...a) => globalThis.__thorAsyncTest.downloadFile(...a);" };
    if (url === uploadTransport) return { format: "module", shortCircuit: true, source:
      "export const CHUNK_BYTES = 8*1024*1024; export const MAX_CHUNK_BYTES = 16*1024*1024;" +
      ["obterImportacao", "criarImportacao", "enviarParteImportacao", "acionarImportacao"]
        .map(name => "export const " + name + " = (...a) => globalThis.__thorUploadTest." + name + "(...a);").join("") };
    return next(url, context);
  }
});
const api = await import(new URL("lib/importacoes-assincronas.ts", root));
const { uploadImportacao } = await import(new URL("lib/importacao-upload.ts", root));

test("API: prefixo, filtros paginados, JSON, multipart, limites e download autenticados", async () => {
  calls.length = 0;
  const signal = new AbortController().signal;
  await api.listarImportacoesAssincronas("iid", { q: "a & b", status: "PAUSADA", limit: 20, offset: 40 }, signal);
  const url = new URL(calls[0][0], "http://test");
  assert.equal(url.pathname, "/instrumentos/iid/registros/importacoes/assincronas");
  assert.deepEqual(Object.fromEntries(url.searchParams), { q: "a & b", status: "PAUSADA", limit: "20", offset: "40" });
  assert.equal(calls[0][1].signal, signal);
  await api.obterLimitesImportacao("iid", signal);
  assert.ok(calls.at(-1)[0].endsWith("/assincronas/limites"));
  const payload = { operacao_id: crypto.randomUUID(), nome_arquivo: "dados.csv", tamanho_bytes: 9 };
  await api.criarImportacao("iid", payload, signal);
  assert.deepEqual(JSON.parse(calls.at(-1)[1].body), payload);
  await api.obterImportacao("iid", "jid", signal);
  assert.ok(calls.at(-1)[0].endsWith("/assincronas/jid"));
  await api.enviarParteImportacao("iid", "jid", 1, new Blob(["conteudo"]), signal);
  assert.ok(calls.at(-1)[0].endsWith("/partes?numero=1"));
  assert.ok(calls.at(-1)[1].body instanceof FormData);
  assert.equal(calls.at(-1)[1].body.get("arquivo").size, 8);
  assert.equal(calls.at(-1)[1].headers, undefined);
  const configuration = { operacao_id: payload.operacao_id, schema_version: 3, mapeamentos: [{ origem: "Nome", destino: "nome" }] };
  for (const action of ["finalizar", "validar", "confirmar", "retomar", "cancelar"]) {
    await api.acionarImportacao("iid", "jid", action, action === "validar" ? configuration : undefined, signal);
    assert.ok(calls.at(-1)[0].endsWith("/jid/" + action));
    assert.equal(calls.at(-1)[1].method, "POST");
    if (action === "validar") assert.deepEqual(JSON.parse(calls.at(-1)[1].body), configuration);
  }
  await api.baixarErrosImportacao("iid", "jid");
  assert.deepEqual(calls.at(-1), ["/instrumentos/iid/registros/importacoes/assincronas/jid/erros", "importacao-jid-erros.csv"]);
});
test("estados terminais nao retomam, progresso separa fase de importados", () => {
  for (const state of ["CONCLUIDA", "CANCELADA", "EXPIRADA"]) {
    assert.equal(api.podeRetomarImportacao(state), false);
    assert.equal(api.podeCancelarImportacao(state), false);
    assert.equal(api.importacaoAtiva(state), false);
  }
  assert.equal(api.podeRetomarImportacao("PAUSADA"), true);
  assert.equal(api.podeRetomarImportacao("FALHOU"), true);
  assert.equal(api.importacaoAtiva("ERROS_VALIDACAO"), false);
  const job = { status: "VALIDANDO", total: 10, processados: 0, fase_processados: 7 };
  assert.deepEqual(api.progressoImportacao(job), { atual: 7, total: 10, percentual: 70 });
  assert.equal(api.progressoImportacao({ ...job, status: "IMPORTANDO", processados: 3 }).atual, 3);
  assert.equal(api.progressoImportacao({ ...job, status: "RECEBENDO", bytes_recebidos: 4, tamanho_bytes: 8 }).percentual, 50);
});

function scenario(size = api.CHUNK_BYTES + 7) {
  const entries = new Map(), events = [], chunks = [];
  const storage = { getItem: key => entries.get(key) ?? null, setItem: (key, value) => entries.set(key, value) };
  const file = new File([new Uint8Array(size)], "dados.csv", { lastModified: 1234 });
  const job = { id: crypto.randomUUID(), nome_arquivo: file.name, tamanho_bytes: file.size, bytes_recebidos: 0, status: "RECEBENDO" };
  const deps = {
    obterImportacao: async () => { events.push("get"); return { ...job }; },
    criarImportacao: async (_iid, payload) => {
      events.push(["create", payload]); assert.equal(entries.size, 1, "UUID salvo antes do POST"); return { ...job };
    },
    enviarParteImportacao: async (_iid, _jid, number, blob) => {
      events.push("parte"); chunks.push([number, blob.size]); job.bytes_recebidos += blob.size; return { ...job };
    },
    acionarImportacao: async (_iid, _jid, action) => {
      events.push(action); assert.equal(job.bytes_recebidos, size); job.status = "ANALISANDO"; return { ...job };
    }
  };
  globalThis.__thorUploadTest = deps;
  const run = (options = {}) => uploadImportacao({ iid: "iid", file, storage, signal: new AbortController().signal, onJob() {}, ...options });
  return { file, storage, entries, events, chunks, job, deps, run };
}
test("blocos sequenciais <=8MiB, numero inicia em 1, finalize apos ultimo byte", async () => {
  const s = scenario();
  assert.equal((await s.run()).status, "ANALISANDO");
  assert.deepEqual(s.chunks, [[1, api.CHUNK_BYTES], [2, 7]]);
  assert.deepEqual(s.events.filter(item => typeof item === "string"), ["get", "parte", "parte", "finalizar"]);
});
test("resposta perdida de parte: refresh retoma pelo GET sem duplicar bytes", async () => {
  const s = scenario(), original = s.deps.enviarParteImportacao;
  let lost = true;
  s.deps.enviarParteImportacao = async (...args) => {
    const result = await original(...args);
    if (lost) { lost = false; throw new Error("Conexao interrompida"); }
    return result;
  };
  await assert.rejects(s.run(), /Conexao/);
  assert.equal(s.job.bytes_recebidos, api.CHUNK_BYTES);
  await s.run({ file: new File([s.file], s.file.name, { lastModified: 1234 }) });
  assert.deepEqual(s.chunks, [[1, api.CHUNK_BYTES], [2, 7]]);
  assert.equal(s.events.filter(Array.isArray).length, 1, "nao recria job");
});
test("blocos de 16MiB do servidor sao respeitados e preservados na retomada", async () => {
  const s = scenario(api.MAX_CHUNK_BYTES + 7), original = s.deps.enviarParteImportacao;
  let lost = true;
  s.deps.enviarParteImportacao = async (...args) => {
    const value = await original(...args);
    if (lost) { lost = false; throw new Error("timeout"); }
    return value;
  };
  await assert.rejects(s.run({ chunkBytes: api.MAX_CHUNK_BYTES }), /timeout/);
  assert.equal(JSON.parse([...s.entries.values()][0]).chunkBytes, api.MAX_CHUNK_BYTES);
  await s.run({ chunkBytes: api.MAX_CHUNK_BYTES });
  assert.deepEqual(s.chunks, [[1, api.MAX_CHUNK_BYTES], [2, 7]]);
  assert.equal(s.events.filter(Array.isArray).length, 1, "registro local de 16MiB preserva job");
});
test("POST inicial com resposta perdida reutiliza operacao UUID", async () => {
  const s = scenario(3), create = s.deps.criarImportacao;
  let first = true;
  s.deps.criarImportacao = async (...args) => { const result = await create(...args); if (first) { first = false; throw new Error("timeout"); } return result; };
  await assert.rejects(s.run(), /timeout/);
  await s.run();
  const creations = s.events.filter(Array.isArray);
  assert.equal(creations.length, 2);
  assert.equal(creations[0][1].operacao_id, creations[1][1].operacao_id);
});
test("tamanho imutavel, offset invalido e armazenamento negado bloqueiam envio", async () => {
  let s = scenario(3); s.job.tamanho_bytes = 4;
  await assert.rejects(s.run(), /arquivo original/); assert.equal(s.chunks.length, 0);
  s = scenario(3); s.job.bytes_recebidos = 1;
  await assert.rejects(s.run(), /Posicao/); assert.equal(s.chunks.length, 0);
  s = scenario(3);
  await assert.rejects(s.run({ storage: { getItem() { return null; }, setItem() { throw new Error("quota"); } } }), /armazenamento/);
  assert.equal(s.events.length, 0);
});
test("pausa/falha/cancelamento nao reenviam fonte; abort nao finaliza", async () => {
  for (const status of ["PAUSADA", "FALHOU", "CANCELADA", "EXPIRADA", "CONCLUIDA"]) {
    const s = scenario(3); s.job.status = status;
    await s.run({ jobId: s.job.id });
    assert.equal(s.chunks.length, 0);
    assert.deepEqual(s.events, ["get"]);
  }
  const s = scenario(3), controller = new AbortController();
  s.deps.obterImportacao = async () => { controller.abort(); return { ...s.job }; };
  await assert.rejects(s.run({ signal: controller.signal }));
  assert.equal(s.events.includes("finalizar"), false);
});
test("rotas, identidade CRUD dupla, legado, permissoes e polling", () => {
  const list = source("components/importacoes-lista.tsx"), detail = source("components/importacao-detalhe.tsx");
  for (const route of ["page.tsx", "nova/page.tsx", "[jobId]/page.tsx"])
    assert.ok(source("app/instrumentos/[id]/registros/importacoes/" + route).includes("AppShell"));
  assert.ok(source("app/instrumentos/[id]/registros/page.tsx").includes('href={base + "/importacoes"}'));
  assert.equal(list.match(/\{pagination\}/g).length, 2);
  assert.ok(list.includes('href={base + "/importar"}'));
  assert.ok(detail.includes('usePermission("registros_incluir", id)'));
  assert.ok(detail.includes('usePermission("campos_incluir", id)'));
  assert.ok(detail.includes('document.addEventListener("visibilitychange"'));
  assert.ok(detail.includes('document.removeEventListener("visibilitychange"'));
  assert.ok(detail.includes("setTimeout(load, 3000)"));
  assert.ok(detail.includes("request?.abort()"));
  assert.ok(!detail.includes("exibir_publico") && !detail.includes("publicar"));
});
test.after(() => { hook.deregister(); delete globalThis.__thorAsyncTest; delete globalThis.__thorUploadTest; });
