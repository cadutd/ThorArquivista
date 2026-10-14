import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source = p => readFileSync(new URL("../../" + p, import.meta.url), "utf8");
test("menu administrativo segue Gestor sem Eventos ou Administracao Geral", () => {
  const shell = source("components/app-shell.tsx");
  for(const path of ["/usuarios","/perfis","/permissoes"]) assert.ok(shell.includes(path));
  assert.ok(shell.includes("admin-navigation"));
  assert.ok(!shell.includes('href: "/eventos"') && !shell.includes('href: "/admin"'));
  assert.ok(!shell.includes("Administracao Geral"));
});
test("listagens administrativas usam busca, filtros, paginacao dupla e tooltips", () => {
  const page = source("components/administracao-list.tsx");
  assert.ok(page.includes("onSubmit") && page.includes("URLSearchParams") && page.includes("offset"));
  assert.equal((page.match(/<CrudPagination/g) || []).length, 2);
  for(const label of ["Visualizar","Editar"]) assert.ok(page.includes('title="' + label + '"'));
  const popup = source("components/perfil-popup.tsx");
  assert.ok(popup.includes('title="Excluir perfil"') && popup.includes("window.confirm"));
});
test("perfis usam formulario compartilhado e concessoes preservam selecao por escopo", () => {
  const profile = source("components/perfil-editor.tsx");
  assert.ok(profile.includes("toggle") && profile.includes('type="checkbox"') && profile.includes("Salvar"));
  const access = source("components/acesso-editor.tsx");
  assert.ok(access.includes('/perfis?ativo=true') && access.includes("Escopo global"));
  assert.ok(source("components/access-list.tsx").includes('query.set("usuario_id"'));
});

test("usuarios tem cadastro completo, consulta em popup e edicao em pagina propria", () => {
  const list = source("components/administracao-list.tsx");
  assert.ok(list.includes("<UsuarioPopup") && list.includes('href="/usuarios/novo"'));
  assert.ok(list.includes("setSelectedUser(id)") && list.includes('title="Visualizar"'));
  const editor = source("components/usuario-editor.tsx");
  for(const field of ["username", "cpf", "email", "perfil_codigo", "ativo", "observacoes"]) assert.ok(editor.includes(field));
  assert.ok(editor.includes('method:id ? "PUT" : "POST"') && !editor.includes("<AccessList"));
  assert.ok(!editor.includes("<EntitySelect") && editor.includes("usuario-form-grid"));
  assert.ok(source("components/usuario-escopos.tsx").includes("<AccessList"));
  assert.ok(source("app/usuarios/[id]/editar/page.tsx").includes("<UsuarioEditor"));
  const popup = source("components/usuario-popup.tsx");
  assert.ok(popup.includes("<ModalFrame") && popup.includes('"/editar"') && popup.includes('method:"DELETE"'));
  assert.ok(popup.includes("window.confirm") && popup.includes('title="Excluir usuario"'));
});

test("popup de usuario usa o layout do Gestor sem alterar outros dialogs", () => {
  const popup = source("components/usuario-popup.tsx"),css = source("app/globals.css");
  assert.ok(popup.includes('className="usuario-popup"') && popup.includes('className="usuario-observacoes"'));
  assert.ok(popup.includes("button secondary") && popup.includes("button usuario-delete"));
  assert.ok(css.includes("768px") && css.includes(".usuario-details, .administracao-details") && css.includes("grid-template-columns: repeat(2, minmax(0, 1fr))"));
  assert.ok(css.includes("text-transform: uppercase") && css.includes(".usuario-popup-actions, .administracao-popup-actions { justify-content: flex-end"));
  assert.ok(source("components/modal-frame.tsx").includes("bounds.left"));
});

test("perfis usam popup e formulario isolado, preservando ADMIN e flags de sistema", () => {
  const editor = source("components/perfil-editor.tsx"),popup = source("components/perfil-popup.tsx");
  assert.ok(editor.includes("administracao-editor-page") && editor.includes("administracao-form-grid"));
  assert.ok(!editor.includes("<AdministracaoList") && !editor.includes("<CrudPagination"));
  assert.ok(editor.includes('codigo === "ADMIN"') && editor.includes('readOnly={!!codigo}'));
  assert.ok(popup.includes("<AdministracaoDetails") && popup.includes('codigo !== "ADMIN"'));
  assert.ok(source("app/perfis/[codigo]/page.tsx").includes("perfilInicial={codigo}"));
});

test("permissoes sao somente leitura, sem acoes de mutacao no popup", () => {
  const list = source("components/administracao-list.tsx");
  const readOnly = list.slice(list.indexOf('{tipo === "permissoes" && selected &&'));
  assert.ok(readOnly.includes("<AdministracaoDetails") && !readOnly.includes("actions="));
  assert.ok(list.includes('tipo !== "permissoes"') && list.includes('tipo === "perfis"'));
  const details = source("components/administracao-details.tsx");
  assert.ok(!details.includes("request(") && !details.includes('method:"'));
});
