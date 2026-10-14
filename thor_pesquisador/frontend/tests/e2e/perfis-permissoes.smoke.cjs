const assert = require("node:assert/strict");
const path = require("node:path");
const os = require("node:os");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL,api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true","Use exclusivamente a stack isolada.");
(async () => {
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:900}});
  const page = await context.newPage();
  const code = "PP_" + Date.now();
  const errors = [];
  page.on("pageerror",e => errors.push(e.message));
  let created = false;
  async function json(response) {assert.ok(response.ok(),await response.text());return response.json();}
  async function search(value,entity) {
    await page.getByLabel("Busca simples",{exact:true}).fill(value);
    const response = page.waitForResponse(r => r.url().includes("/" + entity + "?") && r.url().includes("q=" + value));
    await page.getByLabel("Busca simples",{exact:true}).press("Enter");
    await json(await response);
  }
  function permission(value) {
    return page.locator(".permission-choice").filter({has:page.getByText(value,{exact:true})}).getByRole("checkbox");
  }
  async function checkPopup(popup,columns) {
    await popup.waitFor();
    assert.ok((await popup.boundingBox()).width <= 768);
    assert.equal(await popup.locator(".administracao-details").evaluate(el => getComputedStyle(el).gridTemplateColumns.split(" ").length),columns);
    assert.equal(await popup.locator("dt").first().evaluate(el => getComputedStyle(el).textTransform),"uppercase");
    assert.ok(await popup.evaluate(el => el.scrollWidth <= el.clientWidth));
  }
  try {
    await page.goto(base + "/login");
    await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    await page.goto(base + "/perfis");
    await page.getByRole("link",{name:"Novo perfil",exact:true}).click();
    await page.getByLabel(/^Codigo/).fill(code);
    await page.getByLabel(/^Nome/).fill("Perfil visual");
    await page.getByLabel("Descricao",{exact:true}).fill("Primeira linha\nSegunda linha");
    assert.ok(await page.getByRole("checkbox",{name:"Perfil de sistema",exact:true}).isDisabled());
    await permission("instrumentos_consultar").check();
    await permission("instrumentos_editar").check();
    const create = page.waitForResponse(r => r.url() === api + "/perfis" && r.request().method() === "POST");
    await page.getByRole("button",{name:"Salvar perfil",exact:true}).click();
    const initial = await json(await create);
    created = true;
    assert.deepEqual(initial.permissoes.sort(),["instrumentos_consultar","instrumentos_editar"]);
    await page.waitForURL("**/perfis");
    await search(code,"perfis");
    const row = page.getByRole("row").filter({hasText:code});
    assert.equal(await row.getByRole("button",{name:"Excluir perfil",exact:true}).count(),0);
    const listUrl = page.url();
    await row.locator(".crud-record-link").click();
    const popup = page.getByRole("dialog",{name:"Perfil",exact:true});
    await popup.getByText(code,{exact:true}).waitFor();
    assert.equal(page.url(),listUrl);
    await checkPopup(popup,2);
    await popup.locator(".administracao-permission-tag").filter({hasText:"instrumentos_consultar"}).waitFor();
    await page.screenshot({path:path.join(os.tmpdir(),"thor-perfis-popup-desktop.png")});
    await popup.getByRole("link",{name:"Editar",exact:true}).click();
    await page.waitForURL("**/perfis/" + code + "/editar");
    const heading = page.getByRole("heading",{name:"Editar perfil",exact:true});
    await heading.waitFor();
    assert.equal(await heading.evaluate(el => getComputedStyle(el).fontSize),"24px");
    assert.equal(await page.getByRole("table").count(),0);
    assert.equal(await page.locator(".crud-search-form,.crud-pagination").count(),0);
    assert.ok(!(await page.getByLabel(/^Codigo/).isEditable()));
    await page.getByLabel(/^Nome/).fill("Perfil atualizado");
    await page.getByRole("checkbox",{name:"Perfil ativo",exact:true}).uncheck();
    await permission("instrumentos_editar").uncheck();
    await permission("revisar").check();
    await page.screenshot({path:path.join(os.tmpdir(),"thor-perfis-editar-desktop.png")});
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.evaluate(() => window.scrollTo(0,0));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-perfis-editar-mobile.png")});
    const update = page.waitForResponse(r => r.url() === api + "/perfis/" + code && r.request().method() === "PUT");
    await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();
    const changed = await json(await update);
    assert.equal(changed.ativo,false);
    assert.deepEqual(changed.permissoes.sort(),["instrumentos_consultar","revisar"]);
    await page.waitForURL("**/perfis");
    await search(code,"perfis");
    await page.getByRole("row").filter({hasText:code}).getByRole("button",{name:"Visualizar",exact:true}).click();
    await popup.getByText("Perfil atualizado",{exact:true}).waitFor();
    await checkPopup(popup,1);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-perfis-popup-mobile.png")});
    await popup.getByRole("link",{name:"Editar",exact:true}).click();
    await page.getByRole("checkbox",{name:"Perfil ativo",exact:true}).check();
    const activate = page.waitForResponse(r => r.url() === api + "/perfis/" + code && r.request().method() === "PUT");
    await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();
    assert.equal((await json(await activate)).ativo,true);
    await page.waitForURL("**/perfis");
    await search(code,"perfis");
    await page.getByRole("row").filter({hasText:code}).getByRole("button",{name:"Visualizar",exact:true}).click();
    await popup.getByText(code,{exact:true}).waitFor();
    page.once("dialog",d => d.dismiss());
    await popup.getByRole("button",{name:"Excluir",exact:true}).click();
    assert.equal((await context.request.get(api + "/perfis/" + code)).status(),200);
    page.once("dialog",d => d.accept());
    const deletion = page.waitForResponse(r => r.url() === api + "/perfis/" + code && r.request().method() === "DELETE");
    await popup.getByRole("button",{name:"Excluir",exact:true}).click();
    assert.equal((await json(await deletion)).status,"excluido");
    await popup.waitFor({state:"hidden"});
    assert.equal((await context.request.get(api + "/perfis/" + code)).status(),404);
    created = false;
    await page.setViewportSize({width:1440,height:900});
    await search("ADMIN","perfis");
    const adminRow = page.getByRole("row").filter({has:page.getByRole("cell",{name:"ADMIN",exact:true})});
    await adminRow.locator(".crud-record-link").click();
    await popup.getByText("ADMIN",{exact:true}).first().waitFor();
    assert.equal(await popup.getByRole("link",{name:"Editar",exact:true}).count(),0);
    assert.equal(await popup.getByRole("button",{name:"Excluir",exact:true}).count(),0);
    await page.keyboard.press("Escape");
    await page.goto(base + "/perfis/ADMIN/editar");
    await page.getByText("Perfil protegido.",{exact:true}).waitFor();
    assert.ok(await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).isDisabled());
    await page.locator(".permission-choice input").first().waitFor();
    for(const checkbox of await page.locator(".permission-choice input").all()) {
      assert.ok(await checkbox.isChecked());
      assert.ok(await checkbox.isDisabled());
    }
    await page.goto(base + "/permissoes");
    await page.getByRole("heading",{name:"Permissoes",exact:true}).waitFor();
    assert.equal(await page.locator(".actions").getByRole("link",{name:/^(Novo|Nova|Editar|Excluir)/}).count(),0);
    assert.equal(await page.getByRole("button",{name:/^(Novo|Nova|Editar|Excluir)/}).count(),0);
    const before = await json(await context.request.get(api + "/permissoes"));
    const mutations = [];
    page.on("request",r => {if(r.url().startsWith(api + "/permissoes") && r.method() !== "GET") mutations.push(r.method());});
    await search("publicar","permissoes");
    const permissionRow = page.getByRole("row").filter({hasText:"Publicar"});
    const permissionUrl = page.url();
    await permissionRow.locator(".crud-record-link").click();
    const permissionPopup = page.getByRole("dialog",{name:"Permissao",exact:true});
    await permissionPopup.getByText("Publicar",{exact:true}).first().waitFor();
    assert.equal(page.url(),permissionUrl);
    await checkPopup(permissionPopup,2);
    assert.equal(await permissionPopup.getByRole("link").count(),0);
    assert.equal(await permissionPopup.getByRole("button").count(),1);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-permissoes-popup-desktop.png")});
    await page.setViewportSize({width:390,height:844});
    await checkPopup(permissionPopup,1);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-permissoes-popup-mobile.png")});
    await page.keyboard.press("Escape");
    await permissionRow.getByRole("button",{name:"Visualizar permissao",exact:true}).click();
    await permissionPopup.waitFor();
    await permissionPopup.getByRole("button",{name:"Fechar",exact:true}).click();
    assert.deepEqual(mutations,[]);
    for(const method of ["post","put","delete"]) {
      const response = await context.request[method](api + "/permissoes");
      assert.equal(response.status(),405);
    }
    assert.equal((await json(await context.request.get(api + "/permissoes"))).total,before.total);
    assert.deepEqual(errors,[]);
    console.log("PASS: perfil CRUD em paginas proprias, popup desktop/mobile, ativacao/desativacao, exclusao confirmada, ADMIN protegido e permissoes somente leitura na UI/API.");
  } catch(e) {
    await page.screenshot({path:path.join(os.tmpdir(),"thor-perfis-permissoes-falha.png")}).catch(() => {});
    throw e;
  } finally {
    if(created) await context.request.delete(api + "/perfis/" + code).catch(() => {});
    await browser.close();
  }
})().catch(e => {console.error(e);process.exit(1);});
