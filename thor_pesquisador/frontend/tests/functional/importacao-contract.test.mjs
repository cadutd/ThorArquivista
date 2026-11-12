import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import ts from "typescript";
const source = path => readFileSync(new URL("../../" + path, import.meta.url), "utf8");
test("importacao e pagina dedicada com permissoes existentes e retorno a registros", () => {
  assert.match(source("app/instrumentos/[id]/registros/importar/page.tsx"), /<AppShell><ImportacaoRegistros/);
  assert.ok(source("components/importacoes-lista.tsx").includes('href={base + "/importar"}'));
  const page = source("components/importacao-registros.tsx");
  for (const item of ["registros_incluir", "campos_incluir", "Associacao de campos", "Conferencia", "Resultado da importacao",
    "window.confirm", "Retomar importacao", "Importacoes recentes", "Invalidos", 'accept=".csv,.json"'])
    assert.ok(page.includes(item), item);
  assert.match(page, /disabled=\{busy \|\| report.invalidos > 0\}/);
  assert.ok(!page.includes("publicar") && !page.includes("exibir_publico"));
});
test("geracao de UUID v4 funciona sem crypto.randomUUID", () => {
  const compiled = ts.transpileModule(source("lib/uuid.ts"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS }
  }).outputText;
  const sandbox = {
    exports: {},
    globalThis: { crypto: { getRandomValues: bytes => bytes.fill(0) } }
  };
  vm.runInNewContext(compiled, sandbox);
  assert.equal(sandbox.exports.criarUuid(), "00000000-0000-4000-8000-000000000000");
});
test("importacao permite gerenciar campos persistentes respeitando permissoes", () => {
  const fields = source("components/importacao-campos-schema.tsx");
  for (const item of ['method: "PUT"', 'method: "DELETE"', "validacoesJson", "opcoesJson", "onSchemaChange"])
    assert.ok(fields.includes(item), item);
  for (const path of ["components/importacao-registros.tsx", "components/importacao-detalhe.tsx"]) {
    const page = source(path);
    assert.match(page, /<ImportacaoCamposSchema/);
    assert.match(page, /usePermission\("campos_editar"/);
    assert.match(page, /usePermission\("campos_excluir"/);
  }
});
test("upload usa FormData sem definir boundary e preserva operacao na retomada", () => {
  const api = source("lib/importacoes.ts"), page = source("components/importacao-registros.tsx");
  assert.match(api, /new FormData/);
  assert.match(api, /configuracao.*JSON.stringify/);
  assert.match(page, /resume\?\.configuracao.schema_version/);
  assert.match(source("lib/api.ts"), /init\?\.body instanceof FormData/);
});
