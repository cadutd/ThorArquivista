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
  const access = source("components/acesso-cadastro.tsx");
  assert.ok(access.includes('/perfis?ativo=true') && access.includes("Escopo da concessao"));
  assert.ok(source("components/access-list.tsx").includes('query.set("usuario_id"'));
});

test("usuarios tem cadastro completo, consulta em popup e edicao em pagina propria", () => {
  const list = source("components/administracao-list.tsx");
  assert.ok(list.includes("<UsuarioPopup") && list.includes('href="/usuarios/novo"'));
  assert.ok(list.includes("setSelectedUser(id)") && list.includes('title="Visualizar"'));
  const editor = source("components/usuario-editor.tsx");
  for(const field of ["username", "cpf", "email", "ativo", "observacoes"]) assert.ok(editor.includes(field));
  assert.ok(editor.includes('method:id ? "PUT" : "POST"') && !editor.includes("<AccessList"));
  assert.ok(!editor.includes("<EntitySelect") && editor.includes("usuario-form-grid"));
  assert.ok(!editor.includes("perfil_codigo") && !editor.includes("/perfis?"));
  assert.ok(editor.includes("Conceder acesso") && editor.includes('acao="acessos_incluir"'));
  assert.ok(source("components/permission.tsx").includes("Acesso nao concedido"));
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

test("concessoes compartilham identidade visual de usuarios e popup sob demanda", () => {
  const list=source("components/access-list.tsx"),editor=source("components/acesso-cadastro.tsx");
  assert.equal((list.match(/<CrudPagination/g) || []).length,2);
  assert.ok(list.includes("<AcessoPopup") && list.includes("setSelected(row.id)"));
  assert.ok(list.includes('title="Visualizar"') && list.includes("instrumento_nome") && list.includes("perfil_nome"));
  assert.ok(!list.includes("Trash2") && !list.includes("method:"));
  assert.ok(editor.includes("administracao-editor-page") && editor.includes("administracao-form-grid"));
  assert.ok(editor.includes("<AccessList") && editor.includes("readonly hideHeading"));
  assert.ok(source("components/acesso-editor.tsx").includes("<AcessoCadastro id={id}"));
  const popup=source("components/acesso-popup.tsx");
  assert.ok(popup.includes("<AdministracaoDetails") && popup.includes("window.confirm") && popup.includes('method:"DELETE"'));
  assert.ok(popup.includes('acao="acessos_editar"') && popup.includes('acao="acessos_excluir"'));
  assert.ok(source("app/acessos/[id]/page.tsx").includes("acessoInicial={id}"));
});

test("inclusao de concessoes usa etapas, selecao multipla e gravacao atomica", () => {
  const page=source("app/acessos/novo/page.tsx"),form=source("components/acesso-cadastro.tsx");
  assert.ok(page.includes("<AcessoCadastro"));
  for(const label of ["Nome de usuario","Email","Acessos existentes","Perfis selecionados","Instrumentos selecionados","Resumo da concessao"])
    assert.ok(form.includes(label));
  assert.ok(form.includes('key:"tipo"') && form.includes('key:"status"'));
  assert.ok(form.includes('disabled={scope === "GLOBAL"}') && form.includes('setInstruments([])'));
  assert.ok(form.includes('"/acessos/lote"') && form.includes("instrumento_ids:") && form.includes("perfis:"));
  assert.ok(form.includes("selected.filter") && form.includes("[...selected,item]"));
  assert.ok(form.includes("<CrudPagination") && form.includes("offset:String(page*size)"));
});

test("cadastro de concessoes compartilha superficie, detalhes e controles administrativos", () => {
  const page=source("components/acesso-cadastro.tsx"),css=source("app/globals.css");
  assert.ok(page.includes('className="administracao-editor-surface"') && page.includes('className="administracao-editor-content concessao-editor-content"'));
  assert.ok(page.includes("administracao-form-grid") && page.includes('readonly hideHeading'));
  assert.ok(page.includes("administracao-details concessao-selected-user"));
  assert.ok(page.includes(">Limpar</button>") && page.includes('title={"Buscar "'));
  assert.ok(css.includes("accent-color: hsl(var(--primary))"));
  assert.ok(!css.includes(".concessao-step:disabled { opacity:"));
});
