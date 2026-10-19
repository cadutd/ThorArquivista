import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {colorErrors} from "../../lib/portal-colors.mjs";
const source=p=>readFileSync(new URL("../../"+p,import.meta.url),"utf8");
const colors={primaria:"#0e6496",secundaria:"#235347",destaque:"#8f2453",fundo:"#ffffff",texto:"#17232d"};

test("paleta valida contraste e rejeita injecao antes do envio",()=>{
  assert.deepEqual(colorErrors(colors),{});
  for(const value of ["url(javascript:x)","#fff","red","</style>",""])assert.ok(colorErrors({...colors,primaria:value})["cores.primaria"]);
  assert.ok(colorErrors({...colors,texto:"#eeeeee"})["cores.texto"]);
  assert.ok(colorErrors({...colors,destaque:"#ffffff"})["cores.destaque"]);
});

test("landing real com assets, busca e ranking honesto",()=>{
  assert.ok(source("app/page.tsx").includes("PortalHome"));
  const home=source("components/portal-home.tsx");
  for(const value of ["/publico/destaques","com_acessos","Instrumentos publicados","router.push","Pesquisar instrumentos"])
    assert.ok(home.includes(value),value);
  const css=source("app/portal.css");
  assert.ok(css.includes('url("/images/login_pesquisador.png")')&&css.includes(".portal-hero"));
  assert.ok(!css.includes("body {")&&!css.includes(":root"));
});

test("catalogo so pesquisa instrumentos e conserva paginacao padrao",()=>{
  const catalog=source("components/portal-catalog.tsx");
  assert.ok(catalog.includes("/publico/instrumentos?")&&!catalog.includes('"/buscar'));
  assert.equal((catalog.match(/<CrudPagination /g)||[]).length,2);
  assert.ok(catalog.includes("setPage(0)")&&catalog.includes("useSearchParams"));
  assert.ok(catalog.includes('<table className="table"')&&!catalog.includes("PortalCards"));
  for(const key of ["nome","tipo","descricao"])assert.ok(catalog.includes("draft."+key));
  assert.ok(source("components/portal-cards.tsx").includes('prefetch={false}'));
});

test("sessao opcional publica nunca aciona endpoint 401 para descobrir visitante",()=>{
  const shell=source("components/portal-shell.tsx");
  assert.ok(shell.includes('"/auth/estado"')&&!shell.includes('"/auth/me"'));
  assert.ok(shell.includes("identity.area_interna")&&shell.includes("identity.autenticado"));
  assert.ok(!shell.includes('<Link href="/consulta">Instrumentos</Link>'));
  assert.ok(source("components/session-guard.tsx").includes("if(publicRoute) return"));
});

test("cards usam capa opcional e imagem padrao sem alterar formato",()=>{
  assert.ok(source("components/portal-cards.tsx").includes("InstrumentoCardImage"));
  const image=source("components/instrumento-card-image.tsx");
  assert.ok(image.includes("DEFAULT_INSTRUMENTO_IMAGE")&&image.includes("onError"));
  assert.ok(image.includes("width={960}")&&image.includes("height={540}"));
  const internal=source("app/instrumentos/page.tsx");
  for(const key of ["nome","tipo","status","visibilidade","descricao"])assert.ok(internal.includes("draftFilters."+key));
  assert.ok(source("components/instrumento-form.tsx").includes("InstrumentoCoverField"));
});

test("configuracao usa identidade interna e paleta de preview escopada",()=>{
  const settings=source("components/portal-settings.tsx");
  for(const value of ["portal_configuracao_consultar","portal_configuracao_editar","page-heading","panel stack","colorErrors","type=\"color\"","Restaurar padrao","portalStyle(form.cores)"])
    assert.ok(settings.includes(value),value);
  const library=source("lib/portal.ts");
  assert.ok(library.includes('"--primary"')&&library.includes("CSSProperties"));
  assert.ok(source("components/app-shell.tsx").includes('href:"/portal/configuracao"'));
});

test("registros mantem filtros sob demanda e nao prebuscam conteudo protegido",()=>{
  const records=source("components/portal-records.tsx");
  assert.ok(records.includes("if(!advanced)return")&&records.includes('path+"/facetas"'));
  assert.ok(records.includes('path+"/acessos"')&&records.includes("counted.current"));
  assert.equal((records.match(/<CrudPagination /g)||[]).length,2);
  assert.ok(records.includes("prefetch={false}")&&records.includes("setFilters({...draft})"));
});
