const assert=require("node:assert/strict");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED==="true","Use apenas a stack isolada.");
(async()=>{
  const browser=await chromium.launch({headless:true}),context=await browser.newContext();
  const page=await context.newPage(),errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  async function login(next="/dashboard") {
    await page.goto(base+"/login?next="+encodeURIComponent(next));
    await page.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
    await page.waitForURL(base+next);
  }
  async function redirected(path) {
    await page.waitForURL(url=>url.pathname==="/login" && url.searchParams.get("next")===path);
    assert.equal(await page.locator(".app-header").count(),0);
  }
  try {
    for(const route of ["/dashboard","/usuarios","/perfis","/permissoes","/acessos/novo","/imagens",
        "/consulta/00000000-0000-0000-0000-000000000001/registro",
        "/auditoria","/exportacoes","/exportacoes/nova","/relatorios","/retencao/politicas",
        "/retencao/politicas/nova","/retencao/execucoes",
        "/auditoria/geral/00000000-0000-0000-0000-000000000001",
        "/exportacoes/00000000-0000-0000-0000-000000000001",
        "/retencao/politicas/00000000-0000-0000-0000-000000000001",
        "/retencao/execucoes/00000000-0000-0000-0000-000000000001",
        "/instrumentos/00000000-0000-0000-0000-000000000001/registros/registro/editar"]) {
      await page.goto(base+route);await redirected(route);
    }
    await page.goto(base+"/usuarios?nome=Teste");
    await redirected("/usuarios?nome=Teste");
    await page.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
    await page.waitForURL(base+"/usuarios?nome=Teste");
    await page.getByRole("heading",{name:"Gestao de Usuarios",exact:true}).waitFor();
    await context.clearCookies();
    await page.getByLabel("Busca simples",{exact:true}).fill("sessao");
    await page.getByRole("button",{name:"Pesquisar",exact:true}).click();
    await redirected("/usuarios?nome=Teste");
    await login("/imagens");
    await page.getByRole("heading",{name:"Imagens",exact:true}).waitFor();
    await context.clearCookies();
    await page.getByLabel("Busca simples",{exact:true}).fill("sessao");
    await page.getByRole("button",{name:"Buscar",exact:true}).click();
    await redirected("/imagens");
    await login("/dashboard");
    await page.getByRole("heading",{name:/Dashboard/}).waitFor();
    await context.clearCookies();
    await page.evaluate(()=>window.dispatchEvent(new Event("focus")));
    await redirected("/dashboard");
    await login("/perfis");
    await page.route("**/api/v1/perfis?**",route=>route.fulfill({status:403,contentType:"application/json",body:JSON.stringify({detail:"Sem permissao de teste."})}));
    await page.reload();
    await page.getByRole("alert").filter({hasText:"Sem permissao de teste."}).waitFor();
    assert.equal(new URL(page.url()).pathname,"/perfis");
    await page.unroute("**/api/v1/perfis?**");
    await page.goto(base+"/login?next="+encodeURIComponent("https://outside.example/"));
    await page.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
    await page.waitForURL(base+"/dashboard");
    assert.deepEqual(errors,[]);
    console.log("PASS: todas as rotas sem sessao, retorno com query, expiracao em API/imagens/foco, 403 sem logout e destino externo bloqueado.");
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
