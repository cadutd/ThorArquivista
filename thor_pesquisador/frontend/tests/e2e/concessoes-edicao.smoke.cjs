const assert=require("node:assert/strict"),os=require("node:os"),path=require("node:path");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const {selecionarPerfil,selecionarInstrumento}=require("./concessoes-helpers.cjs");
const base=process.env.BASE_URL,api=process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED==="true","Use apenas a stack isolada.");
function cpfTeste() {
  let value=String(Math.floor(Math.random()*1000000000)).padStart(9,"0");
  for(const size of [9,10]) {const digit=[...value].reduce((s,d,i)=>s+Number(d)*(size+1-i),0)*10%11;value+=String(digit===10?0:digit);}
  return value;
}
(async()=>{
  const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage(),code="EDICAO_"+Date.now(),profiles=[],instruments=[],grants=[],errors=[];
  let user,original,unrelated;
  page.on("pageerror",e=>errors.push(e.message));
  async function json(r) {assert.ok(r.ok(),await r.text());return r.json();}
  try {
    await page.goto(base+"/login");await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    user=await json(await context.request.post(api+"/usuarios",{data:{nome:"Edicao "+code,username:code.toLowerCase(),email:code.toLowerCase()+"@example.org",cpf:cpfTeste()}}));
    for(let n=1;n<=2;n++) {
      profiles.push(await json(await context.request.post(api+"/perfis",{data:{codigo:code+"_"+n,nome:"Perfil de edicao "+n+" "+code,permissoes:["instrumentos_consultar"]}})));
      instruments.push(await json(await context.request.post(api+"/instrumentos",{data:{nome:"Instrumento de edicao "+n+" "+code,tipo:"CATALOGO"}})));
    }
    original=(await json(await context.request.post(api+"/acessos",{data:{usuario_id:user.id,papel:profiles[0].codigo,instrumento_id:instruments[0].id}}))).id;grants.push(original);
    unrelated=(await json(await context.request.post(api+"/acessos",{data:{usuario_id:user.id,papel:"PUBLICO_AUTENTICADO"}}))).id;grants.push(unrelated);
    const before=await json(await context.request.get(api+"/acessos/"+unrelated));
    await page.goto(base+"/acessos/"+original+"/editar?usuario="+user.id);
    await page.getByLabel("Usuario selecionado",{exact:true}).getByText(user.nome,{exact:true}).waitFor();
    assert.ok((await page.getByLabel("Perfis selecionados",{exact:true}).innerText()).includes(profiles[0].nome));
    assert.ok((await page.getByLabel("Instrumentos selecionados",{exact:true}).innerText()).includes(instruments[0].nome));
    assert.ok(await page.getByRole("radio",{name:"Por instrumento",exact:true}).isChecked());
    await page.getByRole("region",{name:"Acessos existentes",exact:true}).getByRole("row").filter({hasText:"PUBLICO_AUTENTICADO"}).waitFor();
    await selecionarPerfil(page,profiles[1].codigo);
    await selecionarInstrumento(page,instruments[1]);
    assert.ok((await page.getByLabel("Perfis selecionados",{exact:true}).innerText()).includes(": 2"));
    assert.ok((await page.getByLabel("Instrumentos selecionados",{exact:true}).innerText()).includes(": 2"));
    await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-edicao-compartilhada-desktop.png")});
    await page.setViewportSize({width:390,height:844});
    await page.getByRole("region",{name:"Resumo da concessao",exact:true}).scrollIntoViewIfNeeded();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-edicao-compartilhada-mobile.png")});
    const saved=page.waitForResponse(r=>r.url()===api+"/acessos/"+original+"/lote" && r.request().method()==="PUT");
    await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();
    const result=await json(await saved);
    assert.equal(result.total,4);assert.equal(result.items[0].id,original);
    grants.push(...result.items.filter(i=>i.id!==original).map(i=>i.id));
    await page.waitForURL("**/usuarios/"+user.id+"/acessos");
    assert.deepEqual(await json(await context.request.get(api+"/acessos/"+unrelated)),before);
    assert.equal((await json(await context.request.get(api+"/acessos?usuario_id="+user.id))).total,5);
    await page.goto(base+"/acessos/"+original+"/editar");
    await page.getByLabel("Usuario selecionado",{exact:true}).waitFor();
    await page.getByRole("radio",{name:"Global",exact:true}).check();
    assert.ok(await page.getByRole("group",{name:"Pesquisa de instrumentos",exact:true}).getByLabel("Nome",{exact:true}).isDisabled());
    const conflict=page.waitForResponse(r=>r.url()===api+"/acessos/"+original+"/lote" && r.request().method()==="PUT");
    await page.getByRole("button",{name:"Salvar alteracoes",exact:true}).click();
    assert.equal((await conflict).status(),409);
    await page.getByRole("alert").filter({hasText:"sobreposta"}).waitFor();
    assert.equal((await json(await context.request.get(api+"/acessos/"+original))).instrumento_id,instruments[0].id);
    assert.deepEqual(errors,[]);
    console.log("PASS: edicao com fluxo da inclusao, pre-selecao, multiplos perfis/instrumentos, preservacao de ID e outros acessos, conflito atomico e desktop/mobile.");
  } finally {
    for(const id of grants) await context.request.delete(api+"/acessos/"+id);
    for(const p of profiles) await context.request.delete(api+"/perfis/"+p.codigo);
    for(const i of instruments) await context.request.delete(api+"/instrumentos/"+i.id);
    if(user) await context.request.delete(api+"/usuarios/"+user.id);
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1);});
