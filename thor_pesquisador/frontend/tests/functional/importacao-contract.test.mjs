import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
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
test("upload usa FormData sem definir boundary e preserva operacao na retomada", () => {
  const api = source("lib/importacoes.ts"), page = source("components/importacao-registros.tsx");
  assert.match(api, /new FormData/);
  assert.match(api, /configuracao.*JSON.stringify/);
  assert.match(page, /resume\?\.configuracao.schema_version/);
  assert.match(source("lib/api.ts"), /init\?\.body instanceof FormData/);
});
