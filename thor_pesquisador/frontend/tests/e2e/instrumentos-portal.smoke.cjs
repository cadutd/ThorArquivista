const assert=require("node:assert/strict"),path=require("node:path"),os=require("node:os");
const {chromium,request}=require(process.env.PLAYWRIGHT_MODULE||"@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base&&api&&process.env.THOR_E2E_ISOLATED==="true","Use somente a stack isolada.");
(async()=>{
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1440,height:1000}});
 const anonymous=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),portal=await anonymous.newPage();
 const name="Capa e filtros "+Date.now(),description="Descricao para filtro exclusivo "+Date.now(),errors=[];
 let iid;
 for(const p of [page,portal])p.on("pageerror",e=>errors.push(e.message));
 async function json(r){assert.ok(r.ok(),r.status()+": "+await r.text());return r.json();}
 async function publish(){
  for(const action of ["enviar-revisao","aprovar","publicar"]){
   const current=await json(await context.request.get(api+"/instrumentos/"+iid));
   await json(await context.request.post(api+"/instrumentos/"+iid+"/editorial/"+action,{data:{
    operacao_id:crypto.randomUUID(),versao:current.versao_editorial,justificativa:"Teste isolado de capa institucional"}}));
  }
 }
 async function shot(p,label){
  assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),"Sem overflow: "+label);
  await p.screenshot({path:path.join(os.tmpdir(),"thor-capas-"+label+".png")});
 }
 try{
  await page.goto(base+"/login");await page.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
  await page.waitForURL("**/dashboard");await page.goto(base+"/instrumentos/novo");
  await page.getByLabel("Nome *",{exact:true}).fill(name);
  await page.getByRole("combobox",{name:/^Tipo/}).selectOption("CATALOGO");
  await page.getByRole("combobox",{name:/^Visibilidade/}).selectOption("PUBLICO");
  await page.getByLabel("Descricao",{exact:true}).fill(description);
  const upload=page.waitForResponse(r=>r.url()===api+"/instrumentos/imagens-card"&&r.request().method()==="POST");
  await page.getByLabel("Imagem do card",{exact:true}).setInputFiles(path.resolve(__dirname,"../../public/images/login_pesquisador.png"));
  const capa=await json(await upload);assert.deepEqual([capa.largura,capa.altura],[960,540]);
  await page.waitForFunction(()=>document.querySelector(".instrumento-cover-preview img")?.naturalWidth===960);
  await shot(page,"form-desktop");await page.setViewportSize({width:390,height:844});await shot(page,"form-mobile");
  const created=page.waitForResponse(r=>r.url()===api+"/instrumentos"&&r.request().method()==="POST");
  await page.getByRole("button",{name:"Salvar instrumento",exact:true}).click();
  const instrument=await json(await created);iid=instrument.id;assert.equal(instrument.imagem_card_id,capa.id);
  await page.waitForURL(base+"/instrumentos");await page.getByRole("button",{name:"Filtros avancados",exact:true}).click();
  await page.getByLabel("Nome",{exact:true}).fill(name);
  await page.getByRole("combobox",{name:/^Tipo/}).selectOption("CATALOGO");
  await page.getByRole("combobox",{name:/^Status/}).selectOption("RASCUNHO");
  await page.getByRole("combobox",{name:/^Visibilidade/}).selectOption("PUBLICO");
  await page.getByLabel("Descricao",{exact:true}).fill(description);
  await page.getByLabel("Descricao",{exact:true}).press("Enter");
  await page.getByText("1 instrumentos encontrados",{exact:true}).waitFor();
  await page.getByRole("link",{name,exact:true}).waitFor();await shot(page,"interno-mobile");
  await publish();
  const url=api+"/publico/instrumentos/"+iid+"/imagem-card/"+capa.id;
  assert.equal((await anonymous.request.get(url)).status(),200);
  for(let i=0;i<10;i++){
   const visitor=await request.newContext();
   try{await json(await visitor.post(api+"/auth/dev-login"));assert.equal((await visitor.post(api+"/publico/instrumentos/"+iid+"/acessos")).status(),204);
    await visitor.post(api+"/auth/logout");}finally{await visitor.dispose();}
  }
  await portal.goto(base+"/");
  assert.equal(await portal.locator('header a[href="/consulta"]').count(),0);
  const card=portal.locator(".portal-card").filter({hasText:name});
  await card.waitFor();await card.locator("img").waitFor();
  await portal.waitForFunction(url=>[...document.querySelectorAll(".portal-card img")].some(img=>img.src===url&&img.naturalWidth===960),url);
  await shot(portal,"landing-desktop");await portal.setViewportSize({width:390,height:844});await shot(portal,"landing-mobile");
  await portal.goto(base+"/consulta");assert.equal(await portal.locator(".portal-card").count(),0);
  await portal.getByRole("button",{name:"Filtros avancados",exact:true}).click();
  await portal.getByLabel("Nome",{exact:true}).fill(name);
  await portal.getByRole("combobox",{name:/^Tipo/}).selectOption("CATALOGO");
  await portal.getByLabel("Descricao",{exact:true}).fill(description);
  await portal.getByRole("button",{name:"Buscar",exact:true}).click();
  await portal.getByText("1 instrumentos encontrados",{exact:true}).waitFor();
  await portal.getByRole("link",{name,exact:true}).waitFor();await shot(portal,"catalogo-mobile");
  await portal.setViewportSize({width:1440,height:1000});await shot(portal,"catalogo-desktop");
  await page.goto(base+"/instrumentos/"+iid+"/editar");
  await page.getByRole("button",{name:"Remover imagem do card",exact:true}).waitFor();
  page.once("dialog",d=>d.accept());await page.getByRole("button",{name:"Remover imagem do card",exact:true}).click();
  await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();await page.waitForURL(base+"/instrumentos");
  assert.equal((await anonymous.request.get(url)).status(),404);
  await publish();await portal.goto(base+"/");
  await card.waitFor();
  await portal.waitForFunction(name=>[...document.querySelectorAll(".portal-card")].some(card=>card.textContent.includes(name)&&
   card.querySelector("img")?.src.endsWith("/images/login-digital-archive.png")&&card.querySelector("img")?.naturalWidth>0),name);
  assert.deepEqual(errors,[]);
  console.log("PASS: filtros internos/publicos, tabela, cabecalho, upload/previsualizacao, card 960x540, remocao/default e desktop/mobile.");
 }finally{
  if(iid){
   const r=await context.request.get(api+"/instrumentos/"+iid);
   if(r.ok()){const value=await r.json();await context.request.post(api+"/instrumentos/"+iid+"/editorial/arquivar",{data:{
    operacao_id:crypto.randomUUID(),versao:value.versao_editorial,justificativa:"Encerramento da fixture de capa"}});}
  }
  await context.request.post(api+"/auth/logout");await browser.close();
 }
})().catch(e=>{console.error(e);process.exit(1);});
