import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
const read = file => readFileSync(new URL("../../" + file, import.meta.url), "utf8");

test("visualizacao de instrumento exibe todos os metadados da API e a imagem", () => {
  const view = read("app/instrumentos/[id]/page.tsx");
  for (const field of ["id","nome","tipo","descricao","status","visibilidade","schema_version",
    "versao_editorial","publicacao_id","imagem_card_id","criado_em","atualizado_em"])
    assert.ok(view.includes("instrumento." + field), field);
  assert.match(view, /<InstrumentoCardImage/);
  assert.match(view, /alt=\{"Imagem do instrumento/);
  assert.match(view, /crud-details/);
  assert.match(view, /<EditorialPanel/);
});

test("exclusoes de instrumento, registro e imagem ficam nos detalhes e exigem confirmacao", () => {
  for (const root of ["instrumentos", "imagens", "instrumentos/[id]/registros"]) {
    const list = read("app/" + root + "/page.tsx");
    assert.doesNotMatch(list, /deleteInstrumento|deleteRegistro|deleteImagem|Trash2|window\.confirm/);
    const view = read("app/" + root + (root.includes("registros") ? "/[registroId]" : "/[id]") + "/page.tsx");
    assert.match(view, /window\.confirm/);
    assert.match(view, /_excluir/);
    assert.match(view, /disabled=\{removing\}/);
  }
});

test("acoes destrutivas de conformidade so sao disponibilizadas nos detalhes", () => {
  const source = read("components/conformidade-actions.tsx");
  assert.match(source, /detail=false/);
  assert.match(source, /detail&&\["PENDENTE"/);
  assert.match(source, /detail&&p\.ativo/);
  assert.match(source, /confirmation&&<AdministracaoDetails/);
  assert.match(read("components/conformidade-detail.tsx"), /row=\{data\} detail/);
});

test("tabelas usam acoes ghost, formulario responsivo e detalhes compactos do Gestor", () => {
  const style = read("app/globals.css");
  assert.match(style, /\.table \.icon-button \{[^}]*border-color: transparent; background: transparent/);
  assert.match(style, /\.crud-detail-field dt \{[^}]*font-size: 12px/);
  assert.match(style, /\.crud-detail-field dd \{[^}]*font-size: 14px/);
  assert.match(style, /\.app-frame form \.grid, \.crud-details \{ grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/);
  for (const file of ["app/instrumentos/page.tsx", "app/imagens/page.tsx", "components/administracao-list.tsx",
    "components/access-list.tsx", "components/conformidade-list.tsx", "components/importacoes-lista.tsx",
    "components/portal-catalog.tsx", "components/portal-records.tsx"])
    assert.match(read(file), /crud-actions-heading/, file);
});

test("pesquisa avancada pagina no servidor e preserva a consulta aplicada", () => {
  const source = read("app/pesquisa/page.tsx");
  assert.equal((source.match(/\{pagination\}/g) || []).length, 2);
  assert.match(source, /offset: page \* size/);
  assert.match(source, /consultarPagina\(applied, page, pageSize\)/);
  assert.match(source, /consultarPagina\(applied, 0, size\)/);
  assert.match(source, /version !== requestVersion\.current/);
  assert.match(source, /title="Visualizar registro"/);
});
