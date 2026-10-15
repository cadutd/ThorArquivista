const assert = require("node:assert/strict");
const path = require("node:path");
const os = require("node:os");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true","Use exclusivamente a stack isolada.");
(async () => {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage(),code="CV_" + Date.now();
  const errors=[];page.on("pageerror",e => errors.push(e.message));
  let profile,instrument,scoped,globalGrant;
  async function json(response) {assert.ok(response.ok(),await response.text());return response.json();}
  async function search() {
    await page.getByLabel("Busca simples",{exact:true}).fill(code);
    await page.getByLabel("Busca simples",{exact:true}).press("Enter");
    await page.getByRole("row").filter({hasText:profile.nome}).first().waitFor();
  }
  try {
    await page.goto(base + "/login");
    await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    const user=await json(await context.request.get(api + "/auth/me"));
    profile=await json(await context.request.post(api + "/perfis",{data:{codigo:code,
      nome:"Perfil de concessao com nome longo " + code,permissoes:["instrumentos_consultar"]}}));
    instrument=await json(await context.request.post(api + "/instrumentos",{data:{
      nome:"Instrumento fotografico com descricao extensa " + code,tipo:"CATALOGO"}}));
    scoped=(await json(await context.request.post(api + "/acessos",{data:{
      usuario_id:user.id,papel:code,instrumento_id:instrument.id}}))).id;
    await page.goto(base + "/acessos");
    await page.getByRole("heading",{name:"Concessoes de acesso",exact:true}).waitFor();
    assert.equal(await page.locator(".crud-pagination").count(),2);
    await search();
    const row=page.getByRole("row").filter({hasText:instrument.nome});
    assert.ok((await row.innerText()).includes(profile.nome));
    assert.ok(!(await row.innerText()).includes(instrument.id));
    const listUrl=page.url();
    await row.locator(".crud-record-link").click();
    const popup=page.getByRole("dialog",{name:"Concessao de acesso",exact:true});
    await popup.getByText(instrument.nome,{exact:true}).waitFor();
    assert.equal(page.url(),listUrl);
    assert.ok((await popup.boundingBox()).width <= 768);
    assert.equal(await popup.locator(".administracao-details").evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(" ").length),2);
    assert.equal(await popup.locator("dt").first().evaluate(el=>getComputedStyle(el).textTransform),"uppercase");
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-popup-desktop.png")});
    await popup.getByRole("link",{name:"Editar",exact:true}).click();
    await page.waitForURL("**/acessos/" + scoped + "/editar");
    await page.getByRole("heading",{name:"Editar acesso",exact:true}).waitFor();
    await page.getByRole("region",{name:"Acessos existentes",exact:true}).waitFor();
    await page.getByRole("radiogroup",{name:"Escopo da concessao",exact:true}).waitFor();
    assert.equal(await page.locator(".administracao-form-grid").first().evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(" ").length),2);
    assert.equal(await page.getByRole("heading",{name:"Editar acesso",exact:true}).evaluate(el=>getComputedStyle(el).fontSize),"24px");
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-editar-desktop.png")});
    await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();
    await page.waitForURL("**/acessos");
    await page.setViewportSize({width:390,height:844});
    await search();
    await page.getByRole("button",{name:"Filtros",exact:true}).click();
    await page.getByLabel("Escopo",{exact:true}).selectOption("INSTRUMENTO");
    const filtered=page.waitForResponse(r=>r.url().includes("/acessos?") && r.url().includes("escopo=INSTRUMENTO"));
    await page.getByRole("button",{name:"Pesquisar",exact:true}).click();
    assert.equal((await json(await filtered)).total,1);
    await page.waitForFunction(()=>document.querySelector("tbody")?.querySelectorAll("tr").length===1);
    await page.getByRole("row").filter({hasText:instrument.nome}).waitFor();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-lista-mobile.png")});
    await page.getByRole("row").filter({hasText:instrument.nome}).getByRole("button",{name:"Visualizar",exact:true}).click();
    await popup.getByText(instrument.nome,{exact:true}).waitFor();
    assert.equal(await popup.locator(".administracao-details").evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(" ").length),1);
    assert.ok(await popup.evaluate(el=>el.scrollWidth <= el.clientWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-popup-mobile.png")});
    page.once("dialog",d=>d.accept());
    await popup.getByRole("button",{name:"Revogar acesso",exact:true}).click();
    await popup.waitFor({state:"hidden"});scoped=undefined;
    assert.deepEqual(errors,[]);
    console.log("PASS: busca com nomes, popup sem navegacao, edicao/criacao isoladas, Enter nos lookups, filtros, revogacao e desktop/mobile.");
  } finally {
    if(scoped) await context.request.delete(api + "/acessos/" + scoped);
    if(globalGrant) await context.request.delete(api + "/acessos/" + globalGrant);
    if(instrument) await context.request.delete(api + "/instrumentos/" + instrument.id);
    if(profile) await context.request.delete(api + "/perfis/" + profile.codigo);
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1);});
