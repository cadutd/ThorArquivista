import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";
const read = p => readFileSync(new URL("../../" + p, import.meta.url), "utf8");
test("acoes editoriais tem operacao idempotente, versao, justificativa e permissoes", () => {
  const panel = read("components/editorial-panel.tsx");
  for(const action of ["enviar-revisao", "aprovar", "devolver", "publicar", "arquivar", "reabrir"])
    assert.ok(panel.includes(action));
  assert.match(panel, /operacao_id: crypto.randomUUID/);
  assert.match(panel, /versao, justificativa/);
  assert.match(panel, /permissions.includes/);
  assert.match(panel, /historico\?limit=20&offset=/);
});
test("consulta nao usa indice interno nem oferece comandos administrativos", () => {
  const portal = read("components/portal-records.tsx");
  assert.match(portal, /\/publico\/instrumentos/);
  assert.doesNotMatch(portal, /reindexarInstrumento|EditorialPanel|buscar-avancado/);
  assert.match(portal, /CrudPagination/);
  assert.match(portal, /aria-expanded=\{advanced\}/);
  assert.match(read("app/consulta/[id]/[registroId]/page.tsx"), /RegistroImagens.*publico/);
});
test("galeria e formularios sao reaproveitados e schema nao publica por PUT", () => {
  const gallery = read("components/registro-imagens.tsx");
  assert.match(gallery, /publico\?await request/);
  assert.match(gallery, /!publico&&!readonly/);
  assert.match(read("components/instrumento-form.tsx"), /readOnly value=\{form.status\}/);
  assert.match(read("app/instrumentos/[id]/registros/[registroId]/editar/page.tsx"), /versao: record.versao/);
});
