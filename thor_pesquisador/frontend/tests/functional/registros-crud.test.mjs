import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const read = path => readFileSync(new URL("../../" + path, import.meta.url), "utf8");
const root = "app/instrumentos/[id]/registros/";
const list = read(root + "page.tsx"), form = read("components/registro-form.tsx");

test("registros usam paginacao CRUD dupla e consulta limitada no servidor", () => {
  assert.match(list, /CrudPagination/);
  assert.equal((list.match(/\{pagination\}/g) || []).length, 2);
  assert.match(list, /offset: pageIndex \* pageSize/);
  assert.doesNotMatch(list, /Carregar mais|nextCursor|\.\.\.previous\s*,\s*\.\.\./);
  assert.match(list, /setPageIndex\(0\)/);
  assert.match(list, /if \(!current\) return/);
});

test("listagem tem busca explicita, filtros, limpar e acoes autorizadas", () => {
  assert.match(list, /onSubmit=\{buscar\}/);
  assert.match(list, /Filtros avancados/);
  assert.match(list, /campo\.aparece_busca/);
  for (const action of ["incluir", "editar"]) assert.match(list, new RegExp('acao="registros_' + action + '"'));
  for (const title of ["Visualizar registro", "Editar registro"])
    assert.ok(list.includes('title="' + title + '"'));
  assert.doesNotMatch(list, /deleteRegistro|window\.confirm|Excluir registro/);
  assert.match(list, /crud-record-link/);
});

test("criacao e edicao compartilham formulario e retornam a listagem", () => {
  for (const path of ["novo/page.tsx", "[registroId]/editar/page.tsx"]) {
    const page = read(root + path);
    assert.match(page, /<RegistroForm/);
    assert.match(page, /router\.push\(base\)/);
    assert.match(page, /href=\{base\}/);
    assert.match(page, /page-heading/);
  }
  assert.match(form, /className="panel stack"/);
  assert.match(form, /disabled=\{saving\}/);
  assert.match(form, /Salvando\.\.\./);
  assert.match(form, /fieldErrors/);
});

test("visualizacao preserva imagens editorial retencao e acoes no cabecalho", () => {
  const page = read(root + "[registroId]/page.tsx");
  for (const component of ["RegistroImagens", "EditorialPanel", "RetencaoRegistro"]) assert.match(page, new RegExp("<" + component));
  assert.match(page, /acao="registros_excluir"/);
  assert.match(page, /window\.confirm/);
});
