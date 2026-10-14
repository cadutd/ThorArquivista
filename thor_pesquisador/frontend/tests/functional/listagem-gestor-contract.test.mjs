import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=p=>readFileSync(new URL("../../"+p,import.meta.url),"utf8");
test("Administracao mantem alinhamento e apenas submenus recebem recuo",()=>{
  const css=source("app/globals.css");
  assert.ok(css.includes(".admin-navigation > a.nav-link"));
  assert.ok(!css.includes(".admin-navigation > .nav-link"));
});
test("paginacao compartilha barra de Unidades de Acondicionamento com paginas numeradas",()=>{
  const pagination=source("components/crud-pagination.tsx");
  for(const label of ["Primeira","Anterior","Pr&oacute;xima","&Uacute;ltima","Por p&aacute;gina:"]) assert.ok(pagination.includes(label));
  assert.ok(pagination.includes("registros de") && pagination.includes("useId"));
  assert.ok(pagination.includes("getPaginationItems") && pagination.includes("pagination-page-current"));
  assert.ok(pagination.includes('page === "ellipsis"') && pagination.includes("aria-current"));
  const instruments=source("app/instrumentos/page.tsx");
  assert.equal((instruments.match(/<CrudPagination/g)||[]).length,2);
  assert.ok(!instruments.includes("function Pagination"));
  assert.ok(source("components/registro-imagens.tsx").includes("listVinculos(instrumentoId,registroId,offset,pageSize)"));
});
test("primeira coluna dos CRUDs e navegavel e usa cor primaria",()=>{
  for(const file of ["components/administracao-list.tsx","components/access-list.tsx","app/instrumentos/page.tsx",
    "app/imagens/page.tsx","app/instrumentos/[id]/registros/page.tsx","app/instrumentos/[id]/campos/page.tsx"]) {
    assert.ok(source(file).includes('className="crud-record-link"'),file);
  }
  assert.match(source("app/globals.css"),/\.crud-record-link\s*\{ color: hsl\(var\(--primary\)\)/);
});

test("rotulo Por pagina fica centralizado e junto do seletor",()=>{
  assert.ok(source("components/crud-pagination.tsx").includes('className="pagination-page-size"'));
  const css=source("app/globals.css");
  assert.match(css,/\.crud-pagination \.actions \{[^}]*align-items: center/);
  assert.match(css,/\.pagination-page-size \{[^}]*align-items: center[^}]*white-space: nowrap/);
});
