import { expect, test } from "@playwright/test";

const APP_URL = process.env.E2E_APP_URL ?? "http://localhost:3000";
const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";
const KEYCLOAK_URL = process.env.E2E_KEYCLOAK_URL ?? "http://localhost:8081";
const REALM = process.env.E2E_KEYCLOAK_REALM ?? "thor";
const CLIENT_ID = process.env.E2E_KEYCLOAK_CLIENT_ID ?? "thor-api";
const ADMIN_USER = process.env.E2E_ADMIN_USER ?? "admin";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "admin";

test("cadastra usuario, cria conta no Keycloak e autentica no Thor", async ({ page, request }) => {
  test.setTimeout(120_000);

  const suffix = `${Date.now()}${Math.random().toString(16).slice(2, 8)}`;
  const username = `e2e_usuario_${suffix}`;
  const name = `Usuario E2E ${suffix}`;
  const email = `${username}@thor.local`;
  const finalPassword = `ThorFinal${suffix}!A1`;

  await cleanupUser(request, username);

  try {
    await login(page, ADMIN_USER, ADMIN_PASSWORD);

    await page.goto(`${APP_URL}/usuarios/nova`);
    await expect(page.getByRole("heading", { name: "Novo usuário" })).toBeVisible();

    await page.locator('input[name="nome"]').fill(name);
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="email"]').fill(email);
    await page.locator('select[name="papel"]').selectOption("OPERADOR");
    await page.getByRole("button", { name: "Salvar usuário" }).click();

    await expect(page.getByText("Usuário cadastrado.")).toBeVisible();
    await page.getByRole("button", { name: "Criar no Keycloak" }).click();

    const createdBox = page.getByText("Conta criada no Keycloak.").locator("..");
    await expect(createdBox).toBeVisible();
    await expect(createdBox).toContainText(username);
    const temporaryPassword = await createdBox.locator("code").innerText();
    expect(temporaryPassword).toMatch(/\S+/);

    await clearBrowserSession(page);
    await login(page, username, temporaryPassword, finalPassword);

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText(username).first()).toBeVisible();

    const claims = await page.evaluate(async (apiUrl) => {
      const rawSession = window.localStorage.getItem("thor.auth.session");
      if (!rawSession) {
        throw new Error("Sessão não encontrada no localStorage.");
      }
      const session = JSON.parse(rawSession);
      const response = await fetch(`${apiUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${session.accessToken}` },
      });
      if (!response.ok) {
        throw new Error(`Falha em /auth/me: ${response.status}`);
      }
      return response.json();
    }, API_URL);

    expect(claims.preferred_username).toBe(username);
    expect(claims.email).toBe(email);
  } finally {
    await cleanupUser(request, username);
  }
});

async function login(page, username, password, newPassword) {
  await page.goto(`${APP_URL}/login`);
  await page.getByRole("button", { name: "Entrar com Keycloak" }).click();

  await page.locator("#username").fill(username);
  await page.locator("#password").fill(password);
  await page.locator("#kc-login").click();

  if (newPassword) {
    await page.locator("#password-new").fill(newPassword);
    await page.locator("#password-confirm").fill(newPassword);
    await page.locator("#kc-passwd-update-form button[type='submit'], #kc-form-buttons input[type='submit']").click();
  }

  await page.waitForURL(/\/dashboard$/, { timeout: 30_000 });
}

async function clearBrowserSession(page) {
  await page.evaluate(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });
  await page.context().clearCookies();
}

async function cleanupUser(request, username) {
  await deleteLocalUsers(request, username);
  await deleteKeycloakUsers(request, username);
}

async function deleteLocalUsers(request, username) {
  const token = await getRealmToken(request, ADMIN_USER, ADMIN_PASSWORD);
  const listed = await request.get(`${API_URL}/usuarios`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { q: username, limit: 100 },
  });
  if (!listed.ok()) {
    return;
  }

  const body = await listed.json();
  const matching = (body.items ?? []).filter((item) => item.username === username);
  for (const user of matching) {
    await request.delete(`${API_URL}/usuarios/${user.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}

async function deleteKeycloakUsers(request, username) {
  const token = await getAdminToken(request);
  const users = await request.get(`${KEYCLOAK_URL}/admin/realms/${REALM}/users`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { username, exact: "true" },
  });
  if (!users.ok()) {
    return;
  }

  for (const user of await users.json()) {
    await request.delete(`${KEYCLOAK_URL}/admin/realms/${REALM}/users/${user.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}

async function getRealmToken(request, username, password) {
  const response = await request.post(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
    form: {
      grant_type: "password",
      client_id: CLIENT_ID,
      username,
      password,
    },
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()).access_token;
}

async function getAdminToken(request) {
  const response = await request.post(`${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token`, {
    form: {
      grant_type: "password",
      client_id: "admin-cli",
      username: ADMIN_USER,
      password: ADMIN_PASSWORD,
    },
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()).access_token;
}
