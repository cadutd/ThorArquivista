const assert=require("node:assert/strict"),os=require("node:os"),path=require("node:path"),fs=require("node:fs");
const {execFileSync}=require("node:child_process");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"@playwright/test");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base&&api&&process.env.THOR_E2E_ISOLATED==="true","Use somente a stack isolada.");
assert.ok(process.env.AXE_SCRIPT&&fs.existsSync(process.env.AXE_SCRIPT),"Informe o axe-core verificado em AXE_SCRIPT.");
(async()=>{
  const browser=await chromium.launch({headless:true}),admin=await browser.newContext({viewport:{width:1440,height:900}}),
        anonymous=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await anonymous.newPage(),adminPage=await admin.newPage(),errors=[],prefix="Portal E2E "+Date.now();
  let original;
  page.on("pageerror",e=>errors.push(e.message));adminPage.on("pageerror",e=>errors.push(e.message));
  async function json(response){assert.ok(response.ok(),await response.text());return response.json();}
  async function publish(endpoint){
    for(const action of ["enviar-revisao","aprovar","publicar"]){
      const current=await json(await admin.request.get(api+endpoint));
      await json(await admin.request.post(api+endpoint+"/editorial/"+action,{data:{
        operacao_id:crypto.randomUUID(),versao:current.versao||current.versao_editorial,justificativa:"Teste isolado fase 6"}}));
    }
  }
  async function a11y(target,name){
    await target.waitForFunction(()=>document.title.trim().length>0);
    await target.addScriptTag({path:process.env.AXE_SCRIPT});
    const result=await target.evaluate(async()=>await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}}));
    assert.deepEqual(result.violations.map(v=>({id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target)})),[],name);
  }
  async function screenshot(target,name){
    assert.ok(await target.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),name+" sem overflow");
    await target.screenshot({path:path.join(os.tmpdir(),"thor-fase6-"+name+".png"),fullPage:false});
  }
  try {
    await json(await admin.request.post(api+"/auth/dev-login"));
    original=await json(await admin.request.get(api+"/publico/configuracao/administracao"));
    let iid,rid;
    for(let n=0;n<21;n++){
      const instrument=await json(await admin.request.post(api+"/instrumentos",{data:{nome:prefix+" - "+String(n).padStart(2,"0"),tipo:"CATALOGO",visibilidade:"PUBLICO",descricao:"Colecao de teste de consulta institucional."}}));
      if(n===0){
        iid=instrument.id;
        for(const [key,show]of [["titulo",true],["segredo",false]])await json(await admin.request.post(api+"/instrumentos/"+iid+"/campos",{data:{nome:key,chave:key,tipo:"TEXTO_CURTO",exibir_publico:show,facetavel:show}}));
        rid=(await json(await admin.request.post(api+"/instrumentos/"+iid+"/registros",{data:{dados:{titulo:"Documento consultivo",segredo:"NAO_DIVULGAR_FASE6"}}}))).id;
      }
      await publish("/instrumentos/"+instrument.id);
    }
    await publish("/instrumentos/"+iid+"/registros/"+rid);
    const processCode=["import uuid","from app.core.config import settings","from app.db.session import SessionLocal",
      "from app.services.publicacao_service import processar_pendente","assert settings.mongodb_database.endswith('_test')",
      "with SessionLocal() as db:"," while processar_pendente(db,instrumento_id=uuid.UUID('"+iid+"')): pass"].join("\n");
    execFileSync("docker",["compose","-f",path.resolve(__dirname,"../../../docker-compose.test.yml"),"exec","-T","backend","python","-c",processCode],{encoding:"utf8"});
    await page.goto(base+"/");
    await page.locator(".portal-card").first().waitFor();
    assert.equal(await page.locator(".sidebar,.app-header").count(),0);
    assert.equal(await page.getByRole("link",{name:"Area interna",exact:true}).count(),0);
    assert.equal((await anonymous.request.get(api+"/publico/instrumentos/"+iid+"/registros/"+rid)).status(),401);
    await screenshot(page,"landing-desktop");await a11y(page,"Landing desktop");
    await page.setViewportSize({width:390,height:844});await screenshot(page,"landing-mobile");await a11y(page,"Landing mobile");
    await page.setViewportSize({width:1440,height:900});
    await page.getByLabel("Pesquisar instrumentos",{exact:true}).fill(prefix);
    await page.getByRole("button",{name:"Pesquisar",exact:true}).click();
    await page.waitForURL("**/consulta?q=*");
    await page.getByText("21 instrumentos encontrados",{exact:true}).waitFor();
    assert.equal(await page.locator(".table tbody tr").count(),20);
    await page.locator('button[title="Proxima pagina"]').first().click();
    await page.waitForFunction(()=>document.querySelectorAll(".table tbody tr").length===1);
    await page.getByLabel("Registros por pagina",{exact:true}).first().selectOption("50");
    await page.waitForFunction(()=>document.querySelectorAll(".table tbody tr").length===21);
    await screenshot(page,"catalogo-desktop");await a11y(page,"Catalogo");
    await page.getByRole("link",{name:prefix+" - 00",exact:true}).click();
    await page.waitForURL(url=>url.pathname==="/login"&&url.searchParams.get("next")==="/consulta/"+iid);
    const seedCode=["import json","from app.core.config import settings","from app.db.session import SessionLocal",
      "from app.services.auth_service import usuario_from_claims,create_session","from app.tests.functional.test_usuarios import cpf_teste",
      "assert settings.database_url.rsplit('/',1)[-1].endswith('_test')","with SessionLocal() as db:",
      " print(json.dumps(dict(token=create_session(db,usuario_from_claims(db,{'sub':cpf_teste()})),cookie=settings.session_cookie_name)))"].join("\n");
    const seed=JSON.parse(execFileSync("docker",["compose","-f",path.resolve(__dirname,"../../../docker-compose.test.yml"),"exec","-T","backend","python","-c",seedCode],{encoding:"utf8"}).trim());
    await anonymous.addCookies([{name:seed.cookie,value:seed.token,url:base}]);
    await page.goto(base+"/consulta/"+iid);
    await page.getByRole("link",{name:"Documento consultivo",exact:true}).waitFor();
    assert.equal(await page.getByRole("link",{name:"Area interna",exact:true}).count(),0);
    assert.ok(!(await page.locator("body").innerText()).includes("NAO_DIVULGAR"));
    assert.equal((await anonymous.request.get(api+"/usuarios")).status(),403);
    await page.getByRole("link",{name:"Documento consultivo",exact:true}).click();
    await page.getByRole("heading",{name:"Documento consultivo",exact:true}).waitFor();
    await a11y(page,"Registro publicado");
    await page.setViewportSize({width:390,height:844});await screenshot(page,"registro-mobile");
    await page.goto(base+"/dashboard");await page.waitForURL("**/consulta");
    await adminPage.goto(base+"/portal/configuracao");
    await adminPage.getByLabel("Nome da instituicao",{exact:false}).waitFor();
    const internalColor=await adminPage.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue("--primary"));
    await adminPage.getByLabel("Paleta",{exact:true}).selectOption("Floresta");
    await adminPage.getByLabel("Nome da instituicao",{exact:false}).fill("Arquivo Institucional E2E");
    await adminPage.getByRole("button",{name:"Salvar configuracao",exact:true}).click();
    await adminPage.getByText("Configuracao salva.",{exact:true}).waitFor();
    assert.equal(await adminPage.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue("--primary")),internalColor);
    await page.goto(base+"/");
    await page.getByRole("heading",{name:"Arquivo Institucional E2E",exact:true}).waitFor();
    const primary=await page.locator(".portal").evaluate(el=>getComputedStyle(el).getPropertyValue("--primary"));
    assert.notEqual(primary.trim(),internalColor.trim());
    await a11y(page,"Tema institucional");
    await adminPage.getByLabel("Primaria",{exact:true}).fill("#ffffff");
    await adminPage.getByRole("button",{name:"Salvar configuracao",exact:true}).click();
    await adminPage.getByRole("alert").filter({hasText:"Revise as cores"}).waitFor();
    await adminPage.getByRole("button",{name:"Cancelar",exact:true}).click();
    await a11y(adminPage,"Configuracao institucional");
    await adminPage.setViewportSize({width:390,height:844});await screenshot(adminPage,"configuracao-mobile");
    await page.getByRole("button",{name:"Sair",exact:true}).click();await page.waitForURL(base+"/");
    await page.goto(base+"/consulta/"+iid+"/"+rid);await page.waitForURL("**/login?next=*");
    assert.deepEqual(errors,[]);
    console.log("PASS fase 6: descoberta anonima, paginacao real, login requerido, visitante sem cadastro, registros publicados, tema escopado e axe desktop/mobile.");
  } finally {
    if(original){
      const current=await json(await admin.request.get(api+"/publico/configuracao/administracao"));
      await json(await admin.request.put(api+"/publico/configuracao/administracao",{data:{...original,versao:current.versao}}));
    }
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1);});
