const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL;
const api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true", "Use a stack com bancos e fila isolados.");

(async () => {
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:900}});
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", e => errors.push(e.message));
  let instrument;
  async function json(response) {
    assert.ok(response.ok(), String(response.status()) + ": " + await response.text());
    return response.json();
  }
  async function publishUI(url, endpoint) {
    await page.goto(url);
    for(const [action, label] of [["enviar-revisao","Enviar para revisao"],["aprovar","Aprovar"],["publicar","Publicar"]]) {
      const response = page.waitForResponse(r => r.url() === api + endpoint + "/editorial/" + action && r.request().method() === "POST");
      await page.getByRole("button", {name:label,exact:true}).click();
      await json(await response);
    }
  }
  try {
    await page.goto(base + "/login");
    await page.getByRole("button", {name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    instrument = await json(await context.request.post(api + "/instrumentos", {data:{
      nome:"Editorial smoke " + Date.now(),tipo:"CATALOGO",visibilidade:"PUBLICO",
    }}));
    const prefix = "/instrumentos/" + instrument.id;
    for(const [key, flag] of [["titulo",true],["segredo",false]]) {
      await json(await context.request.post(api + prefix + "/campos", {data:{
        nome:key,chave:key,tipo:"TEXTO_CURTO",exibir_publico:flag,facetavel:flag,
      }}));
    }
    const record = await json(await context.request.post(api + prefix + "/registros", {data:{
      dados:{titulo:"Documento publicado",segredo:"NAO_DIVULGAR"},
    }}));
    const recordPath = prefix + "/registros/" + record.id;
    const imageTitle = "Imagem publica " + Date.now();
    const image = await json(await context.request.post(api + "/imagens/upload", {multipart:{
      titulo:imageTitle,direitos_acesso:"PUBLICO",
      arquivo:{name:"documento.png",mimeType:"image/png",buffer:fs.readFileSync(path.resolve(__dirname,"../../public/images/login_pesquisador.png"))},
    }}));
    await page.goto(base + recordPath);
    await page.getByRole("tab", {name:"Imagens",exact:true}).click();
    await page.getByRole("button", {name:"Vincular imagem",exact:true}).click();
    await page.getByLabel("Buscar imagem").fill(imageTitle);
    await page.getByLabel("Buscar imagem").press("Enter");
    const bind = page.waitForResponse(r => r.url() === api + recordPath + "/imagens" && r.request().method() === "POST");
    await page.getByRole("dialog").getByRole("row").filter({hasText:imageTitle}).getByRole("button", {name:"Vincular imagem",exact:true}).click();
    await json(await bind);
    await page.getByText(/RASCUNHO.*Versao 2/).waitFor();
    await publishUI(base + prefix, prefix);
    await publishUI(base + recordPath, recordPath);
    await page.getByRole("button",{name:"Versoes publicadas",exact:true}).click();
    await page.getByText("Versao 2", {exact:false}).first().waitFor();
    const publicPrefix = api + "/publico" + prefix;
    let ready = false;
    for(let n=0;n<180;n++) {
      const response = await context.request.get(publicPrefix + "/buscar");
      if(response.ok()) {ready=true;break;}
      await new Promise(resolve=>setTimeout(resolve,500));
    }
    assert.ok(ready,"Worker deve concluir a projecao publica.");
    const anonymous = await browser.newContext({viewport:{width:1440,height:900}});
    const publicPage = await anonymous.newPage();
    await publicPage.goto(base + "/consulta");
    await publicPage.waitForURL("**/login?next=*");
    await publicPage.getByRole("button",{name:"Entrar em desenvolvimento",exact:true}).click();
    await publicPage.waitForURL("**/consulta");
    await publicPage.getByRole("combobox").first().selectOption(instrument.id);
    await publicPage.getByRole("link",{name:"Documento publicado",exact:true}).waitFor();
    await publicPage.getByLabel("Buscar registros publicados").fill("Documento");
    const query = publicPage.waitForResponse(r=>r.url().includes("/publico" + prefix + "/buscar") && r.url().includes("q=Documento"));
    await publicPage.getByLabel("Buscar registros publicados").press("Enter");
    await json(await query);
    assert.ok(!(await publicPage.locator("body").innerText()).includes("NAO_DIVULGAR"));
    await publicPage.getByRole("link",{name:"Documento publicado",exact:true}).click();
    await publicPage.getByRole("tab",{name:"Imagens"}).click();
    await publicPage.locator(".image-tile img").waitFor();
    await publicPage.waitForFunction(()=>document.querySelector(".image-tile img")?.naturalWidth > 0);
    assert.equal(await publicPage.getByRole("button",{name:"Vincular imagem"}).count(),0);
    await publicPage.locator(".thumbnail-button").click();
    await publicPage.waitForFunction(()=>document.querySelector("dialog .media-large")?.naturalWidth > 0);
    await publicPage.getByRole("button",{name:"Fechar",exact:true}).click();
    await publicPage.screenshot({path:path.join(os.tmpdir(),"thor-fase4-desktop.png")});
    await publicPage.setViewportSize({width:390,height:844});
    await publicPage.screenshot({path:path.join(os.tmpdir(),"thor-fase4-mobile.png")});
    assert.ok(await publicPage.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth));
    const current = await json(await context.request.get(api + recordPath));
    await json(await context.request.put(api + recordPath, {data:{
      dados:{titulo:"Novo rascunho",segredo:"SEGREDO_NOVO"},versao:current.versao,
    }}));
    assert.deepEqual((await json(await anonymous.request.get(publicPrefix + "/registros/" + record.id))).dados,{titulo:"Documento publicado"});
    await publishUI(base + recordPath, recordPath);
    assert.deepEqual((await json(await anonymous.request.get(publicPrefix + "/registros/" + record.id))).dados,{titulo:"Novo rascunho"});
    const fresh = await json(await context.request.get(api + recordPath));
    await json(await context.request.put(api + recordPath, {data:{dados:{titulo:"Inativo"},versao:fresh.versao,status:"INATIVO"}}));
    assert.equal((await anonymous.request.get(publicPrefix + "/registros/" + record.id)).status(),404);
    await anonymous.close();
    assert.deepEqual(errors,[]);
    console.log("PASS: revisao, aprovacao, publicacao, versoes, consulta autenticada, galeria real, rascunho, republicacao, revogacao e responsividade.");
  } finally {
    if(instrument) {
      const latest = await context.request.get(api + "/instrumentos/" + instrument.id);
      if(latest.ok()) {
        const data = await latest.json();
        await context.request.post(api + "/instrumentos/" + instrument.id + "/arquivar", {data:{
          operacao_id:crypto.randomUUID(),versao:data.versao_editorial,justificativa:"Encerramento do teste isolado",
        }});
      }
    }
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
