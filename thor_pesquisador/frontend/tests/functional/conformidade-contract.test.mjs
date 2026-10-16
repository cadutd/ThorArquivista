import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=p=>readFileSync(new URL("../../"+p,import.meta.url),"utf8");
test("fase 5 reutiliza a estrutura de Instrumentos e a paginacao compartilhada",()=>{
  const list=source("components/conformidade-list.tsx");
  for(const part of ["AppShell","panel stack","page-heading","CrudPagination","crud-record-link","icon-button","aria-label","SlidersHorizontal","setPage(0)","detailPath(tipo,row)","Limpar filtros"])
    assert.ok(list.includes(part),part);
  assert.equal((list.match(/<CrudPagination /g)||[]).length,2);
  assert.ok(!list.includes("style={{")&&!list.includes("fetch("));
  assert.ok(!list.includes("AdministracaoDetails")&&!list.includes("setSelected"));
});
test("formularios de fase 5 tem paginas dedicadas e pesquisa lazy",()=>{
  const editor=source("components/conformidade-editor.tsx");
  for(const part of ["panel stack","page-heading","InstrumentoLookup","ArrowLeft","required","saving"])
    assert.ok(editor.includes(part),part);
  const lookup=source("components/instrumento-lookup.tsx");
  assert.ok(lookup.includes("if(!open) return")&&lookup.includes("limit:String(size)")&&lookup.includes("offset:String(page*size)"));
  assert.ok(lookup.includes("createPortal")&&lookup.includes("e.stopPropagation()"));
});
test("download compartilha cliente autenticado e nao usa URLs assinadas persistentes",()=>{
  const api=source("lib/api.ts");
  assert.ok(api.includes("async function requestResponse")&&api.includes("await requestResponse(path)")&&api.includes("notifySessionExpired()"));
  assert.ok(source("components/conformidade-actions.tsx").includes("downloadFile("));
});

test("auditoria, exportacoes, relatorios e retencao pertencem a Administracao",()=>{
  const shell=source("components/app-shell.tsx"),navigation=shell.slice(shell.indexOf("const navigation"),shell.indexOf("const administration"));
  const admin=shell.slice(shell.indexOf("const administration"),shell.indexOf("export function AppShell"));
  for(const route of ["/auditoria","/exportacoes","/relatorios","/retencao/politicas"]) {
    assert.ok(!navigation.includes(route),route+" fora da raiz");
    assert.ok(admin.includes('href:"'+route+'"'),route+" dentro de Administracao");
  }
  assert.ok(shell.includes("anyScope={item.anyScope}"));
  assert.ok(admin.includes('prefix:"/retencao"'));
});

test("visualizacoes dedicadas compartilham acoes, permissoes e detalhes de Instrumentos",()=>{
  const details=source("components/conformidade-detail.tsx"),actions=source("components/conformidade-actions.tsx");
  for(const part of ["detail-grid","detail-item","page-heading","panel stack","ConformidadeActions","encodeURIComponent(id)","role=\"alert\""])
    assert.ok(details.includes(part),part);
  for(const route of ["auditoria/[fonte]/[id]","exportacoes/[id]","retencao/politicas/[id]","retencao/execucoes/[id]"])
    assert.ok(source("app/"+route+"/page.tsx").includes("ConformidadeDetail"),route);
  for(const permission of ["exportacoes_excluir","exportacoes_repetir","retencao_excluir","retencao_simular","retencao_executar","retencao_cancelar"])
    assert.ok(actions.includes(permission),permission);
  assert.ok(actions.includes("AdministracaoDetails")&&actions.includes("setConfirmation"));
});

test("relatorios usam layout e paginacao comuns sem apresentar dados antigos em erros",()=>{
  const reports=source("components/relatorios.tsx");
  assert.ok(reports.includes('className="panel stack"')&&reports.includes('className="page-heading"'));
  assert.equal((reports.match(/<CrudPagination /g)||[]).length,2);
  assert.ok(reports.includes('setData(undefined)')&&reports.includes("filters===paginationState.filters?paginationState.page:0"));
  assert.ok(reports.includes('<Permission acao="relatorios_consultar"><Permission acao="usuarios_consultar">'));
});
