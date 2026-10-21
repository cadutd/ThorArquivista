const assert = require("node:assert/strict"), path = require("node:path"), os = require("node:os");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true", "Use somente a stack isolada.");
(async () => {
  const browser = await chromium.launch({ headless: true }), context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(), errors = [];
  let iid;
  page.on("pageerror", error => errors.push(error.message));
  async function json(response) { assert.ok(response.ok(), response.status() + ": " + await response.text()); return response.json(); }
  async function upload(name, content) {
    await page.getByLabel("Arquivo CSV ou JSON *", { exact: true }).setInputFiles({
      name, mimeType: name.endsWith(".csv") ? "text/csv" : "application/json", buffer: Buffer.from(content)
    });
    await page.getByRole("button", { name: "Analisar arquivo", exact: true }).click();
    await expect(page.getByRole("table", { name: "Associacao de campos", exact: true })).toBeVisible();
  }
  async function validate() {
    await page.getByRole("button", { name: "Validar importacao", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Conferencia", exact: true })).toBeVisible();
  }
  async function shot(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Sem overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacao-" + label + ".png") });
  }
  try {
    await page.goto(base + "/login");
    await page.getByRole("button", { name: "Entrar em desenvolvimento", exact: true }).click();
    await page.waitForURL("**/dashboard");
    iid = (await json(await context.request.post(api + "/instrumentos", { data: { nome: "Importacao E2E " + Date.now(), tipo: "CATALOGO" } }))).id;
    const prefix = api + "/instrumentos/" + iid, listPath = "/instrumentos/" + iid + "/registros";
    await json(await context.request.post(prefix + "/campos", { data: {
      nome: "Nome completo", chave: "titulo", tipo: "TEXTO_CURTO", obrigatorio: true
    } }));
    await page.goto(base + listPath);
    await page.getByRole("link", { name: "Importacoes", exact: true }).click();
    await page.getByRole("link", { name: "Importacao sincrona", exact: true }).click();
    await expect(page).toHaveURL(base + listPath + "/importar");
    await upload("pessoas.csv", "Nome;Idade;Chegada;Confirmado;Ignorada\nAna;0;31/12/1900;Sim;SEGREDO\nMaria;2,5;01/01/1901;Não;OUTRO");
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await page.getByRole("button", { name: "Criar campos nao associados", exact: true }).click();
    await page.getByLabel("Associar Ignorada", { exact: true }).selectOption("");
    await expect(page.getByLabel("Tipo do campo Idade", { exact: true })).toHaveValue("NUMERO");
    await expect(page.getByLabel("Tipo do campo Chegada", { exact: true })).toHaveValue("DATA");
    await expect(page.getByLabel("Tipo do campo Confirmado", { exact: true })).toHaveValue("BOOLEANO");
    await shot("associacao-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("associacao-mobile");
    await validate();
    const schemaBefore = await json(await context.request.get(prefix + "/schema"));
    assert.equal(schemaBefore.campos.length, 1, "Previa nao cria campos");
    const preview = page.getByRole("table", { name: "Previa de registros", exact: true });
    await expect(preview).toContainText("1900-12-31");
    await expect(preview).toContainText("Nao");
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeEnabled();
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 0);
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Resultado da importacao", exact: true })).toBeVisible();
    await expect(page.locator("body")).toContainText("CONCLUIDA");
    const rows = (await json(await context.request.get(prefix + "/registros"))).items;
    assert.equal(rows.length, 2);
    assert.deepEqual(rows.map(row => row.status_editorial), ["RASCUNHO", "RASCUNHO"]);
    assert.deepEqual(rows.find(row => row.dados.titulo === "Ana").dados, {
      titulo: "Ana", idade: 0, chegada: "1900-12-31", confirmado: true
    });
    assert.ok((await json(await context.request.get(prefix + "/schema"))).campos.every(field => !field.exibir_publico));
    await shot("resultado-mobile");
    await page.getByRole("link", { name: "Ver registros", exact: true }).click();
    await expect(page).toHaveURL(base + listPath);
    await expect(page.locator("tbody tr")).toHaveCount(2);

    await page.getByRole("link", { name: "Importacoes", exact: true }).click();
    await page.getByRole("link", { name: "Importacao sincrona", exact: true }).click();
    await upload("pessoas.json", JSON.stringify([{ Nome: "Jose", idade: 3 }]));
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await validate();
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Confirmar importacao", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Resultado da importacao", exact: true })).toBeVisible();
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 3);
    await page.getByRole("button", { name: "Nova importacao", exact: true }).click();
    await upload("invalido.csv", "Nome;idade\nCarlos;nao-numerico");
    await page.getByLabel("Associar Nome", { exact: true }).selectOption("titulo");
    await validate();
    await expect(page.getByRole("table", { name: "Erros de importacao", exact: true })).toContainText("NUMERO");
    await expect(page.getByRole("button", { name: "Confirmar importacao", exact: true })).toBeDisabled();
    assert.equal((await json(await context.request.get(prefix + "/registros"))).items.length, 3);
    assert.deepEqual(errors, []);
    console.log("PASS: CSV/JSON reais, associacao, criar/ignorar campos, previa sem mutacao, tipagem, confirmacao, rascunho, retorno, erros e desktop/mobile.");
  } catch (error) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-importacao-falha.png") }).catch(() => {});
    throw error;
  } finally {
    if (iid) {
      const current = await json(await context.request.get(api + "/instrumentos/" + iid));
      await context.request.post(api + "/instrumentos/" + iid + "/editorial/arquivar", {
        data: { versao: current.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Encerramento do teste isolado" }
      });
    }
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
