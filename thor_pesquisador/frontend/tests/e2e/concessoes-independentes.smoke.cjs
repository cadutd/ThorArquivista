const {selecionarPerfil,selecionarInstrumento} = require("./concessoes-helpers.cjs");
const assert = require("node:assert/strict");
const {execFileSync} = require("node:child_process");
const path = require("node:path");
const os = require("node:os");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true","Use exclusivamente a stack isolada.");
function cpfTeste() {
  let digits = String(Math.floor(Math.random() * 1000000000)).padStart(9,"0");
  for(const length of [9,10]) {
    const n = [...digits].reduce((sum,d,i) => sum + Number(d) * (length + 1 - i),0) * 10 % 11;
    digits += String(n === 10 ? 0 : n);
  }
  return digits;
}
(async () => {
  const browser = await chromium.launch({headless:true});
  const admin = await browser.newContext({viewport:{width:1440,height:900}});
  const reader = await browser.newContext({viewport:{width:1440,height:900}});
  const page = await admin.newPage(), view = await reader.newPage();
  let user, instrument, grant;
  const errors = [];
  page.on("pageerror",e => errors.push(e.message));
  view.on("pageerror",e => errors.push(e.message));
  async function json(response) {assert.ok(response.ok(),await response.text());return response.json();}
  try {
    await page.goto(base + "/login");
    await page.getByRole("button",{name:"Entrar em desenvolvimento"}).click();
    await page.waitForURL("**/dashboard");
    await page.goto(base + "/usuarios/novo");
    await page.getByLabel("Nome *",{exact:true}).fill("Usuario sem concessao");
    await page.getByLabel("Usuario *",{exact:true}).fill("sem_" + Date.now());
    await page.getByLabel("E-mail *",{exact:true}).fill("sem@example.org");
    await page.getByLabel("CPF *",{exact:true}).fill(cpfTeste());
    assert.equal(await page.locator('select[name="perfil_codigo"]').count(),0);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-usuario-sem-perfil-desktop.png")});
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-usuario-sem-perfil-mobile.png")});
    const created = page.waitForResponse(r => r.url() === api + "/usuarios" && r.request().method() === "POST");
    await page.getByRole("button",{name:"Salvar usuario",exact:true}).click();
    user = await json(await created);
    assert.deepEqual(user.perfis,[]);assert.equal(user.tem_acesso,false);
    await page.getByText("Usuario cadastrado. Sem acesso concedido.",{exact:true}).waitFor();
    const python = [
      "import json,sys,uuid",
      "from app.core.config import settings",
      "from app.db.session import SessionLocal",
      "from app.models.user import Usuario",
      "from app.services.auth_service import create_session",
      "assert settings.database_url.rsplit('/',1)[-1].endswith('_test')",
      "assert settings.mongodb_database.endswith('_test')",
      "with SessionLocal() as db:",
      " print(json.dumps(dict(token=create_session(db,db.get(Usuario,uuid.UUID(sys.argv[1]))),cookie=settings.session_cookie_name)))",
    ].join("\n");
    const token = JSON.parse(execFileSync("docker",["compose","-f",path.resolve(__dirname,"../../../docker-compose.test.yml"),
      "exec","-T","backend","python","-c",python,user.id],{encoding:"utf8"}).trim());
    await reader.addCookies([{name:token.cookie,value:token.token,url:base}]);
    await view.goto(base + "/dashboard");
    await view.getByRole("heading",{name:"Acesso nao concedido",exact:true}).waitFor();
    assert.equal((await reader.request.get(api + "/usuarios")).status(),403);
    await view.screenshot({path:path.join(os.tmpdir(),"thor-sem-acesso-desktop.png")});
    instrument = await json(await admin.request.post(api + "/instrumentos",{data:{nome:"Concessao " + Date.now(),tipo:"CATALOGO"}}));
    await page.getByRole("link",{name:"Conceder acesso",exact:true}).click();
    await page.waitForURL("**/acessos/novo?usuario=" + user.id);
    await selecionarPerfil(page,"CONSULTA_INTERNA");
    await selecionarInstrumento(page,instrument);
    const granted = page.waitForResponse(r => r.url() === api + "/acessos/lote" && r.request().method() === "POST");
    await page.getByRole("button",{name:"Salvar acesso",exact:true}).click();
    grant = (await json(await granted)).items[0].id;
    await page.waitForURL("**/usuarios/" + user.id + "/acessos");
    await view.goto(base + "/instrumentos");
    await view.getByRole("link",{name:instrument.nome,exact:true}).waitFor();
    assert.equal(await view.getByRole("heading",{name:"Acesso nao concedido",exact:true}).count(),0);
    const detail = await json(await admin.request.get(api + "/usuarios/" + user.id));
    assert.equal(detail.perfis[0].codigo,"CONSULTA_INTERNA");
    assert.equal(detail.tem_acesso,true);
    await json(await admin.request.delete(api + "/acessos/" + grant));grant = undefined;
    await view.reload();
    await view.getByRole("heading",{name:"Acesso nao concedido",exact:true}).waitFor();
    await view.setViewportSize({width:390,height:844});
    assert.ok(await view.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await view.screenshot({path:path.join(os.tmpdir(),"thor-sem-acesso-mobile.png")});
    assert.equal((await reader.request.get(api + "/auth/me")).status(),200);
    assert.deepEqual(errors,[]);
    console.log("PASS: cadastro sem perfil, acesso nao concedido, concessao por instrumento e revogacao sem encerrar identidade, desktop/mobile.");
  } finally {
    if(grant) await admin.request.delete(api + "/acessos/" + grant);
    if(user) await admin.request.delete(api + "/usuarios/" + user.id);
    if(instrument) await admin.request.delete(api + "/instrumentos/" + instrument.id);
    await browser.close();
  }
})().catch(e => {console.error(e);process.exit(1);});
