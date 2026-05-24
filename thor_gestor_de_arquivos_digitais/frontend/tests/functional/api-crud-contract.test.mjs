import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const domainApi = readFileSync(new URL("../../lib/api/domain.ts", import.meta.url), "utf8");
const storageApi = readFileSync(new URL("../../lib/api/storage-addressing.ts", import.meta.url), "utf8");
const descricaoApi = readFileSync(new URL("../../lib/api/descricao-arquivistica.ts", import.meta.url), "utf8");
const clientApi = readFileSync(new URL("../../lib/api/client.ts", import.meta.url), "utf8");
const perfisPermissoesApi = readFileSync(new URL("../../lib/api/perfis-permissoes.ts", import.meta.url), "utf8");

function assertFunction(source, name) {
  assert.match(source, new RegExp(`export function ${name}\\b|export async function ${name}\\b`));
}

function assertEndpoint(source, endpoint) {
  assert.ok(source.includes(endpoint), `Endpoint nao encontrado: ${endpoint}`);
}

test("cliente HTTP trata sucesso, 204 e erros da API", () => {
  assertFunction(clientApi, "apiRequest");
  assertEndpoint(clientApi, "response.status === 204");
  assertEndpoint(clientApi, "if (!response.ok)");
  assertEndpoint(clientApi, "response.status === 401");
});

test("funcoes CRUD de unidades estao cobertas no frontend", () => {
  ["listUnidadesPage", "getUnidade", "createUnidade", "updateUnidade", "deleteUnidade"].forEach((name) =>
    assertFunction(domainApi, name),
  );
  assertEndpoint(domainApi, "/unidades-acondicionamento");
  assertEndpoint(domainApi, "method: \"POST\"");
  assertEndpoint(domainApi, "method: \"PATCH\"");
  assertEndpoint(domainApi, "method: \"DELETE\"");
});

test("funcoes CRUD de midias expostas pelo backend estao cobertas no frontend", () => {
  ["listMidiasPage", "createMidia"].forEach((name) => assertFunction(domainApi, name));
  assertEndpoint(domainApi, "/midias-armazenamento");
});

test("funcoes CRUD de instrumentos, campos e registros estao cobertas no frontend", () => {
  [
    "listInstrumentosPesquisa",
    "createInstrumentoPesquisa",
    "updateInstrumentoPesquisa",
    "deleteInstrumentoPesquisa",
    "listInstrumentoCampos",
    "createInstrumentoCampo",
    "updateInstrumentoCampo",
    "deleteInstrumentoCampo",
    "createInstrumentoRegistro",
    "listInstrumentoRegistros",
    "getInstrumentoRegistro",
    "updateInstrumentoRegistro",
    "deleteInstrumentoRegistro",
  ].forEach((name) => assertFunction(domainApi, name));
  assertEndpoint(domainApi, "/instrumentos-pesquisa");
  assertEndpoint(domainApi, "/campos");
  assertEndpoint(domainApi, "/registros");
});

test("funcoes CRUD de descricao arquivistica estao cobertas no frontend", () => {
  [
    "listarRegistrosDescricao",
    "obterRegistroDescricao",
    "criarRegistroDescricao",
    "atualizarRegistroDescricao",
    "excluirRegistroDescricao",
    "duplicarRegistroDescricao",
    "moverRegistroDescricao",
  ].forEach((name) => assertFunction(descricaoApi, name));
  assertEndpoint(descricaoApi, "/descricao-arquivistica/registros");
});

test("funcoes CRUD de enderecamento estao cobertas no frontend", () => {
  [
    "listarLocaisGuarda",
    "criarLocalGuarda",
    "obterLocalGuarda",
    "atualizarLocalGuarda",
    "excluirLocalGuarda",
    "listarZonasGuarda",
    "criarZonaGuarda",
    "atualizarZonaGuarda",
    "excluirZonaGuarda",
    "listarEstruturas",
    "criarEstrutura",
    "atualizarEstrutura",
    "excluirEstrutura",
    "listarCompartimentos",
    "criarCompartimento",
    "atualizarCompartimento",
    "excluirCompartimento",
    "listarPosicoes",
    "obterPosicao",
    "criarPosicao",
    "atualizarPosicao",
    "excluirPosicao",
  ].forEach((name) => assertFunction(storageApi, name));
  ["/locais-guarda", "/zonas-guarda", "/estruturas-armazenamento", "/compartimentos-armazenamento", "/posicoes-armazenamento"].forEach((endpoint) =>
    assertEndpoint(storageApi, endpoint),
  );
});

test("perfis tem CRUD e permissoes sao somente leitura no frontend", () => {
  [
    "listPermissoesPage",
    "getPermissao",
    "listPerfisPage",
    "getPerfil",
    "createPerfil",
    "updatePerfil",
    "deletePerfil",
  ].forEach((name) => assertFunction(perfisPermissoesApi, name));
  ["createPermissao", "updatePermissao", "deletePermissao"].forEach((name) =>
    assert.doesNotMatch(perfisPermissoesApi, new RegExp(`export function ${name}\\b|export async function ${name}\\b`)),
  );
  assertEndpoint(perfisPermissoesApi, "/permissoes");
  assertEndpoint(perfisPermissoesApi, "/perfis");
});
