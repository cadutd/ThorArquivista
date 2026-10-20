const assert = require("node:assert/strict");
const path = require("node:path"), os = require("node:os");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true", "Use somente a stack isolada.");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(), errors = [];
  page.on("pageerror", error => errors.push(error.message));
  let instrument;
  async function json(response) {
    assert.ok(response.ok(), response.status() + ": " + await response.text());
    return response.json();
  }
  async function ready() {
    await expect(page.locator("table")).toHaveAttribute("aria-busy", "false");
    await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
  }
  async function change(action) {
    const response = page.waitForResponse(r => r.url() === api + "/instrumentos/" + instrument.id + "/registros/consultar");
    await action();
    const result = await response;
    const data = await json(result);
    await ready();
    return { data, payload: result.request().postDataJSON() };
  }
  async function submit(term, enter = false) {
    await page.getByPlaceholder("Busca simples").fill(term);
    return change(() => enter ? page.getByPlaceholder("Busca simples").press("Enter") :
      page.getByRole("button", { name: "Buscar", exact: true }).click());
  }
  async function screenshot(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Sem overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-registros-" + label + ".png") });
  }

  try {
    await page.goto(base + "/login");
    await page.getByRole("button", { name: "Entrar em desenvolvimento" }).click();
    await page.waitForURL("**/dashboard");
    instrument = await json(await context.request.post(api + "/instrumentos", {
      data: { nome: "Smoke registros " + Date.now(), tipo: "CATALOGO" }
    }));
    const prefix = api + "/instrumentos/" + instrument.id, listPath = "/instrumentos/" + instrument.id + "/registros";
    await json(await context.request.post(prefix + "/campos", {
      data: { nome: "Titulo", chave: "titulo", tipo: "TEXTO_CURTO", obrigatorio: true, aparece_busca: true }
    }));
    await json(await context.request.post(prefix + "/campos", {
      data: { nome: "Confirmado", chave: "confirmado", tipo: "BOOLEANO", obrigatorio: true }
    }));
    await json(await context.request.post(prefix + "/registros", {
      data: { dados: { titulo: "Outro registro", confirmado: false }, status: "INATIVO" }
    }));
    for (let i = 0; i < 51; i++) await json(await context.request.post(prefix + "/registros", {
      data: { dados: { titulo: "Correspondencia " + i, confirmado: true } }
    }));
    await page.goto(base + listPath); await ready();
    assert.equal(await page.locator(".crud-pagination").count(), 2);
    assert.equal(await page.locator("tbody tr").count(), 20);
    await expect(page.locator(".crud-pagination").first()).toContainText("52");
    const search = await submit("  Correspondencia  ");
    assert.equal(search.payload.q, "Correspondencia");
    assert.equal(search.data.total, 51);
    assert.equal(await page.locator("tbody tr").count(), 20);
    await page.getByPlaceholder("Busca simples").fill("Outro");
    const next = await change(() => page.getByTitle("Proxima pagina", { exact: true }).first().click());
    assert.equal(next.payload.q, "Correspondencia");
    assert.equal(next.payload.offset, 20);
    assert.ok(!(await page.locator("tbody").innerText()).includes("Outro registro"));
    const last = await change(() => page.getByTitle("Ultima pagina", { exact: true }).last().click());
    assert.equal(last.payload.offset, 40);
    assert.equal(await page.locator("tbody tr").count(), 11);
    const resized = await change(() => page.getByRole("combobox", { name: "Registros por pagina" }).first().selectOption("50"));
    assert.equal(resized.payload.offset, 0);
    assert.equal(await page.locator("tbody tr").count(), 50);
    await expect(page.getByRole("combobox", { name: "Registros por pagina" }).last()).toHaveValue("50");
    await submit("outro", true);
    assert.equal(await page.locator("tbody tr").count(), 1);
    await submit("sem-correspondencia");
    await expect(page.getByText("Nenhum registro encontrado.")).toBeVisible();
    await change(() => page.getByRole("button", { name: "Limpar filtros", exact: true }).click());
    await page.getByRole("button", { name: "Filtros avancados" }).click();
    await page.getByLabel("Status", { exact: true }).selectOption("INATIVO");
    await page.getByLabel("Confirmado", { exact: true }).selectOption("false");
    const advanced = await submit("");
    assert.equal(advanced.data.total, 1);
    assert.equal(advanced.payload.filtros.confirmado, false);
    await expect(page.locator("tbody")).toContainText("Outro registro");
    await change(() => page.getByRole("button", { name: "Limpar filtros", exact: true }).click());
    await page.getByLabel("Titulo", { exact: true }).fill("Correspondencia 17");
    const metadata = await submit("");
    assert.equal(metadata.data.total, 1);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator("tbody").getByRole("link", { name: "Correspondencia 17", exact: true })).toHaveClass("crud-record-link");
    for (const label of ["Visualizar registro", "Editar registro", "Excluir registro"])
      await expect(page.locator("tbody").getByLabel(label, { exact: true })).toHaveAttribute("title", label);
    await screenshot("lista-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await screenshot("lista-mobile");
    await page.setViewportSize({ width: 1440, height: 1000 });

    await page.getByRole("link", { name: "Novo registro", exact: true }).click();
    await expect(page).toHaveURL(base + listPath + "/novo");
    await page.getByLabel("Titulo *", { exact: true }).fill("Registro criado no formulario");
    await screenshot("inclusao-desktop");
    await page.getByRole("button", { name: "Salvar registro", exact: true }).click();
    await expect(page).toHaveURL(base + listPath); await ready();
    await submit("Registro criado no formulario");
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page.getByRole("link", { name: "Editar registro", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Editar registro", exact: true })).toBeVisible();
    await expect(page.getByLabel("Titulo *", { exact: true })).toHaveValue("Registro criado no formulario");
    await expect(page.getByLabel("Confirmado *", { exact: true })).toHaveValue("false");
    await page.getByLabel("Titulo *", { exact: true }).fill("Registro editado no formulario");
    await page.setViewportSize({ width: 390, height: 844 }); await screenshot("edicao-mobile");
    await page.getByRole("button", { name: "Salvar registro", exact: true }).click();
    await expect(page).toHaveURL(base + listPath); await ready();
    await submit("Registro editado no formulario");
    await page.getByRole("link", { name: "Visualizar registro", exact: true }).click();
    await expect(page.getByRole("tab", { name: "Metadados", exact: true })).toBeVisible();
    await expect(page.getByRole("tabpanel")).toContainText("Registro editado no formulario");
    await screenshot("detalhes-mobile");
    await page.getByRole("link", { name: "Voltar", exact: true }).click(); await ready();
    await submit("Registro editado no formulario");
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByRole("button", { name: "Excluir registro", exact: true }).click();
    await expect(page.locator("tbody tr")).toHaveCount(1);
    page.once("dialog", dialog => dialog.accept());
    const deleted = await change(() => page.getByRole("button", { name: "Excluir registro", exact: true }).click());
    assert.equal(deleted.data.total, 0);
    await expect(page.getByText("Nenhum registro encontrado.")).toBeVisible();
    assert.deepEqual(errors, []);
    assert.deepEqual(await page.locator(".error").allTextContents(), []);
    console.log("PASS: paginacao dupla, tamanho/ultima pagina, filtros tipados, busca/Enter/limpar, CRUD, confirmacao e desktop/mobile.");
  } catch (error) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-registros-falha.png") }).catch(() => {});
    throw error;
  } finally {
    if (instrument) await context.request.delete(api + "/instrumentos/" + instrument.id);
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
