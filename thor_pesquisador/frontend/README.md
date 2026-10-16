# Frontend

## Atualizacao de 2026-10-16

Cadastro de usuarios separado das concessoes; inclusao e edicao de acessos
compartilham pesquisa e selecao multipla. Permissoes por operacao e escopo sao
validadas no backend. Todas as telas exigem sessao, exceto /login, com retorno
seguro a pagina solicitada. A massa dev/test possui 60 usuarios e 24 perfis.

Fase 5 implementada: auditoria unificada e imutavel, exportacoes autenticadas
CSV/JSON/pacote, jobs recuperaveis, relatorios, logs estruturados e politicas
de retencao com simulacao, impedimentos e expurgo autorizado.
Validacao acumulada: 360 testes backend e 47 contratos frontend no Docker isolado.
Na revisao de 2026-10-16, os 47 contratos, a compilacao e quatro fluxos Playwright
(conformidade, administracao, sessao e permissoes CRUD) passaram. A verificacao
incluiu exportacao/download, edicao e simulacao de retencao, desativacao/reativacao
de politica, relatorios, escopos, detalhes dedicados e telas desktop/mobile.

Atualizacao de 2026-10-16: Auditoria, Exportacoes, Relatorios e Retencao estao
no menu Administracao e seguem a identidade de Instrumentos (titulos,
filtros Buscar/Limpar filtros, tabelas, paginacao dupla e formularios em grid).
Auditoria, exportacoes, politicas e execucoes possuem visualizacao em pagina
propria. Permissoes, comandos por estado e confirmacoes foram preservados.
Os demais CRUDs administrativos mantem seus popups existentes.
Detalhes, operacao, permissoes e limitacoes em
[Operacao da fase 5](../docs/fase_05_operacao.md).
Os numeros de validacao nas secoes historicas abaixo referem-se as respectivas
entregas anteriores, nao ao total atual. A fase 6 permanece planejada.

Interface web do `thor_pesquisador`, implementada com Next.js, React e TypeScript.

## Responsabilidades

- Login institucional com gov.br e login de desenvolvimento local.
- Dashboard inicial autenticado em `/dashboard`.
- Shell administrativo com identidade visual alinhada ao Thor Gestor.
- Instrumentos, campos dinamicos, registros e pesquisa.
- Busca avancada por instrumento com filtros, facetas, ordenacao e reindexacao manual.
- Consumo da API FastAPI.
- Administracao com Auditoria, Exportacoes, Relatorios e Retencao respeitando escopos.
- Formularios e detalhes dessas funcoes em paginas proprias, no padrao de Instrumentos.

## Identidade Visual

O frontend deve manter a mesma linguagem visual do `thor_gestor_de_arquivos_digitais`:

- paleta clara com azul institucional;
- sidebar administrativa;
- header fixo;
- cards de metricas;
- tabelas e formularios objetivos;
- dashboard como pagina inicial autenticada.

Os dois frontends importam uma copia identica de `app/thor-theme.css`, com
tokens de cor e tipografia base do Thor Gestor. As copias permitem builds Docker
independentes; ao alterar o tema, atualizar ambos os arquivos. O teste
`theme-contract.test.mjs` verifica a paridade quando executado no monorepo.
Os estilos especificos do Pesquisador continuam em `app/globals.css`, usando
14 px para controles e tabelas, 16 px para titulos de paineis e 24 px para
titulos de pagina, sem reduzir o tamanho raiz de 16 px.

A tela de login usa o asset:

```text
public/images/login_pesquisador.png
```

## Comandos

Via Docker Compose:

```bash
docker compose build frontend
docker compose up -d
```

Teste funcional de contrato, executado localmente como no Thor Gestor:

```bash
npm run test:functional
npm run test:functional:report
```

Rotas principais:

- `http://localhost:3000/login`
- `http://localhost:3000/dashboard`
- `http://localhost:3000/instrumentos`
- `http://localhost:3000/instrumentos/novo`
- `http://localhost:3000/instrumentos/{id}`
- `http://localhost:3000/instrumentos/{id}/editar`
- `http://localhost:3000/pesquisa`

## CRUD de Instrumentos

O CRUD de instrumentos segue o padrao Thor CRUD Base:

