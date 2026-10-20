const assert = require("node:assert/strict"), os = require("node:os"), path = require("node:path"), fs = require("node:fs");
const { execFileSync } = require("node:child_process");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true", "Use somente a stack isolada.");
assert.ok(process.env.AXE_SCRIPT && fs.existsSync(process.env.AXE_SCRIPT), "Informe o axe-core verificado.");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const admin = await browser.newContext(), visitor = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await visitor.newPage(), errors = [];
  let iid;
  page.on("pageerror", error => errors.push(error.message));
  async function json(response) { assert.ok(response.ok(), response.status() + ": " + await response.text()); return response.json(); }
  async function publish(endpoint) {
    for (const action of ["enviar-revisao", "aprovar", "publicar"]) {
      const row = await json(await admin.request.get(api + endpoint));
      await json(await admin.request.post(api + endpoint + "/editorial/" + action, { data: {
        versao: row.versao || row.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Teste isolado de pesquisa no portal"
      } }));
    }
  }
  function python(lines) {
    return execFileSync("docker", ["compose", "-f", path.resolve(__dirname, "../../../docker-compose.test.yml"),
      "exec", "-T", "backend", "python", "-c", lines.join("\n")], { encoding: "utf8" }).trim();
  }
  async function ready() {
    await expect(page.locator("table")).toHaveAttribute("aria-busy", "false");
    await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
  }
  async function change(action) {
    const response = page.waitForResponse(r => r.url().startsWith(api + "/publico/instrumentos/" + iid + "/buscar?"));
    await action();
    const result = await response, data = await json(result);
    await ready();
    return { data, params: new URL(result.url()).searchParams };
  }
  async function submit(value, enter = false) {
    await page.getByLabel("Buscar registros publicados", { exact: true }).fill(value);
    return change(() => enter ? page.getByLabel("Buscar registros publicados", { exact: true }).press("Enter") :
      page.getByRole("button", { name: "Buscar", exact: true }).click());
  }
  async function checkLayout(label) {
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Sem overflow: " + label);
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-portal-registros-" + label + ".png") });
    await page.addScriptTag({ path: process.env.AXE_SCRIPT });
    const violations = await page.evaluate(async () => (await axe.run(document, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] }
    })).violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })));
    assert.deepEqual(violations, [], "Acessibilidade: " + label);
  }
  try {
    await json(await admin.request.post(api + "/auth/dev-login"));
    iid = (await json(await admin.request.post(api + "/instrumentos", {
      data: { nome: "Consulta publicada " + Date.now(), tipo: "CATALOGO", visibilidade: "PUBLICO" }
    }))).id;
    const prefix = "/instrumentos/" + iid;
    for (const [chave, nome, tipo, extra] of [
      ["titulo", "Titulo publicado", "TEXTO_CURTO", { filtro_avancado: true }],
      ["numero", "Numero", "NUMERO", { filtro_avancado: true }],
      ["confirmado", "Confirmado", "BOOLEANO", { filtro_avancado: true }],
      ["chegada", "Data de chegada", "DATA", { filtro_avancado: true }],
      ["porto", "Porto", "LISTA_SIMPLES", { facetavel: true }],
      ["fora_lista", "Fora da listagem", "TEXTO_CURTO", { aparece_listagem: false }],
      ["segredo", "Campo privado", "TEXTO_CURTO", { exibir_publico: false, filtro_avancado: true }]
    ]) await json(await admin.request.post(api + prefix + "/campos", {
      data: { chave, nome, tipo, exibir_publico: true, ...extra }
    }));
    await publish(prefix);
    for (let n = 0; n < 21; n++) {
      const record = await json(await admin.request.post(api + prefix + "/registros", { data: { dados: {
        titulo: "Documento publicado " + String(n).padStart(2, "0"), numero: n, confirmado: n !== 0,
        chegada: "1900-01-02", porto: n === 0 ? "Santos" : "Rio",
        fora_lista: "PUBLICO_FORA_LISTA", segredo: "PRIVADO_NAO_DIVULGAR"
      } } }));
      await publish(prefix + "/registros/" + record.id);
    }
    await json(await admin.request.post(api + prefix + "/registros", { data: { dados: { titulo: "RASCUNHO_NAO_DIVULGAR" } } }));
    python(["import uuid", "from app.core.config import settings", "from app.db.session import SessionLocal",
      "from app.services.publicacao_service import processar_pendente", "assert settings.mongodb_database.endswith('_test')",
      "with SessionLocal() as db:", " while processar_pendente(db,instrumento_id=uuid.UUID('" + iid + "')): pass"]);
    const publicPath = "/publico/instrumentos/" + iid;
    assert.equal((await visitor.request.get(api + publicPath + "/buscar")).status(), 401);
    await page.goto(base + "/consulta/" + iid);
    await page.waitForURL(url => url.pathname === "/login" && url.searchParams.get("next") === "/consulta/" + iid);
    const seed = JSON.parse(python(["import json", "from app.core.config import settings", "from app.db.session import SessionLocal",
      "from app.services.auth_service import usuario_from_claims,create_session", "from app.tests.functional.test_usuarios import cpf_teste",
      "assert settings.mongodb_database.endswith('_test')", "with SessionLocal() as db:",
      " print(json.dumps(dict(token=create_session(db,usuario_from_claims(db,{'sub':cpf_teste()})),cookie=settings.session_cookie_name)))"]));
    await visitor.addCookies([{ name: seed.cookie, value: seed.token, url: base }]);
    let facets = 0;
    page.on("request", request => { if (request.url() === api + publicPath + "/facetas") facets++; });
    await page.goto(base + "/consulta/" + iid); await ready();
    await expect(page.getByRole("columnheader", { name: "Titulo publicado", exact: true })).toBeVisible();
    assert.equal(await page.locator(".crud-pagination").count(), 2);
    assert.equal(await page.locator("tbody tr").count(), 20);
    assert.equal(facets, 0, "Facetas sob demanda");
    for (const hidden of ["Campo privado", "Fora da listagem", "PRIVADO_NAO_DIVULGAR", "RASCUNHO_NAO_DIVULGAR", "PUBLICO_FORA_LISTA"])
      assert.ok(!(await page.locator("body").innerText()).includes(hidden), hidden);
    for (const action of ["Novo registro", "Editar registro", "Excluir registro"])
      assert.equal(await page.getByRole(action === "Novo registro" ? "link" : "button", { name: action, exact: true }).count(), 0);
    await expect(page.getByRole("link", { name: "Visualizar registro", exact: true }).first()).toHaveAttribute("title", "Visualizar registro");
    const last = await change(() => page.getByTitle("Ultima pagina", { exact: true }).first().click());
    assert.equal(last.params.get("offset"), "20");
    assert.equal(last.data.total, 21);
    assert.equal(await page.locator("tbody tr").count(), 1);
    const resized = await change(() => page.getByRole("combobox", { name: "Registros por pagina" }).last().selectOption("50"));
    assert.equal(resized.params.get("offset"), "0");
    assert.equal(await page.locator("tbody tr").count(), 21);
    const search = await submit("  Documento publicado  ", true);
    assert.equal(search.params.get("q"), "Documento publicado");
    await page.getByLabel("Buscar registros publicados", { exact: true }).fill("Rascunho");
    const paged = await change(() => page.getByRole("combobox", { name: "Registros por pagina" }).first().selectOption("20"));
    assert.equal(paged.params.get("q"), "Documento publicado");
    const facetResponse = page.waitForResponse(r => r.url() === api + publicPath + "/facetas");
    await page.getByRole("button", { name: "Filtros avancados", exact: true }).click();
    await json(await facetResponse);
    assert.equal(await page.getByLabel("Campo privado", { exact: true }).count(), 0);
    await page.getByLabel("Numero", { exact: true }).fill("0");
    await page.getByLabel("Confirmado", { exact: true }).selectOption("false");
    await page.getByLabel("Data de chegada", { exact: true }).fill("1900-01-02");
    await page.getByLabel("Porto", { exact: true }).selectOption("Santos");
    const filtered = await submit("");
    assert.deepEqual(JSON.parse(filtered.params.get("filtros")), { numero: 0, confirmado: false, chegada: "1900-01-02", porto: "Santos" });
    assert.equal(filtered.data.total, 1);
    await expect(page.locator("tbody")).toContainText("Documento publicado 00");
    await expect(page.locator("tbody")).toContainText("Nao");
    await checkLayout("desktop");
    await page.setViewportSize({ width: 390, height: 844 }); await checkLayout("mobile");
    await page.getByRole("link", { name: "Visualizar registro", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Documento publicado 00", exact: true })).toBeVisible();
    assert.ok(!(await page.locator("body").innerText()).includes("PRIVADO_NAO_DIVULGAR"));
    await page.getByRole("link", { name: "Consulta", exact: true }).click(); await ready();
    await submit("semresultadoxyz");
    await expect(page.getByText("Nenhum registro publicado.", { exact: true })).toBeVisible();
    const cleared = await change(() => page.getByRole("button", { name: "Limpar filtros", exact: true }).click());
    assert.equal(cleared.data.total, 21);
    assert.equal(cleared.params.get("offset"), "0");
    assert.deepEqual(JSON.parse(cleared.params.get("filtros")), {});
    await visitor.clearCookies();
    await page.reload(); await page.waitForURL("**/login?next=*");
    assert.deepEqual(errors, []);
    console.log("PASS: registros publicados, colunas dinamicas, pagina/tamanho, busca/Enter/limpar, filtros zero/falso/data/facetas, visitante, sessao e axe desktop/mobile.");
  } catch (error) {
    await page.screenshot({ path: path.join(os.tmpdir(), "thor-portal-registros-falha.png") }).catch(() => {});
    throw error;
  } finally {
    if (iid) {
      const endpoint = "/instrumentos/" + iid;
      const current = await admin.request.get(api + endpoint);
      if (current.ok()) {
        const row = await current.json();
        await admin.request.post(api + endpoint + "/editorial/arquivar", { data: {
          versao: row.versao_editorial, operacao_id: crypto.randomUUID(), justificativa: "Encerramento do teste isolado"
        } });
      }
    }
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
