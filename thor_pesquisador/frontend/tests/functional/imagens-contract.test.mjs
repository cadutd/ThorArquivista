import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";

const read = path => readFileSync(new URL("../../"+path,import.meta.url),"utf8");
const api=read("lib/imagens.ts");
const table=read("app/imagens/page.tsx");
const form=read("components/imagem-form.tsx");
const gallery=read("components/registro-imagens.tsx");
const detail=read("app/instrumentos/[id]/registros/[registroId]/page.tsx");
const preview=read("components/media-preview.tsx");

test("cliente usa multipart sem sobrescrever boundary e trata 204",()=>{
 assert.match(api,/instanceof FormData/);
 assert.match(api,/credentials: "include"/);
 assert.match(api,/response.status === 204/);
 for(const name of ["listImagens","getImagem","createImagem","updateImagem","deleteImagem","uploadImagem","listVinculos","vincularImagem","editarVinculo","reordenarImagens","desvincularImagem"])assert.ok(api.includes("const "+name));
});
test("CRUD de imagens tem pagina completa, filtros, paginacao dupla e confirmacao",()=>{
 assert.match(table,/pageIndex\*pageSize/);
 assert.match(table,/setPageIndex\(0\)/);
 assert.match(table,/aria-expanded=\{advanced\}/);
 assert.equal((table.match(/<CrudPagination/g)||[]).length,2);
 assert.match(table,/window.confirm/);
 assert.match(table,/title="Visualizar"/);
 assert.match(table,/title="Editar"/);
 assert.match(read("app/imagens/novo/page.tsx"),/ImagemForm/);
 assert.match(read("app/imagens/\[id\]/editar/page.tsx"),/getImagem\(id\)/);
});
test("formulario valida titulo, metadados e campos condicionais",()=>{
 assert.match(form,/Informe o titulo/);
 assert.match(form,/JSON.parse\(metadata\)/);
 assert.match(form,/type="file"/);
 assert.match(form,/type="url"/);
 assert.match(form,/Salvando\.\.\./);
 assert.match(form,/data.set\("metadados_json"/);
 assert.match(form,/tipo_referencia==="UPLOAD"\?null/);
});
test("galeria so carrega na aba e fornece capa, legenda, reordenacao e desvinculo",()=>{
 assert.match(detail,/tab==="imagens"\?<RegistroImagens/);
 assert.match(gallery,/listVinculos\(instrumentoId,registroId,offset\)/);
 assert.match(gallery,/window.confirm/);
 assert.match(gallery,/Salvar legenda/);
 assert.match(gallery,/Marcar como principal/);
 assert.match(gallery,/reordenarImagens/);
 assert.match(preview,/manifest.sequences/);
 assert.match(preview,/manifest.items/);
 assert.match(preview,/AbortController/);
 assert.match(preview,/safeHttp/);
});
