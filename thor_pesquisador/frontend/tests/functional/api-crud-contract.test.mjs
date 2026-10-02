import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const api = readFileSync(new URL("../../lib/api.ts", import.meta.url), "utf8");
const dashboard = readFileSync(new URL("../../app/dashboard/page.tsx", import.meta.url), "utf8");
const login = readFileSync(new URL("../../app/login/page.tsx", import.meta.url), "utf8");
const appShell = readFileSync(new URL("../../components/app-shell.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../../app/globals.css", import.meta.url), "utf8");

function assertFunction(source, name) {
  assert.match(source, new RegExp(`export function ${name}\\b|export async function ${name}\\b`));
}

function assertEndpoint(source, endpoint) {
  assert.ok(source.includes(endpoint), `Endpoint nao encontrado: ${endpoint}`);
}

test("cliente HTTP trata sucesso, 204 e erros da API", () => {
  assert.match(api, /async function request<T>/);
  assertEndpoint(api, "response.status === 204");
  assertEndpoint(api, "if (!response.ok)");
  assertEndpoint(api, "credentials: \"include\"");
});

test("funcoes de autenticacao e dashboard estao cobertas no frontend", () => {
  ["devLogin", "getGovbrStart", "me", "logout", "getDashboardStats"].forEach((name) => assertFunction(api, name));
  assertEndpoint(api, "/auth/dev-login");
  assertEndpoint(api, "/auth/govbr/start");
  assertEndpoint(api, "/auth/me");
  assertEndpoint(api, "/dashboard");
});

test("funcoes CRUD de instrumentos, campos e registros estao cobertas no frontend", () => {
  [
    "listInstrumentos",
    "getInstrumento",
    "getSchema",
    "createInstrumento",
    "updateInstrumento",
    "listCampos",
    "createCampo",
    "listRegistros",
    "searchRegistros",
    "createRegistro",
  ].forEach((name) => assertFunction(api, name));

  assertEndpoint(api, "/instrumentos");
  assertEndpoint(api, "/campos");
  assertEndpoint(api, "/registros");
  assertEndpoint(api, "/buscar");
});

test("dashboard e shell preservam pagina inicial administrativa", () => {
  assert.match(dashboard, /getDashboardStats/);
  assert.match(dashboard, /Instrumentos/);
  assert.match(appShell, /\/dashboard/);
  assert.match(appShell, /\/instrumentos/);
  assert.match(appShell, /\/pesquisa/);
});

test("login preserva identidade visual e imagem do pesquisador", () => {
  assert.match(login, /Entrar com GOV\.BR/);
  assert.match(styles, /login_pesquisador\.png/);
  assert.match(styles, /--primary: #0e6694/);
});
