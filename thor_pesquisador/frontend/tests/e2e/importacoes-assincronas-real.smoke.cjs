const assert = require("node:assert/strict"), path = require("node:path"), os = require("node:os");
const { execFileSync } = require("node:child_process");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(process.env.THOR_E2E_ISOLATED === "true" && base === "http://localhost:3001" &&
  api === "http://localhost:8001/api/v1", "Use somente a stack Docker isolada.");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const page = await context.newPage(), errors = [];
  let iid;
  page.setDefaultTimeout(15000);
  page.on("pageerror", error => errors.push(error.message));
  async function json(response) {
    assert.ok(response.ok(), response.status() + ": " + await response.text());
    return response.json();
  }
  function python(lines) {
    return execFileSync("docker", ["compose", "-f", path.resolve(__dirname, "../../../docker-compose.test.yml"),
      "exec", "-T", "backend", "python", "-c", lines.join("\n")], { encoding: "utf8" }).trim();
  }
  async function shot(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacoes-real-" + label + ".png"), fullPage: true });
    if (process.env.AXE_SCRIPT) {
      await page.addScriptTag({ path: process.env.AXE_SCRIPT });
      const violations = await page.evaluate(async () => (await axe.run()).violations
        .filter(item => ["critical", "serious"].includes(item.impact)).map(item => ({
          id: item.id, nodes: item.nodes.map(node => ({ target: node.target, html: node.html }))
        })));
      assert.deepEqual(violations, [], "Acessibilidade: " + label);
    }
  }
  async function status(jid, expected) {
    await expect.poll(async () => (await json(await context.request.get(api + "/instrumentos/" + iid +
      "/registros/importacoes/assincronas/" + jid))).status, { timeout: 30000 }).toBe(expected);
  }
  async function upload(name, content) {
    await page.goto(base + "/instrumentos/" + iid + "/registros/importacoes/nova");
    await page.locator('input[type="file"]').setInputFiles({ name, mimeType: "application/octet-stream", buffer: Buffer.from(content) });
    await page.getByRole("button", { name: "Enviar arquivo", exact: true }).click();
    await page.waitForURL(/\/registros\/importacoes\/[0-9a-f-]{36}$/);
    const jid = page.url().split("/").pop();
    await status(jid, "AGUARDANDO_MAPA");
    await expect(page.getByRole("heading", { name: "Associacao de campos", exact: true })).toBeVisible();
    return jid;
  }
  async function validate(jid, expected = "AGUARDANDO_CONFIRMACAO") {
    await page.getByRole("button", { name: "Validar importacao", exact: true }).click();
    await status(jid, expected);
    if (expected === "AGUARDANDO_CONFIRMACAO")
      await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeEnabled();
    else await expect(page.getByRole("table", { name: "Erros de importacao", exact: true })).toBeVisible();
  }
  async function confirm(jid) {
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    await status(jid, "CONCLUIDA");
    await expect(page.getByRole("link", { name: "Ver registros", exact: true })).toBeVisible();
  }
  try {
    const session = JSON.parse(python([
      "import json, uuid",
      "from app.core.config import settings",
      "from app.db.session import SessionLocal",
      "from app.models.user import Usuario",
      "from app.models.editorial import AcessoInstrumento",
      "from app.services.auth_service import create_session",
      "assert settings.app_env == 'test' and settings.mongodb_database.endswith('_test')",
      "with SessionLocal() as db:",
      "    user = Usuario(nome='Importacao browser ' + uuid.uuid4().hex)",
      "    db.add(user); db.flush()",
      "    db.add(AcessoInstrumento(usuario_id=user.id, papel='ADMIN')); db.commit()",
      "    print(json.dumps({'name': settings.session_cookie_name, 'value': create_session(db, user)}))",
    ]));
    await context.addCookies([{ ...session, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax" }]);
    iid = (await json(await context.request.post(api + "/instrumentos", { data: {
      nome: "Importacao assincrona E2E " + Date.now(), tipo: "CATALOGO"
    } }))).id;
    const prefix = api + "/instrumentos/" + iid;
    await json(await context.request.post(prefix + "/campos", { data: {
      nome: "Nome completo", chave: "titulo", tipo: "TEXTO_CURTO", obrigatorio: true
    } }));
    const csv = await upload("pessoas.csv", "Nome;Idade\nAna;0\nMaria;2,5");
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await page.getByLabel("Associar Idade", { exact: true }).selectOption("__novo");
    await expect(page.getByLabel("Tipo do campo Idade", { exact: true })).toHaveValue("NUMERO");
    await shot("mapa-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("mapa-mobile");
    await validate(csv);
    assert.equal((await json(await context.request.get(prefix + "/schema"))).campos.length, 1);
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 0);
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 0);
    await confirm(csv);
    const rows = (await json(await context.request.get(prefix + "/registros"))).items;
    assert.equal(rows.length, 2);
    assert.ok(rows.every(row => row.status_editorial === "RASCUNHO"));
    assert.equal(rows.find(row => row.dados.titulo === "Ana").dados.idade, 0);
    assert.equal(rows.find(row => row.dados.titulo === "Maria").dados.idade, 2.5);
    assert.ok((await json(await context.request.get(prefix + "/schema"))).campos.every(field => !field.exibir_publico));
    const repeated = await json(await context.request.post(prefix + "/registros/importacoes/assincronas/" + csv + "/confirmar"));
    assert.equal(repeated.processados, 2);
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 2);
    await shot("concluida-mobile");
    await page.setViewportSize({ width: 1440, height: 1000 }); await shot("concluida-desktop");
    const j = await upload("pessoas.json", '[{"Nome":"Carlos","idade":3}]');
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await validate(j); await confirm(j);
    const invalid = await upload("invalido.csv", "Nome;idade\nTeste;invalido");
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await validate(invalid, "ERROS_VALIDACAO");
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeDisabled();
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Baixar erros CSV", exact: true }).click();
    assert.match((await download).suggestedFilename(), /erros\.csv$/);
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Cancelar importacao", exact: true }).click();
    await status(invalid, "CANCELADA");
    await expect(page.getByRole("button", { name: "Retomar importacao", exact: true })).toHaveCount(0);
    const lines = await upload("pessoas.jsonl", '{"Nome":"Dora","idade":4}\n');
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await validate(lines); await confirm(lines);
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 4);
    await page.getByRole("link", { name: "Voltar", exact: true }).click();
    await expect(page.locator(".crud-pagination")).toHaveCount(2);
    await expect(page.getByRole("table", { name: "Importacoes", exact: true }).locator("tbody tr")).toHaveCount(4);
    await shot("lista-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("lista-mobile");
    assert.deepEqual(errors, []);
    console.log("PASS: CSV/JSON/JSONL via navegador, API/worker/S3/SQL/Mongo reais, mapeamento, novos campos, previa sem mutacao, idempotencia, rascunhos, erros CSV, cancelamento, paginacao e desktop/mobile.");
  } catch (error) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacoes-real-falha.png"), fullPage: true }).catch(() => {});
    throw error;
  } finally {
    if (iid) {
      const current = await json(await context.request.get(api + "/instrumentos/" + iid));
      await context.request.post(api + "/instrumentos/" + iid + "/editorial/arquivar", { data: {
        versao: current.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Encerramento do teste isolado"
      } });
    }
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
