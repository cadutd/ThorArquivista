const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const https = require("node:https"), crypto = require("node:crypto");
const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE || "@playwright/test");
const base = "https://localhost:8443";
assert.equal(process.env.THOR_E2E_LOCAL_GOVBR, "true", "Use somente o perfil local gov.br.");
const ca = fs.readFileSync(path.resolve(__dirname, "../../../.local/govbr-root.crt"));

async function tlsProbe() {
  return new Promise((resolve, reject) => {
    https.get(base + "/api/v1/auth/opcoes", { ca }, response => {
      const authorized = response.socket.authorized;
      let body = "";
      response.on("data", chunk => body += chunk);
      response.on("end", () => {
        try {
          assert.equal(authorized, true);
          assert.equal(response.statusCode, 200);
          assert.equal(typeof JSON.parse(body).login_desenvolvimento, "boolean");
          resolve();
        } catch (error) { reject(error); }
      });
    }).on("error", reject);
  });
}

(async () => {
  await tlsProbe();
  const browser = await chromium.launch({ headless: true });
  // Tests never install trust; use the existing user trust store when requested.
  const trusted = process.env.THOR_E2E_TRUSTED_CA === "true";
  const context = await browser.newContext({ ignoreHTTPSErrors: !trusted });
  const page = await context.newPage(), errors = [];
  let authorization;
  page.on("pageerror", error => errors.push(error.message));
  await context.route("https://sso.staging.acesso.gov.br/authorize?**", async route => {
    authorization = new URL(route.request().url());
    await route.fulfill({ contentType: "text/html", body: "<h1>Provedor simulado</h1>" });
  });
  try {
    await page.goto(base + "/login?next=%2Fconsulta");
    await page.getByRole("button", { name: "Entrar com GOV.BR", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Provedor simulado" })).toBeVisible();
    assert.equal(authorization.searchParams.get("redirect_uri"), base + "/api/v1/auth/govbr/callback");
    assert.equal(authorization.searchParams.get("response_type"), "code");
    assert.equal(authorization.searchParams.get("code_challenge_method"), "S256");
    assert.ok(authorization.searchParams.get("client_id") && authorization.searchParams.get("client_id") !== "change-me");
    assert.equal(authorization.searchParams.has("client_secret"), false);
    const cookies = await context.cookies(base);
    for (const name of ["thor_auth_state", "thor_auth_nonce", "thor_auth_verifier", "thor_auth_return_to"]) {
      const cookie = cookies.find(item => item.name === name);
      assert.ok(cookie && cookie.secure && cookie.httpOnly && cookie.sameSite === "Lax", name);
    }
    const verifier = cookies.find(cookie => cookie.name === "thor_auth_verifier").value;
    assert.equal(authorization.searchParams.get("code_challenge"), crypto.createHash("sha256").update(verifier).digest("base64url"));
    await page.goto(base + "/login");
    await page.getByRole("button", { name: "Entrar em desenvolvimento", exact: true }).click();
    await page.waitForURL(base + "/dashboard");
    const identity = await page.evaluate(async () => {
      const response = await fetch("/api/v1/auth/me");
      return { status: response.status, id: (await response.json()).id };
    });
    assert.equal(identity.status, 200);
    assert.ok(identity.id);
    assert.ok((await context.cookies(base)).find(cookie => cookie.name === "thor_pesquisador_session" && cookie.secure && cookie.httpOnly));
    assert.equal(await page.evaluate(async () => (await fetch("/api/v1/auth/logout", { method: "POST" })).status), 200);
    assert.equal(await page.evaluate(async () => (await fetch("/api/v1/auth/me")).status), 401);
    assert.deepEqual(errors, []);
    console.log("PASS: certificado validado com CA local, mesma origem HTTPS, botao gov.br/PKCE/callback/cookies e sessao local. Provedor interceptado; nenhuma autenticacao real nem envio de segredo ao gov.br. Navegador com TLS normal: " + trusted);
  } finally { await browser.close(); }
})().catch(error => { console.error(error.name + ": " + error.message.split("Call log:")[0].trim()); process.exitCode = 1; });