- listagem paginada no servidor com `limit` e `offset`;
- busca simples por `q` com reset para a primeira pagina;
- paginas completas para criacao e edicao;
- visualizacao somente leitura em rota propria;
- formulario reutilizavel com campos obrigatorios, erros de campo e estado `Salvando...`;
- exclusao com confirmacao explicita antes de chamar a API.

## Busca Simples de Registros

A busca simples na listagem de registros aplica o termo ao enviar pelo botao
Buscar ou pela tecla Enter. Carregar mais preserva esse termo e o cursor;
editar o texto sem enviar nao altera os resultados ja pesquisados.
Enviar o campo vazio restaura a listagem geral. O teste
`npm run test:e2e:registros-busca` valida esses fluxos com a API real,
criando e removendo apenas dados proprios; requer login de desenvolvimento.

Campo vazio nao abre filtros: recarrega a listagem. Com apenas um registro,
a tabela pode continuar igual. O botao mostra o estado de carregamento;
respostas antigas nao sobrescrevem uma consulta mais recente.

## Busca Avancada

A rota `/pesquisa` consome:

- `POST /instrumentos/{id}/buscar-avancado`
- `GET /instrumentos/{id}/facetas`
- `POST /instrumentos/{id}/reindexar`

Os filtros e ordenacoes sao gerados a partir das propriedades dos campos dinamicos:

- `filtro_avancado`
- `facetavel`
- `ordenavel`

Essa rota permanece interna, autenticada e autorizada por escopo. A fase 4
acrescenta `/consulta` como superficie publica separada, sem comandos administrativos.

## Configuracao

A URL publica da API e definida por:

```text
NEXT_PUBLIC_API_BASE_URL
```

Em build standalone, o Dockerfile copia `public/` para garantir que imagens e assets estaticos sejam servidos pelo container.
A URL publica da API e compilada no build; alterar somente a variavel de
runtime nao substitui o rebuild com o argumento correto.

## Kubernetes/OKD

O container deve rodar sem root e com UID arbitrario. Ajuste `PUBLIC_APP_URL`, CORS no backend e Route/Ingress conforme o ambiente.

## Imagens (Fase 3)

O menu Imagens abre `/imagens`, com busca, filtros por tipo/acesso e
paginacao no servidor, acima e abaixo da tabela. Acoes usam icones com
nomes acessiveis e tooltip. Rotas completas:

- `/imagens/novo`.
- `/imagens/{id}`.
- `/imagens/{id}/editar`.
- `/instrumentos/{id}/registros/{registroId}`: metadados e aba Imagens.

O formulario compartilhado aceita URL, manifest IIIF, repositorio externo
ou arquivo para upload S3. Metadados adicionais usam JSON. O backend valida
o MIME real e tamanho; a interface apresenta erros sem descartar o formulario.

A galeria carrega apenas ao abrir a aba Imagens. O seletor de imagens existentes
usa busca e paginacao da API, sem carregar o acervo inteiro.
Cada vinculo permite legenda, principal, ordenacao e remocao confirmada.
Uma imagem pode ser reutilizada entre registros. Imagens maiores e manifests
IIIF sao buscados apenas ao abrir a previa; binarios IIIF nao sao duplicados.
Os dialogs usam foco modal nativo e fechamento por Escape.

Miniaturas de upload usam o endpoint autenticado, com cookies da sessao.
A busca mostra resumo e miniatura disponivel, sem carregar a galeria.
Permissoes sao aplicadas pelo backend; alterar/excluir exige permissao explicita
e autoria, salvo ADMIN. Vinculos tambem respeitam o estado editorial do registro.
IIIF e URLs externas precisam permitir acesso e CORS no provedor.

### Validacao de Navegador

