const assert=require("node:assert/strict");
const path=require("node:path");
const os=require("node:os");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base&&api&&process.env.THOR_E2E_ISOLATED==="true","Use apenas a stack isolada.");
(async()=>{
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:900}});
 const page=await context.newPage(), ids=[],mark="Lista "+Date.now();
 const errors=[];page.on("pageerror",e=>errors.push(e.message));
 let image;
 async function json(r){assert.ok(r.ok(),await r.text());return r.json();}
 async function blueLink(){
  const link=page.locator("tbody tr td:first-child .crud-record-link").first();
  await link.waitFor();
  await page.waitForFunction(()=>{
    const e=document.querySelector("tbody tr td:first-child .crud-record-link");
    const color=e?getComputedStyle(e).color:"";
    const channels=color.match(/\d+/g)?.map(Number);
    return channels&&channels[2]>channels[0]&&channels[2]>channels[1];
  });
  const color=await link.evaluate(e=>getComputedStyle(e).color);
  const channels=color.match(/\d+/g).map(Number);
  assert.ok(channels[2]>channels[0]&&channels[2]>channels[1],color);
  return link;
 }
 try{
  await page.goto(base+"/login");await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();await page.waitForURL("**/dashboard");
  await page.locator(".admin-navigation summary").waitFor();
  const a=await page.locator(".sidebar .admin-navigation summary svg").first().boundingBox();
  const b=await page.locator('.sidebar a.nav-link[href="/dashboard"] svg').boundingBox();
  assert.equal(a.x,b.x,"Cabecalhos do menu devem alinhar os icones");
  for(let n=0;n<161;n++) ids.push((await json(await context.request.post(api+"/instrumentos",{data:{nome:mark+" "+n,tipo:"CATALOGO"}}))).id);
  await page.goto(base+"/instrumentos");
  await page.getByLabel("Busca simples",{exact:true}).fill(mark);
  const query=page.waitForResponse(r=>r.url().includes("/instrumentos?")&&r.url().includes("q=Lista"));
  await page.getByLabel("Busca simples",{exact:true}).press("Enter");await json(await query);
  const bar=page.locator(".crud-pagination").first();
  await bar.getByText(/20 registros de 161/).waitFor();
  assert.equal(await bar.getByRole("button").count(),7);
  assert.equal((await bar.getByRole("button",{name:"Primeira",exact:true}).boundingBox()).height,36);
  assert.equal((await bar.getByLabel("Registros por pagina").boundingBox()).height,36);
  assert.equal(await bar.locator(".pagination-ellipsis").count(),1);
  assert.ok(await bar.getByRole("button",{name:"1",exact:true}).isDisabled());
  await bar.getByRole("button",{name:"2",exact:true}).click();
  await bar.getByText(/pagina 2|p\u00e1gina 2/).waitFor();
  assert.equal(await bar.getByRole("button",{name:"2",exact:true}).getAttribute("aria-current"),"page");
  for(let n=3;n<=5;n++){
    await bar.getByRole("button",{name:"Pr\u00f3xima",exact:true}).click();
    await bar.getByText(new RegExp("p\u00e1gina "+n+" de 9")).waitFor();
  }
  assert.equal(await bar.locator(".pagination-ellipsis").count(),2);
  await page.screenshot({path:path.join(os.tmpdir(),"thor-paginacao-unidades.png")});
  await bar.getByRole("button",{name:"9",exact:true}).click();
  await bar.getByText(/1 registros de 161/).waitFor();
  assert.ok(await bar.getByRole("button",{name:"Pr\u00f3xima",exact:true}).isDisabled());
  await bar.getByLabel("Registros por pagina").selectOption("50");
  await bar.getByText(/50 registros de 161/).waitFor();
  await page.waitForFunction(()=>!document.querySelector(".crud-pagination select")?.disabled);
  const first=await blueLink();await first.click();await page.getByRole("heading",{name:/Lista/}).waitFor();
  for(const route of ["/usuarios","/perfis","/permissoes"]){await page.goto(base+route);await blueLink();}
  image=await json(await context.request.post(api+"/imagens",{data:{titulo:mark,uri:"https://example.org/image.png",direitos_acesso:"PUBLICO"}}));
  await page.goto(base+"/imagens");await blueLink();
  const prefix="/instrumentos/"+ids[0];
  await json(await context.request.post(api+prefix+"/campos",{data:{nome:"Titulo",chave:"titulo",tipo:"TEXTO_CURTO",aparece_listagem:true}}));
  const record=await json(await context.request.post(api+prefix+"/registros",{data:{dados:{titulo:mark}}}));
  await page.goto(base+prefix+"/registros");await (await blueLink()).click();await page.waitForURL("**/"+record.id);
  await page.goto(base+prefix+"/campos");await (await blueLink()).click();await page.getByRole("dialog",{name:"Visualizar campo"}).waitFor();
  await page.getByRole("button",{name:"Fechar",exact:true}).click();
  await page.goto(base+"/perfis");
  await page.screenshot({path:path.join(os.tmpdir(),"thor-listagens-desktop.png")});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(os.tmpdir(),"thor-listagens-mobile.png")});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual(errors,[]);
  console.log("PASS: alinhamento, pesquisa, paginacao no servidor, tamanho de pagina, links azuis, detalhes e desktop/mobile.");
 }finally{
  for(const id of ids)await context.request.delete(api+"/instrumentos/"+id);
  if(image)await context.request.delete(api+"/imagens/"+image.id);
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
