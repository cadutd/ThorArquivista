const assert = require("node:assert/strict");
const path = require("node:path"), os = require("node:os");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const {selecionarPerfil,selecionarInstrumento} = require("./concessoes-helpers.cjs");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true","Use exclusivamente a stack isolada.");
function cpfTeste() {
  let value = String(Math.floor(Math.random()*1000000000)).padStart(9,"0");
  for(const length of [9,10]) {
    const digit = [...value].reduce((sum,d,i)=>sum+Number(d)*(length+1-i),0)*10%11;
    value += String(digit === 10 ? 0 : digit);
  }
  return value;
}
(async () => {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage(),code="LOTE_" + Date.now();
  const profiles=[],instruments=[],grants=[],errors=[];
  let user;
  page.on("pageerror",e=>errors.push(e.message));
  async function json(response) {assert.ok(response.ok(),await response.text());return response.json();}
  async function overflow() {assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
  try {
    await page.goto(base + "/login");
    await page.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
    await page.waitForURL("**/dashboard");
    user=await json(await context.request.post(api + "/usuarios",{data:{
      nome:"Usuario do lote " + code,username:code.toLowerCase(),email:code.toLowerCase()+"@example.org",cpf:cpfTeste()
    }}));
    for(let n=1;n<=2;n++) {
      profiles.push(await json(await context.request.post(api + "/perfis",{data:{
        codigo:code+"_"+n,nome:"Perfil "+n+" "+code,permissoes:["instrumentos_consultar"]
      }})));
      instruments.push(await json(await context.request.post(api + "/instrumentos",{data:{
        nome:"Instrumento "+n+" "+code,tipo:"CATALOGO"
      }})));
    }
    grants.push((await json(await context.request.post(api + "/acessos",{data:{
      usuario_id:user.id,papel:"CONSULTA_INTERNA"
    }}))).id);
    await page.goto(base + "/acessos/novo");
    const users=page.getByRole("group",{name:"Pesquisa de usuarios",exact:true});
    await users.getByLabel("Nome",{exact:true}).fill(user.nome);
    await users.getByLabel("Nome de usuario",{exact:true}).fill(user.username);
    await users.getByLabel("Email",{exact:true}).fill(user.email);
    await users.getByLabel("Email",{exact:true}).press("Enter");
    await users.getByRole("radio",{name:"Selecionar "+user.nome,exact:true}).check();
    await page.getByRole("region",{name:"Acessos existentes",exact:true}).getByRole("row").filter({hasText:"CONSULTA_INTERNA"}).waitFor();
    for(const profile of profiles) await selecionarPerfil(page,profile.codigo);
    const instrumentGroup=page.getByRole("group",{name:"Pesquisa de instrumentos",exact:true});
    assert.ok(await instrumentGroup.getByLabel("Nome",{exact:true}).isDisabled());
    await page.getByRole("radio",{name:"Por instrumento",exact:true}).check();
    await instrumentGroup.getByLabel("Nome",{exact:true}).fill(code);
    await instrumentGroup.getByLabel("Tipo",{exact:true}).selectOption("CATALOGO");
    await instrumentGroup.getByLabel("Status",{exact:true}).selectOption("RASCUNHO");
    await instrumentGroup.getByLabel("Nome",{exact:true}).press("Enter");
    for(const instrument of instruments) await instrumentGroup.getByRole("checkbox",{name:"Selecionar "+instrument.nome,exact:true}).check();
    assert.ok((await page.getByRole("region",{name:"Resumo da concessao"}).innerText()).includes("4"));
    await overflow();
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-lote-desktop.png"),fullPage:true});
    await page.getByRole("radio",{name:"Global",exact:true}).check();
    assert.ok(await instrumentGroup.getByLabel("Nome",{exact:true}).isDisabled());
    assert.ok((await page.getByLabel("Instrumentos selecionados",{exact:true}).innerText()).includes(": 0"));
    // An overlapping profile rejects the entire batch, including valid new profiles.
    await selecionarPerfil(page,"CONSULTA_INTERNA");
    const conflict=page.waitForResponse(r=>r.url()===api+"/acessos/lote" && r.request().method()==="POST");
    await page.getByRole("button",{name:"Salvar acesso",exact:true}).click();
    assert.equal((await conflict).status(),409);
    await page.getByRole("alert").filter({hasText:"sobreposta"}).waitFor();
    assert.equal((await json(await context.request.get(api+"/acessos?usuario_id="+user.id))).total,1);
    await page.getByRole("group",{name:"Pesquisa de perfis",exact:true}).getByRole("row").filter({hasText:"CONSULTA_INTERNA"}).getByRole("checkbox").uncheck();
    await selecionarInstrumento(page,instruments[0]);
    await selecionarInstrumento(page,instruments[1]);
    await page.setViewportSize({width:390,height:844});
    await overflow();
    await page.getByRole("region",{name:"Resumo da concessao"}).scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(os.tmpdir(),"thor-concessoes-lote-mobile.png"),fullPage:true});
    const created=page.waitForResponse(r=>r.url()===api+"/acessos/lote" && r.request().method()==="POST");
    await page.getByRole("button",{name:"Salvar acesso",exact:true}).click();
    const result=await json(await created);
    assert.equal(result.total,4);grants.push(...result.items.map(i=>i.id));
    await page.waitForURL("**/acessos");
    assert.equal((await json(await context.request.get(api+"/acessos?usuario_id="+user.id))).total,5);
    // A successful global batch persists no instrument IDs.
    await page.goto(base+"/acessos/novo?usuario="+user.id);
    await selecionarPerfil(page,"PUBLICO_AUTENTICADO");
    const global=page.waitForResponse(r=>r.url()===api+"/acessos/lote" && r.request().method()==="POST");
    await page.getByRole("button",{name:"Salvar acesso",exact:true}).click();
    const globalResult=await json(await global);grants.push(...globalResult.items.map(i=>i.id));
    assert.equal(globalResult.total,1);
    assert.equal(globalResult.items[0].instrumento_id,null);
    await page.waitForURL("**/usuarios/"+user.id+"/acessos");
    assert.deepEqual(errors,[]);
    console.log("PASS: pesquisa por nome/username/email, acessos existentes, multiplos perfis/instrumentos, filtros tipo/status, escopo global desabilitado, limpeza do escopo, validacao atomica e desktop/mobile.");
  } finally {
    for(const id of grants) await context.request.delete(api+"/acessos/"+id);
    for(const profile of profiles) await context.request.delete(api+"/perfis/"+profile.codigo);
    for(const instrument of instruments) await context.request.delete(api+"/instrumentos/"+instrument.id);
    if(user) await context.request.delete(api+"/usuarios/"+user.id);
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1);});
