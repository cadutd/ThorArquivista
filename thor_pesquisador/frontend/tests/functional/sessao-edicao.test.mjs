import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {safeReturnPath,loginPath,notifySessionExpired} from "../../lib/auth-navigation.mjs";

test("retorno de login aceita somente destinos internos sem loops", () => {
  for(const value of [null,undefined,"https://outside.example","//outside.example","/%2foutside.example",
      "/\\outside.example","/login","/login?next=/perfis","/a/../login","/usuarios%0d%0aLocation:x","/%ZZ"])
    assert.equal(safeReturnPath(value),"/dashboard",String(value));
  for(const value of ["/usuarios","/acessos/novo?usuario=abc","/instrumentos?q=Ana%20Maria","/consulta/a#imagens"])
    assert.equal(safeReturnPath(value),value);
  assert.equal(loginPath("/perfis?ativo=true"),"/login?next=%2Fperfis%3Fativo%3Dtrue");
  assert.doesNotThrow(notifySessionExpired);
});
test("rotas protegidas tem guarda e apenas descoberta e login ficam abertos", () => {
  const source=p=>readFileSync(new URL("../../"+p,import.meta.url),"utf8");
  assert.ok(source("app/layout.tsx").includes("<SessionGuard>"));
  const guard=source("components/session-guard.tsx");
  for(const value of ['pathname==="/"||pathname==="/consulta"||pathname==="/login"','"/auth/me"',"e.status === 401","window.location.replace","SESSION_EXPIRED",
                      'addEventListener("focus"','addEventListener("visibilitychange"',"setInterval","controller.abort()"])
    assert.ok(guard.includes(value),value);
  for(const file of ["lib/api.ts","lib/imagens.ts"])
    assert.ok(source(file).includes("response.status === 401) notifySessionExpired()"));
  assert.ok(source("app/login/page.tsx").includes("safeReturnPath"));
});
test("edicao de acessos reutiliza inclusao e requer incluir ao expandir", () => {
  const source=p=>readFileSync(new URL("../../"+p,import.meta.url),"utf8");
  assert.ok(source("components/acesso-editor.tsx").includes("<AcessoCadastro id={id}"));
  const form=source("components/acesso-cadastro.tsx");
  assert.ok(form.includes('method:id ? "PUT" : "POST"') && form.includes('"/lote"'));
  assert.ok(form.includes('request<Acesso>("/acessos/" + id)') && form.includes("setOriginal(access)"));
  assert.ok(form.includes("editing && count > 1 && !canInclude"));
});
