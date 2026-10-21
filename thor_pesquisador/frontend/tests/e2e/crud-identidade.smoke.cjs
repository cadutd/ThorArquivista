const assert = require("node:assert/strict"), path = require("node:path"), os = require("node:os");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base === "http://localhost:3001" && api === "http://localhost:8001/api/v1" &&
  process.env.THOR_E2E_ISOLATED === "true", "Use somente a stack isolada.");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(), errors = [], deletions = [], ids = new Set();
  let imageId;
  page.on("pageerror", err => errors.push(err.message));
  page.on("request", req => { if (req.method() === "DELETE") deletions.push(req.url()); });
  async function json(response) { assert.ok(response.ok(), response.status() + ": " + await response.text()); return response.json(); }
  async function shot(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-crud-identidade-" + label + ".png"), fullPage: true });
    if (process.env.AXE_SCRIPT) {
      await page.addScriptTag({ path: process.env.AXE_SCRIPT });
      const violations = await page.evaluate(async () => (await axe.run()).violations
        .filter(v => ["serious", "critical"].includes(v.impact)).map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })));
      assert.deepEqual(violations, [], "Axe: " + label);
    }
  }
  try {
    await page.goto(base + "/login");
    await page.getByRole("button", { name: "Entrar em desenvolvimento", exact: true }).click();
    await page.waitForURL("**/dashboard");
    await page.goto(base + "/instrumentos/novo");
    const name = "Identidade CRUD " + Date.now();
    await page.getByLabel("Nome *", { exact: true }).fill(name);
    await page.getByLabel("Descricao", { exact: true }).fill("Descricao completa\nSegunda linha preservada.");
    const upload = page.waitForResponse(r => r.url() === api + "/instrumentos/imagens-card" && r.request().method() === "POST");
    await page.getByLabel("Imagem do card", { exact: true }).setInputFiles(path.resolve(__dirname, "../../public/images/login_pesquisador.png"));
    const cover = await json(await upload);
    await expect(page.locator(".instrumento-cover-preview img")).toHaveJSProperty("naturalWidth", 960);
    await shot("inclusao-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("inclusao-mobile");
    const created = page.waitForResponse(r => r.url() === api + "/instrumentos" && r.request().method() === "POST");
    await page.getByRole("button", { name: "Salvar instrumento", exact: true }).click();
    const inst = await json(await created); ids.add(inst.id);
    await expect(page).toHaveURL(base + "/instrumentos");
    await page.getByLabel("Busca simples", { exact: true }).fill(name);
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    const row = page.locator("tbody tr").filter({ hasText: name });
    await expect(row).toHaveCount(1);
    await expect(row.getByRole("button", { name: /Excluir/ })).toHaveCount(0);
    const icon = row.getByTitle("Visualizar", { exact: true });
    assert.deepEqual(await icon.evaluate(el => {
      const s = getComputedStyle(el); return [s.backgroundColor, s.borderTopColor, s.width, s.height];
    }), ["rgba(0, 0, 0, 0)", "rgba(0, 0, 0, 0)", "40px", "40px"]);
    await shot("lista-mobile");
    await page.setViewportSize({ width: 1440, height: 1000 }); await shot("lista-desktop");
    await icon.click();
    await expect(page.getByRole("heading", { name: "Visualizar instrumento", exact: true })).toBeVisible();
    for (const label of ["ID","Nome","Tipo","Status","Visibilidade","Versao do schema","Versao editorial",
      "Publicacao (ID)","Criado em","Atualizado em","Descricao","Imagem do card","Imagem do card (ID)"])
      await expect(page.locator("dt").filter({ hasText: new RegExp("^" + label.replace(/[()]/g, "\\$&") + "$") })).toHaveCount(1);
    await expect(page.locator(".crud-details")).toContainText(inst.id);
    await expect(page.locator(".crud-details")).toContainText(cover.id);
    await expect(page.getByAltText("Imagem do instrumento " + name)).toHaveJSProperty("naturalWidth", 960);
    await shot("detalhes-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("detalhes-mobile");
    await page.getByTitle("Editar instrumento", { exact: true }).click();
    await expect(page.getByLabel("Nome *", { exact: true })).toHaveValue(name);
    await expect(page.locator(".instrumento-cover-preview img")).toHaveJSProperty("naturalWidth", 960);
    await shot("edicao-mobile");
    await page.setViewportSize({ width: 1440, height: 1000 }); await shot("edicao-desktop");
    await page.goto(base + "/instrumentos/" + inst.id);
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByTitle("Excluir instrumento", { exact: true }).click();
    assert.equal(deletions.length, 0);
    assert.equal((await context.request.get(api + "/instrumentos/" + inst.id)).status(), 200);
    page.once("dialog", dialog => dialog.accept());
    await page.getByTitle("Excluir instrumento", { exact: true }).click();
    await expect(page).toHaveURL(base + "/instrumentos"); ids.delete(inst.id);
    assert.equal(deletions.length, 1);
    assert.equal((await context.request.get(api + "/instrumentos/" + inst.id)).status(), 404);
    const noCover = await json(await context.request.post(api + "/instrumentos", { data: { nome: "Sem capa " + Date.now(), tipo: "GUIA" } }));
    ids.add(noCover.id);
    await page.goto(base + "/instrumentos/" + noCover.id);
    await expect(page.getByAltText("Imagem do instrumento " + noCover.nome)).toHaveJSProperty("complete", true);
    assert.ok(await page.getByAltText("Imagem do instrumento " + noCover.nome).evaluate(img => img.naturalWidth > 0 && img.src.endsWith("/images/login-digital-archive.png")));
    await json(await context.request.post(api + "/instrumentos/" + noCover.id + "/editorial/enviar-revisao", {
      data: { versao: noCover.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Teste isolado de historico" }
    }));
    await page.reload();
    page.once("dialog", dialog => dialog.accept());
    await page.getByTitle("Excluir instrumento", { exact: true }).click();
    await expect(page.locator("main .error[role=alert]")).toContainText("historico");
    await expect(page).toHaveURL(base + "/instrumentos/" + noCover.id);
    imageId = (await json(await context.request.post(api + "/imagens", { data: {
      titulo: "Imagem CRUD " + Date.now(), tipo_referencia: "URL", uri: "https://example.com/imagem.jpg",
      direitos_acesso: "INTERNO", metadados_json: {}
    } }))).id;
    await page.goto(base + "/imagens/" + imageId);
    const before = deletions.length;
    page.once("dialog", dialog => dialog.dismiss());
    await page.getByTitle("Excluir imagem", { exact: true }).click();
    assert.equal(deletions.length, before);
    page.once("dialog", dialog => dialog.accept());
    await page.getByTitle("Excluir imagem", { exact: true }).click();
    await expect(page).toHaveURL(base + "/imagens"); imageId = undefined;
    for (const route of ["/usuarios","/perfis","/permissoes","/acessos","/auditoria","/exportacoes","/retencao/politicas"]) {
      await page.goto(base + route);
      await expect(page.locator("table")).toHaveAttribute("aria-busy", "false");
      await expect(page.locator(".crud-pagination")).toHaveCount(2);
      await expect(page.locator("tbody").getByRole("button", { name: /Excluir|Descartar|Executar retencao|Desativar/ })).toHaveCount(0);
      await shot(route.replaceAll("/", "-"));
    }
    const queries = [];
    await context.route("**/instrumentos/*/buscar-avancado", async route => {
      const query = route.request().postDataJSON(); queries.push(query);
      const items = Array.from({ length: Math.min(query.limit, 41 - query.offset) }, (_, i) => ({
        id: "registro-" + (query.offset + i), instrumento_id: noCover.id, titulo: "Resultado " + (query.offset + i),
        texto_geral: "Texto de consulta", status: "ATIVO", atualizado_em: "2026-10-20T12:00:00Z"
      }));
      await route.fulfill({ json: { items, total: 41, limit: query.limit, offset: query.offset, indice_defasado: false } });
    });
    await page.goto(base + "/pesquisa");
    await page.getByLabel("Texto", { exact: true }).fill("consulta aplicada");
    await page.getByRole("button", { name: "Pesquisar", exact: true }).click();
    await expect(page.locator("tbody tr")).toHaveCount(20);
    await page.getByLabel("Texto", { exact: true }).fill("rascunho nao aplicado");
    await page.getByTitle("Proxima pagina", { exact: true }).first().click();
    await expect.poll(() => queries.at(-1)?.offset).toBe(20);
    assert.equal(queries.at(-1).q, "consulta aplicada");
    await page.getByLabel("Registros por pagina", { exact: true }).first().selectOption("50");
    await expect(page.locator("tbody tr")).toHaveCount(41);
    assert.equal(queries.at(-1).offset, 0);
    assert.equal(queries.at(-1).q, "consulta aplicada");
    await shot("pesquisa-desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await shot("pesquisa-mobile");
    assert.deepEqual(errors, []);
    console.log("PASS: imagem e todos os metadados; inclusao/edicao, detalhes desktop/mobile, acoes ghost, exclusao confirmada/cancelada, bloqueio por historico e listagens administrativas.");
  } catch (err) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-crud-identidade-falha.png"), fullPage: true }).catch(() => {});
    throw err;
  } finally {
    if (imageId) await context.request.delete(api + "/imagens/" + imageId);
    for (const id of ids) {
      const response = await context.request.get(api + "/instrumentos/" + id);
      if (response.ok()) {
        const inst = await response.json();
        await context.request.post(api + "/instrumentos/" + id + "/editorial/arquivar", { data: {
          versao: inst.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Encerramento de teste isolado"
        } });
      }
    }
    await browser.close();
  }
})().catch(err => { console.error(err); process.exitCode = 1; });
