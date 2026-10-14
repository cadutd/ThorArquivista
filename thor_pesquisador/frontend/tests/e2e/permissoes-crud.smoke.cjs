const assert = require("node:assert/strict");
const {execFileSync} = require("node:child_process");
const path = require("node:path");
const os = require("node:os");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = process.env.BASE_URL, api = process.env.API_URL;
assert.ok(base && api && process.env.THOR_E2E_ISOLATED === "true", "Use a stack isolada.");
(async () => {
  const browser = await chromium.launch({headless:true});
  const admin = await browser.newContext();
  const actor = await browser.newContext({viewport:{width:1440,height:900}});
  const page = await actor.newPage();
  const code = "UI_CRUD_" + Date.now();
  const read = ["usuarios_consultar","perfis_consultar","permissoes_consultar","acessos_consultar",
                "instrumentos_consultar","imagens_consultar"];
  let seed, created = false;
  async function json(response) {assert.ok(response.ok(), await response.text());return response.json();}
  async function update(extra) {
    await json(await admin.request.put(api + "/perfis/" + code,
      {data:{codigo:code,nome:"Permissoes UI",permissoes:[...read,...extra]}}));
  }
  try {
    await json(await admin.request.post(api + "/auth/dev-login"));
    await json(await admin.request.post(api + "/perfis",
      {data:{codigo:code,nome:"Permissoes UI",permissoes:read}}));
    created = true;
    const python = [
      "import json,sys,uuid",
      "from app.core.config import settings",
      "from app.db.session import SessionLocal",
      "from app.models.user import Usuario",
      "from app.models.editorial import AcessoInstrumento",
      "from app.services.auth_service import create_session",
      "assert settings.database_url.rsplit('/',1)[-1].endswith('_test')",
      "assert settings.mongodb_database.endswith('_test')",
      "with SessionLocal() as db:",
      " u=Usuario(nome='Permissoes UI',username='ui_'+uuid.uuid4().hex,ativo=True)",
      " db.add(u);db.flush()",
      " a=AcessoInstrumento(usuario_id=u.id,papel=sys.argv[1])",
      " db.add(a);db.commit()",
      " print(json.dumps(dict(id=str(u.id),grant=str(a.id),token=create_session(db,u),cookie=settings.session_cookie_name)))",
    ].join("\n");
    seed = JSON.parse(execFileSync("docker",["compose","-f",
      path.resolve(__dirname,"../../../docker-compose.test.yml"),"exec","-T","backend","python","-c",python,code],
      {encoding:"utf8"}).trim());
    await actor.addCookies([{name:seed.cookie,value:seed.token,url:base}]);
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto(base + "/usuarios?q=ignored");
    await page.getByRole("heading",{name:"Gestao de Usuarios",exact:true}).waitFor();
    await page.locator(".admin-navigation").getByRole("link",{name:"Perfis",exact:true}).waitFor();
    assert.equal(await page.getByRole("link",{name:"Novo usuario",exact:true}).count(),0);
    await page.getByLabel("Busca simples",{exact:true}).fill("desenvolvimento");
    await page.getByLabel("Busca simples",{exact:true}).press("Enter");
    const row = page.getByRole("row").filter({has:page.getByRole("cell",{name:"desenvolvimento",exact:true})});
    await row.waitFor();
    assert.equal(await row.getByRole("link",{name:"Editar",exact:true}).count(),0);
    await row.getByRole("button",{name:"Visualizar",exact:true}).click();
    const popup = page.getByRole("dialog",{name:"Visualizar usuario",exact:true});
    await popup.locator(".usuario-details").waitFor();
    assert.equal(await popup.getByRole("link",{name:"Editar",exact:true}).count(),0);
    assert.equal(await popup.getByRole("button",{name:"Excluir",exact:true}).count(),0);
    await page.keyboard.press("Escape");
    await page.goto(base + "/imagens");
    await page.getByRole("heading",{name:"Imagens",exact:true}).waitFor();
    assert.equal(await page.getByRole("link",{name:"Nova imagem",exact:true}).count(),0);
    await update(["usuarios_incluir","imagens_incluir"]);
    await page.goto(base + "/usuarios");
    await page.getByRole("link",{name:"Novo usuario",exact:true}).waitFor();
    assert.equal(await page.getByRole("link",{name:"Editar",exact:true}).count(),0);
    await page.goto(base + "/imagens");
    await page.getByRole("link",{name:"Nova imagem",exact:true}).waitFor();
    await page.goto(base + "/perfis");
    assert.equal(await page.getByRole("link",{name:"Novo perfil",exact:true}).count(),0);
    await update(["perfis_incluir","perfis_editar"]);
    await page.reload();
    await page.getByRole("link",{name:"Novo perfil",exact:true}).waitFor();
    await page.getByLabel("Busca simples",{exact:true}).fill(code);
    await page.getByLabel("Busca simples",{exact:true}).press("Enter");
    const profileRow = page.getByRole("row").filter({hasText:code});
    await profileRow.getByRole("link",{name:"Editar",exact:true}).waitFor();
    await profileRow.getByRole("button",{name:"Visualizar",exact:true}).click();
    const profilePopup = page.getByRole("dialog",{name:"Perfil",exact:true});
    await profilePopup.getByRole("link",{name:"Editar",exact:true}).waitFor();
    assert.equal(await profilePopup.getByRole("button",{name:"Excluir",exact:true}).count(),0);
    await page.screenshot({path:path.join(os.tmpdir(),"thor-permissoes-delegadas-desktop.png")});
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path:path.join(os.tmpdir(),"thor-permissoes-delegadas-mobile.png")});
    assert.equal((await actor.request.delete(api + "/perfis/" + code)).status(),403);
    assert.deepEqual(errors,[]);
    console.log("PASS: administracao delegada, consultar sem mutacoes, incluir sem editar, editar sem excluir, API protegida e desktop/mobile.");
  } finally {
    if(seed) {
      await admin.request.delete(api + "/acessos/" + seed.grant);
      await admin.request.delete(api + "/usuarios/" + seed.id);
    }
    if(created) await admin.request.delete(api + "/perfis/" + code);
    await browser.close();
  }
})().catch(e => {console.error(e);process.exit(1);});
