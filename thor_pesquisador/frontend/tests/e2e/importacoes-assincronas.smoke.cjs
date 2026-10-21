const assert = require("node:assert/strict");
const os = require("node:os"), path = require("node:path");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL;
const chunkBytes = Number(process.env.THOR_E2E_CHUNK_BYTES || 8 * 1024 * 1024);
assert.ok([8 * 1024 * 1024, 16 * 1024 * 1024].includes(chunkBytes));
assert.ok(base && process.env.THOR_E2E_MOCK === "true", "Use frontend isolado e THOR_E2E_MOCK=true; nenhuma API real e acessada.");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const page = await context.newPage(), errors = [], calls = [], chunks = [], creations = [];
  page.setDefaultTimeout(10000);
  let permissions = ["registros_incluir", "campos_incluir", "registros_consultar"];
  const iid = "instrumento-teste", prefix = "/instrumentos/" + iid + "/registros";
  const route = prefix + "/importacoes", apiPrefix = prefix + "/importacoes/assincronas";
  const jobs = new Map(), now = new Date().toISOString();
  const campo = { id: "campo", nome: "Nome completo", chave: "titulo", tipo: "TEXTO_CURTO", obrigatorio: true };
  const fresh = (id, status = "CONCLUIDA") => ({
    id, status, phase: status, total: 2, processados: status === "CONCLUIDA" ? 2 : 0, fase_processados: 0,
    validos: 0, invalidos: 0, bytes_recebidos: 0, tamanho_bytes: 10, nome_arquivo: id + ".csv", erro: null,
    analise: null, configuracao: null, relatorio: null, criado_em: now, atualizado_em: now,
    expira_em: "2099-01-01T00:00:00Z", velocidade: 2, estimativa_segundos: 1
  });
  for (let i = 0; i < 23; i++) jobs.set("historico-" + i, fresh("historico-" + i, i === 0 ? "FALHOU" : i === 1 ? "PAUSADA" : "CONCLUIDA"));
  jobs.set("cancelada", fresh("cancelada", "CANCELADA"));
  let failedPart = false, validations = 0, polls = 0, advance = true, activeId;
  page.on("pageerror", error => errors.push(error.message));
  await context.route("**/api/v1/**", async interception => {
    const request = interception.request(), url = new URL(request.url()), method = request.method();
    const endpoint = url.pathname.replace("/api/v1", "");
    calls.push({ endpoint, method, search: url.search });
    const reply = (body, status = 200, headers = {}) => interception.fulfill({ status,
      headers: { "access-control-allow-origin": new URL(base).origin, "access-control-allow-credentials": "true", ...headers },
      contentType: typeof body === "string" ? "text/csv" : "application/json", body: typeof body === "string" ? body : JSON.stringify(body) });
    if (method === "OPTIONS") return reply({}, 204);
    if (endpoint === "/auth/me") return reply({ id: "usuario", nome: "Teste" });
    if (endpoint === "/auth/permissoes") return reply({ permissoes: permissions, escopos: {} });
    if (endpoint === "/instrumentos/" + iid + "/schema") return reply({ nome: "Instrumento de teste", campos: [campo] });
    if (endpoint === prefix + "/consultar") return reply({ items: [], total: 0 });
    if (endpoint === prefix + "/importacoes") return reply([]);
    if (endpoint === apiPrefix + "/limites") return reply({ max_bytes: 64 * 1024 * 1024, max_registros: 100000, chunk_bytes: chunkBytes });
    if (endpoint === apiPrefix && method === "GET") {
      const selected = [...jobs.values()].filter(job => (!url.searchParams.get("q") || job.nome_arquivo.includes(url.searchParams.get("q"))) &&
        (!url.searchParams.get("status") || job.status === url.searchParams.get("status")));
      const limit = Number(url.searchParams.get("limit")), offset = Number(url.searchParams.get("offset"));
      return reply({ items: selected.slice(offset, offset + limit), total: selected.length, limit, offset });
    }
    if (endpoint === apiPrefix && method === "POST") {
      const payload = request.postDataJSON(); creations.push(payload);
      assert.match(payload.operacao_id, /^[0-9a-f-]{36}$/);
      const existing = [...jobs.values()].find(job => job.operation === payload.operacao_id);
      if (existing) return reply(existing);
      activeId = "upload-teste";
      const job = { ...fresh(activeId, "RECEBENDO"), nome_arquivo: payload.nome_arquivo,
        tamanho_bytes: payload.tamanho_bytes, operation: payload.operacao_id };
      jobs.set(activeId, job); return reply(job);
    }
    if (endpoint.startsWith(apiPrefix + "/")) {
      const [jid, action] = endpoint.slice(apiPrefix.length + 1).split("/");
      const job = jobs.get(jid);
      if (!job) return reply({ detail: "Nao encontrado" }, 404);
      if (!action) {
        if (jid === activeId && advance) {
          polls++;
          if (job.status === "ANALISANDO" && polls >= 2) {
            job.status = "AGUARDANDO_MAPA"; job.phase = job.status; job.fase_processados = 2;
            job.analise = { nome: job.nome_arquivo, schema_version: 4, campos: [campo], colunas: [
              { origem: "Nome", chave_sugerida: "nome", tipo_sugerido: "TEXTO_CURTO", amostras: ["Ana"] },
              { origem: "Idade", chave_sugerida: "idade", tipo_sugerido: "NUMERO", amostras: [0] },
              { origem: "Ignorada", chave_sugerida: "ignorada", tipo_sugerido: "TEXTO_CURTO", amostras: ["ignorar"] }
            ] };
          }
          if (job.status === "VALIDANDO" && polls >= 2) {
            job.status = validations === 1 ? "ERROS_VALIDACAO" : "AGUARDANDO_CONFIRMACAO";
            job.phase = job.status; job.fase_processados = 2;
            job.relatorio = { total: 2, validos: validations === 1 ? 1 : 2, invalidos: validations === 1 ? 1 : 0,
              erros: validations === 1 ? [{ linha: 2, campo: "idade", mensagem: "Numero invalido" }] : [],
              previa: [{ linha: 1, dados: { titulo: "Ana", idade: 0 } }] };
          }
          if (job.status === "PENDENTE" && polls >= 2) { job.status = "IMPORTANDO"; job.phase = job.status; polls = 0; }
          if (job.status === "IMPORTANDO" && polls >= 2) { job.status = "CONCLUIDA"; job.phase = job.status; job.processados = 2; }
        }
        return reply(job);
      }
      if (action === "partes") {
        const numero = Number(url.searchParams.get("numero"));
        if (numero === 2 && !failedPart) { failedPart = true; return reply({ detail: "Conexao interrompida no teste" }, 503); }
        const body = request.postDataBuffer(), start = body.indexOf(Buffer.from("\r\n\r\n")) + 4;
        const end = body.lastIndexOf(Buffer.from("\r\n--"));
        const length = end - start;
        assert.ok(length > 0 && length <= chunkBytes);
        assert.equal(numero, Math.floor(job.bytes_recebidos / chunkBytes) + 1);
        chunks.push([numero, length]); job.bytes_recebidos += length;
        return reply(job);
      }
      if (action === "finalizar") {
        assert.equal(job.bytes_recebidos, job.tamanho_bytes); job.status = "ANALISANDO"; polls = 0; return reply(job, 202);
      }
      if (action === "validar") {
        const configuration = request.postDataJSON();
        assert.equal(configuration.schema_version, 4);
        assert.equal(configuration.mapeamentos.length, 2);
        job.configuracao = configuration; job.status = "VALIDANDO"; validations++; polls = 0; return reply(job, 202);
      }
      if (action === "confirmar") {
        assert.equal(job.relatorio.invalidos, 0); job.status = "PENDENTE"; polls = 0; return reply(job, 202);
      }
      if (action === "retomar") {
        assert.ok(["FALHOU", "PAUSADA"].includes(job.status)); assert.equal(request.postData(), null);
        job.status = "ANALISANDO"; return reply(job);
      }
      if (action === "cancelar") { job.status = "CANCELADA"; return reply(job); }
      if (action === "erros") return reply("linha,campo,mensagem\n2,idade,Numero invalido", 200, { "content-disposition": 'attachment; filename="erros.csv"' });
    }
    throw new Error("Requisicao nao simulada: " + method + " " + endpoint);
  });
  async function shot(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Sem overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacoes-async-" + label + ".png"), fullPage: true });
  }
  async function file() {
    await page.locator('input[type="file"]').evaluate((input, size) => {
      const data = new DataTransfer();
      data.items.add(new File([new Uint8Array(size + 17)], "arquivo-teste.csv", { type: "text/csv", lastModified: 1234 }));
      input.files = data.files; input.dispatchEvent(new Event("change", { bubbles: true }));
    }, chunkBytes);
  }
  try {
    await page.goto(base + prefix);
    await page.getByRole("link", { name: "Importacoes", exact: true }).click();
    await expect(page).toHaveURL(base + route);
    await expect(page.locator(".crud-pagination")).toHaveCount(2);
    await expect(page.getByRole("table", { name: "Importacoes", exact: true }).locator("tbody tr")).toHaveCount(20);
    await page.getByTitle("Proxima pagina", { exact: true }).first().click();
    await expect(page.getByRole("table", { name: "Importacoes", exact: true }).locator("tbody tr")).toHaveCount(4);
    await page.getByRole("button", { name: "Filtros avancados", exact: true }).click();
    await page.getByLabel(/^Status/).selectOption("CANCELADA");
    await page.getByLabel("Busca simples", { exact: true }).fill("cancelada");
    await page.getByLabel("Busca simples", { exact: true }).press("Enter");
    await expect(page.getByRole("table", { name: "Importacoes", exact: true }).locator("tbody tr")).toHaveCount(1);
    assert.ok(calls.some(call => call.search.includes("offset=0") && call.search.includes("status=CANCELADA") && call.search.includes("q=cancelada")));
    await expect(page.getByRole("button", { name: "Retomar importacao", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Cancelar importacao", exact: true })).toHaveCount(0);
    await shot("lista-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("lista-mobile");
    await page.getByRole("button", { name: "Limpar filtros", exact: true }).click();
    await page.getByRole("button", { name: "Retomar importacao", exact: true }).first().click();
    await expect(page.getByRole("button", { name: "Retomar importacao", exact: true })).toHaveCount(1);
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByRole("button", { name: "Cancelar importacao", exact: true }).first().click();
    assert.equal(calls.filter(call => call.endpoint.endsWith("/cancelar")).length, 0);
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Cancelar importacao", exact: true }).first().click();
    await expect.poll(() => calls.filter(call => call.endpoint.endsWith("/cancelar")).length).toBe(1);

    await page.getByRole("link", { name: "Nova importacao", exact: true }).click();
    await file();
    await page.getByRole("button", { name: "Enviar arquivo", exact: true }).click();
    await expect(page.locator("p.error[role=alert]")).toContainText("Conexao interrompida");
    await page.reload(); await file();
    await page.getByRole("button", { name: "Enviar arquivo", exact: true }).click();
    await expect(page).toHaveURL(base + route + "/upload-teste");
    assert.deepEqual(chunks, [[1, chunkBytes], [2, 17]]);
    assert.equal(creations.length, 1);
    await expect(page.getByRole("heading", { name: "Associacao de campos", exact: true })).toBeVisible({ timeout: 12000 });
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await page.getByLabel("Associar Idade", { exact: true }).selectOption("__novo");
    await expect(page.getByLabel("Tipo do campo Idade", { exact: true })).toHaveValue("NUMERO");
    await shot("mapa-mobile"); await page.setViewportSize({ width: 1440, height: 1000 }); await shot("mapa-desktop");
    await page.getByRole("button", { name: "Validar importacao", exact: true }).click();
    await expect(page.getByRole("table", { name: "Erros de importacao", exact: true })).toBeVisible({ timeout: 12000 });
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeDisabled();
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Baixar erros CSV", exact: true }).click();
    assert.match((await download).suggestedFilename(), /erros.*\.csv$/);
    await page.getByRole("button", { name: "Validar importacao", exact: true }).click();
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeEnabled({ timeout: 12000 });
    await expect(page.getByRole("table", { name: "Previa de registros", exact: true })).toContainText("0");
    await page.getByLabel("Nome do campo Idade", { exact: true }).fill("Idade corrigida");
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeDisabled();
    await page.getByRole("button", { name: "Validar importacao", exact: true }).click();
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeEnabled({ timeout: 12000 });
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    assert.equal(calls.filter(call => call.endpoint.endsWith("/confirmar")).length, 0);
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    await expect(page.getByRole("link", { name: "Ver registros", exact: true })).toBeVisible({ timeout: 20000 });
    const getCount = () => calls.filter(call => call.endpoint === apiPrefix + "/upload-teste" && call.method === "GET").length;
    let count = getCount(); await page.waitForTimeout(3300); assert.equal(getCount(), count, "terminal para polling");
    await shot("resultado-desktop"); await page.setViewportSize({ width: 390, height: 844 }); await shot("resultado-mobile");

    jobs.get(activeId).status = "ANALISANDO"; advance = false;
    await page.reload(); await expect(page.getByLabel("Progresso da importacao", { exact: true })).toBeVisible();
    await page.evaluate(() => { Object.defineProperty(document, "hidden", { configurable: true, value: true }); document.dispatchEvent(new Event("visibilitychange")); });
    await page.waitForTimeout(100); count = getCount(); await page.waitForTimeout(3300); assert.equal(getCount(), count, "aba oculta para polling");
    await page.evaluate(() => { Object.defineProperty(document, "hidden", { configurable: true, value: false }); document.dispatchEvent(new Event("visibilitychange")); });
    await expect.poll(getCount).toBeGreaterThan(count);
    await page.getByRole("link", { name: "Voltar", exact: true }).click();
    count = getCount(); await page.waitForTimeout(3300); assert.equal(getCount(), count, "unmount para polling");
    await page.getByRole("link", { name: "Importacao sincrona", exact: true }).click();
    await expect(page).toHaveURL(base + prefix + "/importar");
    await expect(page.getByRole("button", { name: "Analisar arquivo", exact: true })).toBeVisible();

    permissions = ["registros_incluir"];
    jobs.get(activeId).status = "AGUARDANDO_CONFIRMACAO";
    await page.goto(base + route + "/" + activeId);
    await expect(page.getByRole("heading", { name: "Associacao de campos", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Criar campos nao associados", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeDisabled();
    permissions = ["registros_consultar"];
    const before = calls.filter(call => call.endpoint === apiPrefix && call.method === "POST").length;
    await page.goto(base + route + "/nova");
    await expect(page.getByRole("status")).toContainText("Sem permissao");
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
    assert.equal(calls.filter(call => call.endpoint === apiPrefix && call.method === "POST").length, before);
    assert.deepEqual(errors, []);
    console.log("PASS: central CRUD, filtros/paginacao dupla, retomar/cancelar, upload >8MiB e refresh, mapa, validacao/CSV, confirmar, permissoes, polling e desktop/mobile; API 100% simulada.");
  } catch (error) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacoes-async-falha.png"), fullPage: true }).catch(() => {});
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