Para contratos, execute `npm run test:functional` em container. Para o fluxo completo,
inicie `docker-compose.test.yml` com perfil `e2e` e armazenamento privado.
Com dependencias frontend e Chromium do Playwright disponiveis:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e:imagens
npm run test:e2e:registros-busca
```

O script usa `BASE_URL` (padrao localhost:3000) e `API_URL` (padrao
localhost:8000/api/v1), cria dados proprios e remove-os ao concluir.
Defina BASE_URL=http://localhost:3001 e API_URL=http://localhost:8001/api/v1
para usar exclusivamente a stack isolada. Requer login local e bucket configurado.
O teste de registros requer apenas a API ativa, sem bucket ou MinIO.
Valida API/S3 reais, upload, acesso protegido, edicao, URL/IIIF, legenda,
capa, ordem, compartilhamento e exclusao bloqueada. Somente o manifest IIIF
externo e simulado. Capturas desktop/mobile ficam no diretorio temporario do SO.

## Editorial, Acessos e Consulta (Fase 4)

- `/revisao`: fila paginada por escopo.
- `/acessos`: CRUD autorizado por operacao de papeis globais ou por instrumento, com seletores
  pesquisaveis, paginas completas e acoes com tooltips.
- Detalhes de instrumento/registro: estado, comandos editoriais, justificativa,
  historico paginado e versoes publicadas consultadas sob demanda.
- `/instrumentos/{id}/registros/{registroId}/editar`: formulario compartilhado;
  editar uma publicacao cria rascunho e preserva o snapshot vigente.
- `/consulta`: catalogo paginado de publicacoes, filtros e detalhes do snapshot; exige sessao ativa.
  A galeria reutiliza RegistroImagens e MediaPreview, sem botoes de alteracao.

O PermissionProvider carrega permissoes globais/por escopo; botoes respeitam
estado e permissao, mas a autorizacao efetiva permanece no backend.
Dashboard continua sendo a primeira tela autenticada, com pendencias e
publicacoes recentes agregadas no PostgreSQL.

Para e2e, use exclusivamente a stack `docker-compose.test.yml` com perfil
`e2e`, frontend 3001 e API 8001. O fluxo editorial exige `THOR_E2E_ISOLATED=true`.
Com Chromium e Playwright ja disponiveis:

```bash
BASE_URL=http://localhost:3001 API_URL=http://localhost:8001/api/v1 THOR_E2E_ISOLATED=true node tests/e2e/editorial.smoke.cjs
BASE_URL=http://localhost:3001 API_URL=http://localhost:8001/api/v1 npm run test:e2e:registros-busca
BASE_URL=http://localhost:3001 API_URL=http://localhost:8001/api/v1 npm run test:e2e:imagens
```

[Operacao da fase 4](../docs/fase_04_operacao.md) descreve inicializacao,
isolamento de testes, matriz de acesso e limitacoes operacionais.

## Administracao

Menu agrupado como no Gestor, sem Eventos ou Administracao Geral:
`/usuarios`, `/perfis`, `/permissoes` e `/acessos`. O menu tem acesso pelo cabecalho
no celular. Usuarios possuem visualizacao em popup (nome e icone Visualizar),
criacao em `/usuarios/novo` e edicao em `/usuarios/{id}/editar`.
O formulario inclui nome, usuario, CPF, e-mail, ativo e observacoes;
concessoes adicionais por instrumento usam a pagina propria
`/usuarios/{id}/acessos`, acessada por Perfis e escopos. A edicao contem somente
o formulario, sem busca, tabela ou paginacao de concessoes abaixo.
O popup usa duas colunas, campos com borda, observacoes separadas e acoes
alinhadas a direita; a edicao usa formulario de duas colunas como no Gestor.
Exclusao confirmada ocorre no popup e preserva o historico no backend. Perfis usam
formulario compartilhado com permissoes por checkbox e situacao.
Perfis usam popup no mesmo padrao dos usuarios: campos com borda, descricao
separada, permissoes associadas e acoes a direita. Criacao e edicao usam
paginas proprias com formulario de duas colunas, sem a busca abaixo.
ADMIN e protegido; a indicacao de perfil de sistema permanece somente leitura.
Permissoes possuem catalogo pesquisavel e popup no mesmo padrao visual,
somente leitura: nao ha inclusao, edicao, exclusao ou botoes dessas acoes.
Listagens usam filtros recolhidos, paginacao dupla e acoes com tooltips.

`administracao.smoke.cjs` valida o modulo com API real na stack isolada.
`usuarios.smoke.cjs` valida cadastro, CPF invalido, popup, edicao em pagina
propria, desativacao, reativacao e exclusao em desktop/mobile.
`perfis-permissoes.smoke.cjs` valida CRUD de perfis, ADMIN protegido,
popups desktop/mobile e ausencia de mutacoes no catalogo de permissoes.
Consulte [Administracao](../docs/administracao_acessos.md).

As listagens usam links azuis na primeira coluna. A barra paginada reproduz
Unidades de Acondicionamento do Gestor: contagem, Primeira/Anterior, paginas
numeradas com destaque da atual e reticencias, Proxima/Ultima e seletor ao final.
Instrumentos, administracao, imagens e galerias reutilizam CrudPagination.
Registros dinamicos preservam pagina por cursor e Carregar mais filtrado.

## Permissoes por Operacao

Os oito CRUDs (instrumentos, campos, registros, imagens, galerias, usuarios,
perfis e concessoes) usam codigos independentes para Consultar, Incluir,
Editar e Excluir, inclusive na administracao. Menus e botoes respeitam esses
codigos; a autorizacao efetiva permanece no backend, com escopos por instrumento
e protecao contra escalada de privilegios na delegacao administrativa.

As permissoes dos varios perfis ativos do usuario sao somadas, respeitando
o escopo de cada concessao; perfis inativos nao autorizam operacoes.
A API retorna 403 em tentativas nao autorizadas, inclusive por acesso direto,
e 401 quando nao ha sessao valida. Ocultar um botao nao substitui essa validacao.
Alteracoes de concessoes/perfis valem na proxima requisicao ao backend;
uma tela ja aberta pode precisar de recarga para atualizar menus e botoes.

Com dev_admin_enabled e govbr_dev_login habilitados em dev/test, Entrar em
desenvolvimento provisiona a concessao ADMIN global para a conta reservada
de desenvolvimento. Essa conta possui acesso total e nao serve para avaliar
restricoes de um perfil comum. Os testes de permissoes usam usuarios sem ADMIN
na stack isolada. A massa sintetica nao cria senhas nem sessoes para seus usuarios.

A migration `20261013_000009` preserva os perfis e acessos atuais e substitui
os agrupamentos antigos por permissoes granulares. O catalogo de Permissoes
permanece somente leitura. Consulte a matriz e as regras de rollback em
[Administracao de Acessos](../docs/administracao_acessos.md).

Validacao: 230 testes backend e 41 contratos frontend, executados no Docker
isolado. O teste `frontend/tests/e2e/permissoes-crud.smoke.cjs` cobre a
interface com usuario nao administrador e verificacoes desktop/mobile.

## Cadastro Sem Perfil

Desde a migration `20261014_000010`, o cadastro de usuarios nao atribui perfis.
Permissoes sao concedidas exclusivamente em Concessoes de acesso, globais ou
por instrumento. Varios perfis podem coexistir, sem perfil principal.
Os vinculos antigos, IDs e historico foram preservados; origem USUARIO dos
legados e apenas procedencia historica.

Apos cadastrar, Conceder acesso aparece somente para quem possui essa permissao.
Usuarios ativos sem concessoes podem autenticar-se, mas a interface informa
Acesso nao concedido e as APIs internas continuam protegidas. Consultas de
usuarios mostram os perfis concedidos e a situacao de acesso. A protecao do
ultimo administrador tambem cobre revogacoes simultaneas.

O teste `concessoes-independentes.smoke.cjs` cobre o novo fluxo em desktop/mobile.

## Concessoes em Lote

O cadastro de acesso pesquisa usuario por nome, nome de usuario e email,
mostra seus acessos existentes e permite selecionar varios perfis ativos.
O escopo global desabilita a pesquisa de instrumentos; no escopo por instrumento,
a pesquisa usa Nome, Tipo e Status e permite selecionar varios instrumentos.
Um resumo apresenta os acessos que serao criados antes da confirmacao.

POST /api/v1/acessos/lote valida todos os vinculos antes de inserir e grava
o lote em uma unica transacao, sem inclusoes parciais. Duplicidades,
sobreposicoes global/instrumento para o mesmo perfil, referencias invalidas
e delegacao superior aos privilegios do operador sao rejeitadas. A edicao
em pagina propria e o popup de visualizacao permanecem disponiveis.

Validado no Docker isolado: 230 testes backend, 41 contratos frontend e
teste de navegador concessoes-lote.smoke.cjs com layout desktop/mobile.

## Massa de Acessos para Desenvolvimento

O gerador app.scripts.seed_acessos cria 60 usuarios e 24 perfis sinteticos,
com situacoes ativas/inativas, usuarios sem acesso e multiplas concessoes.
E idempotente, restrito a dev/test e nao sobrescreve cadastros existentes.
Consulte [Massa de testes de acessos](../docs/massa_teste_acessos.md).
A inclusao de concessoes reutiliza a identidade visual de Usuarios e Perfis,
com Cadastro, controles do tema, buscas com Limpar e paginacao compartilhada.

## Edicao de Acessos e Sessao Ativa

Inclusao e edicao reutilizam o mesmo formulario: usuario, acessos existentes,
multiplos perfis e escopo global ou varios instrumentos. A edicao carrega as
selecoes atuais e salva em PUT /api/v1/acessos/{id}/lote. Preserva o ID original,
datas/origem e os outros acessos; somente as combinacoes adicionais sao inseridas.
A operacao exige acessos_editar, e acessos_incluir quando gera novos vinculos.
Duplicidades, sobreposicoes, delegacao indevida e remocao do ultimo administrador
sao bloqueadas, com rollback de toda a operacao.

Todas as telas, inclusive /consulta, verificam a sessao no backend antes de exibir
seu conteudo. A unica tela aberta sem sessao e /login. A guarda revalida ao navegar,
ao retornar a aba/janela e periodicamente a cada 60 segundos. Qualquer resposta
401 dos clientes da API, incluindo imagens/upload, encaminha ao login.
Respostas 403 indicam falta de permissao e nao encerram uma sessao valida.

O parametro next preserva caminho, filtros e fragmento da pagina solicitada.
O login de desenvolvimento e o callback gov.br so aceitam destinos internos;
enderecos externos e retornos para login sao recusados. No gov.br, o destino
fica em cookie HttpOnly temporario e e revalidado no callback, mantendo state,
nonce e demais verificacoes existentes. APIs publicas de publicacoes permanecem
inalteradas; a exigencia de sessao abrange a interface do sistema.

Validacao: 230 testes backend e 41 contratos frontend no Docker isolado.
Os testes sessao.smoke.cjs e concessoes-edicao.smoke.cjs verificam navegacao
direta, expiracao durante o uso, retorno seguro e edicao desktop/mobile.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.

## Identidade Visual das Concessoes

Concessoes de acesso reutiliza a identidade visual de Usuarios: a primeira
coluna azul e o icone Visualizar abrem popup com campos de leitura em duas
colunas no desktop e uma no celular, acoes de editar/revogar e fechamento por
Escape. A revogacao exige confirmacao no popup. Criacao e edicao sao paginas
proprias, com pesquisa e selecao do usuario, seus acessos existentes,
multiplos perfis/instrumentos, validacao e retorno para a listagem de origem.

A busca tem filtros em rascunho, Enter/Pesquisar, filtros avancados recolhidos,
Limpar e paginacao no servidor acima e abaixo da tabela. Perfil e instrumento
sao apresentados pelo nome, com escopo em coluna separada, sem UUIDs na lista.
GET /acessos aceita instrumento (nome) e escopo GLOBAL/INSTRUMENTO, alem de
q, papel, usuario_id, limit e offset. O contrato mantem os IDs para mutacoes.
O teste concessoes-crud.smoke.cjs verifica o fluxo e screenshots desktop/mobile.

## Regressao de Sessao e Concessoes

Com a stack isolada ativa (frontend 3001/API 8001), Playwright e Chromium disponiveis,
execute na pasta frontend em PowerShell:

```powershell
$env:BASE_URL = "http://localhost:3001"
$env:API_URL = "http://localhost:8001/api/v1"
$env:THOR_E2E_ISOLATED = "true"
node tests/e2e/sessao.smoke.cjs
node tests/e2e/concessoes-edicao.smoke.cjs
node tests/e2e/concessoes-lote.smoke.cjs
```

Se o Playwright estiver instalado em outro projeto, PLAYWRIGHT_MODULE pode apontar
para a instalacao existente. Capturas desktop/mobile ficam no temporario do sistema.
O teste editorial exige tambem o worker de indexacao e MinIO isolados.
