const assert=require("node:assert/strict");
const os=require("node:os"),path=require("node:path");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED==="true","Use exclusivamente a stack isolada.");
(async()=>{
  const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage(),errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  try {
    await page.goto(base+"/login");await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    await page.goto(base+"/usuarios/novo");
    await page.locator(".usuario-editor-surface").waitFor();
    const reference=await page.locator(".usuario-editor-surface").evaluate(el=>({
      background:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderRadius,
      title:getComputedStyle(el.querySelector("h2")).fontSize
    }));
    await page.goto(base+"/acessos/novo");
    const surface=page.locator(".administracao-editor-surface");await surface.waitFor();
    assert.deepEqual(await surface.evaluate(el=>({
      background:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderRadius,
      title:getComputedStyle(el.querySelector("h2")).fontSize
    })),reference);
    const users=page.getByRole("group",{name:"Pesquisa de usuarios",exact:true});
    await users.getByLabel("Nome de usuario",{exact:true}).fill("massa_acesso_");
    const found=page.waitForResponse(r=>r.url().includes("/usuarios?") && r.url().includes("username=massa_acesso_"));
    await users.getByRole("button",{name:"Buscar usuarios",exact:true}).click();
    assert.equal((await (await found).json()).total,54);
    await users.getByRole("radio").first().waitFor();
    const selectedName=await users.getByRole("radio").first().getAttribute("aria-label");
    await users.getByRole("radio").first().check();
    const current=page.getByRole("region",{name:"Acessos existentes",exact:true});
    await current.waitFor();
    assert.equal(await current.getByRole("heading").count(),1);
    await users.locator(".crud-pagination").first().getByTitle("Proxima pagina",{exact:true}).click();
    await users.getByRole("radio").first().waitFor();
    assert.ok((await page.getByLabel("Usuario selecionado",{exact:true}).innerText()).includes(selectedName.replace("Selecionar ","")));
    await users.locator(".crud-pagination").first().getByTitle("Primeira pagina",{exact:true}).click();
    await users.getByRole("radio",{name:selectedName,exact:true}).waitFor();
    assert.ok(await users.getByRole("radio",{name:selectedName,exact:true}).isChecked());
    const profiles=page.getByRole("group",{name:"Pesquisa de perfis",exact:true});
    await profiles.getByLabel("Perfil",{exact:true}).fill("MASSA_ACESSO_");
    const matched=page.waitForResponse(r=>r.url().includes("/perfis?") && r.url().includes("q=MASSA_ACESSO_"));
    await profiles.getByRole("button",{name:"Buscar perfis",exact:true}).click();
    assert.equal((await (await matched).json()).total,22);
    const first=profiles.getByRole("row").filter({hasText:"MASSA_ACESSO_001"}).getByRole("checkbox");await first.waitFor();
    const firstName=await first.getAttribute("aria-label");await first.check();
    await profiles.locator(".crud-pagination").first().getByTitle("Proxima pagina",{exact:true}).click();
    await profiles.getByRole("row").filter({hasText:"MASSA_ACESSO_022"}).getByRole("checkbox").check();
    await profiles.locator(".crud-pagination").first().getByTitle("Primeira pagina",{exact:true}).click();
    await profiles.getByRole("checkbox",{name:firstName,exact:true}).waitFor();
    assert.ok(await profiles.getByRole("checkbox",{name:firstName,exact:true}).isChecked());
    assert.ok((await page.getByLabel("Perfis selecionados",{exact:true}).innerText()).includes(": 2"));
    assert.ok(await page.getByRole("group",{name:"Pesquisa de instrumentos",exact:true}).getByLabel("Nome",{exact:true}).isDisabled());
    await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessao-identidade-desktop.png")});
    await profiles.scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessao-perfis-desktop.png")});
    await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert.equal(await users.locator("form").evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(" ").length),1);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessao-identidade-mobile.png")});
    await page.getByRole("region",{name:"Resumo da concessao",exact:true}).scrollIntoViewIfNeeded();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessao-resumo-mobile.png")});
    assert.deepEqual(errors,[]);
    console.log("PASS: identidade de Usuarios/Perfis, 54 usuarios ativos e 22 perfis ativos paginados, selecao persistente entre paginas, escopo e desktop/mobile.");
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
