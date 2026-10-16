# Thor Pesquisador

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

Em 2026-10-16, Auditoria, Exportacoes, Relatorios e Retencao foram agrupados
em Administracao e alinhados a Instrumentos: busca, tabelas, paginacao,
formularios e visualizacao em pagina propria. Os demais CRUDs administrativos
continuam com seus popups. Permissoes globais e por instrumento sao preservadas.
Detalhes, operacao, permissoes e limitacoes em
[Operacao da fase 5](docs/fase_05_operacao.md).
Os numeros de validacao nas secoes historicas abaixo referem-se as respectivas
entregas anteriores, nao ao total atual. A fase 6 permanece planejada.

Sistema web para instrumentos de pesquisa dinamicos, com autenticacao gov.br, dashboard administrativo, registros flexiveis em MongoDB e deploy preparado para Docker Compose e Kubernetes/OKD.

O projeto e independente do `thor_gestor_de_arquivos_digitais`, mas mantem a mesma identidade visual: paleta, shell administrativo, cards, tabelas, login institucional e dashboard como pagina inicial autenticada.

## Estado Atual

- Backend FastAPI com SQLAlchemy, Alembic, PostgreSQL e MongoDB.
- Frontend Next.js, React e TypeScript.
- Login gov.br via OIDC/OAuth2 com fluxo de desenvolvimento local.
- Dashboard inicial em `/dashboard`.
- CRUD de instrumentos alinhado ao padrao Thor CRUD Base, com listagem paginada, busca, detalhes, criacao, edicao e exclusao com confirmacao.
- Configuracao de campos dinamicos por instrumento.
- CRUD/listagem de registros dinamicos persistidos no MongoDB.
- Busca simples baseada em `texto_busca_basico`.
- Busca de registros com termo aplicado e cursor preservados em Carregar mais; Enter submete e campo vazio restaura a listagem.
- Busca avancada com Meilisearch como indice derivado.
- Redis e `index_worker` para eventos de indexacao e reindexacao por instrumento.
- CRUD de imagens por URL, upload S3, IIIF e repositorio externo, com vinculos compartilhados, galeria sob demanda e auditoria.
- Docker Compose funcional.
- Manifests Kustomize iniciais para Kubernetes/OKD.
- Licenca AGPL-3.0, igual ao Thor Gestor.

As fases 1 a 5 estao implementadas. A fase 4 inclui RBAC por instrumento,
revisao editorial, publicacao versionada, historico e consulta de publicacoes em
`/consulta`. `/pesquisa` continua sendo busca interna autorizada por escopo.
Exportacoes, auditoria, relatorios e retencao controlada foram entregues na fase 5.
Consolidacao operacional, portal e refinamentos de desempenho ficam na fase 6.
Consulte [Operacao da fase 4](docs/fase_04_operacao.md) para provisionamento,
migrations, reconciliacao e testes isolados.

## Arquitetura

Administracao agrupa Gestao de Usuarios, Perfis, Permissoes, Concessoes de acesso,
Auditoria, Exportacoes, Relatorios e Retencao, sem Eventos ou Administracao Geral.
Perfis sao cadastraveis e concessoes preservam os escopos por instrumento.
[Operacao administrativa](docs/administracao_acessos.md).

- `backend/`: API FastAPI, migrations Alembic, modelos PostgreSQL, servicos MongoDB e testes.
- `frontend/`: Next.js standalone, `AppShell`, dashboard, login, instrumentos, campos, registros e pesquisa.
- `deploy/`: manifests Kustomize com `base` e overlays `dev`, `homolog` e `prod`.
- `prompts/roadmap/`: prompts por fase para evolucao incremental do sistema.
- `docker-compose.yml`: ambiente local com backend, frontend, index_worker, export_worker, retention_scheduler, PostgreSQL, MongoDB, Redis, Meilisearch e armazenamento MinIO opcional.

PostgreSQL guarda usuarios, sessoes, instrumentos, campos e governanca. MongoDB guarda os registros dinamicos e deve continuar sendo a fonte canonica para conteudo variavel, inclusive em cenarios com milhoes de registros.

Meilisearch guarda apenas uma projecao de busca, eventualmente consistente e reconstituivel por reindexacao. Redis e usado como fila simples para eventos de indexacao processados pelo `index_worker`.

## Ambiente Local

```bash
cd thor_pesquisador
docker compose up --build
```

URLs:

- Frontend: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`
- Consulta publica: `http://localhost:3000/consulta`
- Login: `http://localhost:3000/login`
- Backend health: `http://localhost:8000/api/v1/health`
- Meilisearch: `http://localhost:7700`

Em desenvolvimento, a tela de login oferece `Entrar em desenvolvimento`. Em homologacao/producao, configure gov.br.

## Variaveis Principais

- `DATABASE_URL`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `CORS_ORIGINS`
- `PUBLIC_APP_URL`
- `SESSION_COOKIE_DOMAIN`
- `SESSION_COOKIE_SECURE`
- `APP_SESSION_SECRET`
- `GOVBR_AUTHORIZE_URL`
- `GOVBR_TOKEN_URL`
- `GOVBR_JWKS_URL`
- `GOVBR_CLIENT_ID`
- `GOVBR_CLIENT_SECRET`
- `GOVBR_REDIRECT_URI`
- `REDIS_URL`
- `INDEXACAO_QUEUE_NAME`
- `MEILISEARCH_URL`
- `MEILISEARCH_API_KEY`
- `INDEXACAO_BATCH_SIZE`

## Kubernetes/OKD

Os manifests ficam em `deploy/` e podem ser aplicados com Kustomize:

```bash
oc new-project thor-pesquisador
oc apply -k deploy/overlays/dev
```

Ajuste antes de usar fora do desenvolvimento:

- dominio das Routes;
- `PUBLIC_APP_URL`;
- `GOVBR_REDIRECT_URI`;
- credenciais gov.br;
- credenciais PostgreSQL/MongoDB/Meilisearch;
- Secrets e ConfigMaps por ambiente.

As imagens foram preparadas para rodar sem root e com UID arbitrario. O frontend standalone copia `public/` para preservar assets como `login_pesquisador.png`.

O deploy inclui `index-worker`, Redis e Meilisearch para desenvolvimento/homologacao. Em producao, Redis e Meilisearch podem ser substituidos por servicos externos/gerenciados mantendo as mesmas variaveis.

Convencao de nomes:

- Docker Compose usa `container_name` fixo com prefixo `thor_pesquisador_` e sem sufixo numerico, por exemplo `thor_pesquisador_backend`.
- Kubernetes/OKD usa o prefixo equivalente `thor-pesquisador-`, porque nomes de recursos e containers Kubernetes nao aceitam `_`. Os nomes declarados de Deployments, StatefulSets, Services, Routes e containers nao usam sufixo numerico. Pods gerenciados pelo Kubernetes ainda podem receber sufixos automaticos da propria plataforma.

## Endpoints Principais

- `GET /api/v1/health`
- `GET /api/v1/dashboard`
- `GET /api/v1/auth/govbr/start`
- `GET /api/v1/auth/govbr/callback`
- `POST /api/v1/auth/dev-login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET/POST /api/v1/instrumentos`
- `GET/PUT/DELETE /api/v1/instrumentos/{id}`
- `GET/POST /api/v1/instrumentos/{id}/campos`
- `PUT/DELETE /api/v1/instrumentos/{id}/campos/{campo_id}`
- `GET/POST /api/v1/instrumentos/{id}/registros`
- `GET/PUT/DELETE /api/v1/instrumentos/{id}/registros/{registro_id}`
- `POST /api/v1/instrumentos/{id}/buscar`
- `POST /api/v1/instrumentos/{id}/buscar-avancado`
- `GET /api/v1/instrumentos/{id}/facetas`
- `POST /api/v1/instrumentos/{id}/reindexar`

## Testes

Para backend, prepare bancos PostgreSQL/MongoDB exclusivos de testes e execute
os comandos de [Testes Isolados](backend/README.md#testes-isolados).
Nao rode a suite funcional contra os cadastros operacionais: ela limpa dados.
Contratos frontend podem ser executados em container, na raiz deste projeto:

```bash
docker run --rm -v ./frontend:/app:ro -w /app node:22-alpine sh -c "node --test tests/functional/*.test.mjs"
```

Build isolado do frontend:

```bash
docker compose build frontend
```

## Como Carregar as Massas de Teste

As massas de teste ficam em scripts idempotentes no pacote `backend/app/scripts/`. Execute com a stack Docker ativa:

```bash
docker compose up -d
docker compose exec backend alembic -c alembic.ini upgrade head
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

A massa cria:

- instrumentos de pesquisa em diferentes tipos, status e visibilidades;
- campos dinamicos cobrindo texto, numero, data, booleano, listas e URL;
- registros dinamicos no MongoDB, com `texto_busca_basico` e IDs deterministicos para execucao repetida.

## Busca Avancada e Indexacao

Registros continuam canonicos no MongoDB. Ao criar, atualizar ou excluir logicamente um registro, o backend publica um evento em Redis. O `index_worker` processa a fila e atualiza o indice Meilisearch `instrumento_{instrumento_id}`.

Quando um instrumento ainda nao possui indice no Meilisearch, a busca avancada retorna lista vazia com `indice_defasado=true` e as facetas retornam `{}`. Assim a tela de pesquisa continua funcional antes da primeira reindexacao.

Para reindexar manualmente um instrumento:

```bash
curl -X POST http://localhost:8000/api/v1/instrumentos/{id}/reindexar
```

Para enfileirar a reindexacao dos instrumentos publicados pela linha de comando:

```bash
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

O endpoint cria um job em PostgreSQL com status, total estimado, processados, checkpoint e erro. O dashboard mostra jobs recentes e falhas.

## Padrao CRUD Thor

O CRUD principal de instrumentos segue o padrao `thor-crud-base`:

- API REST com listar, obter, criar, atualizar e excluir;
- paginacao no servidor por `limit` e `offset`;
- busca simples por `q` aplicada no backend;
- paginas completas no frontend para criar e editar;
- rota de detalhes somente leitura;
- formulario reutilizavel com campos obrigatorios e estado de salvamento;
- exclusao com confirmacao explicita;
- exclusao fisica apenas de rascunhos descartaveis; publicacoes/historico editorial bloqueiam a remocao e exigem arquivamento;
- ao excluir um rascunho permitido, os registros dinamicos vinculados sao removidos do MongoDB.

## Testes Funcionais com Relatorio

O projeto segue a estrutura do Thor Gestor:

- testes backend em `backend/app/tests/functional`;
- teste funcional de contrato frontend em `frontend/tests/functional`;
- relatorios em `test-reports/`.

O script abaixo inicia `docker-compose.test.yml`, com bancos, fila e bucket
exclusivos de testes. Ele nao utiliza o banco da stack operacional e suspende
o worker de testes durante pytest:

```powershell
.\scripts\run-tests-with-reports.ps1
```

Arquivos gerados:

- `test-reports/backend/junit.xml`
- `test-reports/frontend/junit.xml`
- `test-reports/summary.md`
- `test-reports/summary.html`

## Roadmap

Os prompts em `prompts/roadmap/` orientam a evolucao:

- Fase 1: MVP base com gov.br, instrumentos, registros, MongoDB e dashboard.
- Fase 2: busca avancada com Meilisearch, Redis, worker, facetas e reindexacao. Implementada.
- Fase 3: imagens opcionais por URL, upload, IIIF e object storage. Implementada.
- Fase 4: RBAC por escopo, revisao, publicacao versionada e consulta publica inicial, preservando ATIVO/INATIVO/EXCLUIDO como estados operacionais de registros. Implementada.
- Fase 5: auditoria de imagens/editorial sem duplicacao, exportacoes recuperaveis, logs, relatorios e retencao controlada. Implementada.
- Fase 6 (planejada; depende da 4 e 5): refinar portal e consolidar acessibilidade, seguranca, desempenho, observabilidade, backup/restore e operacao OKD.

O prompt da fase 4 registra sua base historica de 2026-10-11. Os prompts das
fases 5 e 6 foram harmonizados em 2026-10-15 com a fase 4 e os refinamentos
de usuarios, concessoes em lote, permissoes granulares e sessao ja entregues.
A fase 5 foi executada sobre essa base. A fase 6 continua planejada.

Ambos exigem preservar identidade visual e comportamento em TODA funcionalidade
nova ou alterada: AppShell/tema, paginas de criacao/edicao, popups administrativos,
links azuis, acoes com icones/tooltips, CrudPagination, buscas Enter/Limpar,
lookups sob demanda, SessionGuard e autorizacao real na API. A entrega exige
comparacao com os modulos de referencia e testes desktop/mobile.

## Busca de Registros

Na listagem de registros, digite o termo e envie por Buscar ou Enter.
A busca considera campos marcados com `aparece_busca`; novas buscas reiniciam
o cursor e Carregar mais preserva o termo enviado, mesmo se o texto for editado
sem novo envio. O estado de carregamento e explicito e respostas antigas sao
ignoradas para evitar sobrescrever resultados.

Campo vazio restaura a listagem geral; o botao nao abre um dialog de filtros.
Se o instrumento tem apenas um registro, a tabela pode permanecer igual.
Filtros avancados, facetas e ordenacao estao na rota interna `/pesquisa`.

O teste `npm run test:e2e:registros-busca` cobre clique, Enter, termo aplicado,
cursor filtrado, ausencia de resultados e limpeza da busca com API real.

## Imagens de Documentos (Fase 3)

Imagens sao opcionais: os registros continuam canonicos no MongoDB. PostgreSQL
guarda metadados em `imagens_documento`, vinculos em `registro_imagens` e
historico em `auditoria_imagens`. A migration `20261003_000003` adiciona
essas estruturas sem converter ou remover registros existentes.

O menu Imagens oferece listagem paginada, busca, filtros por referencia/acesso,
criacao, visualizacao, edicao e exclusao. Nos detalhes de um registro, a aba
Imagens carrega os vinculos apenas quando aberta. Permite selecionar imagens
existentes, criar imagens, editar legendas, ordenar e escolher a principal.
Miniaturas sao carregadas primeiro; o original ou manifest IIIF e aberto sob demanda.

Uma imagem pode pertencer a varios registros. A exclusao de uma imagem vinculada
retorna conflito; excluir um registro ou instrumento limpa seus vinculos, preservando
imagens compartilhadas e auditoria. As operacoes de upload, cadastro, alteracao,
vinculo, desvinculo, ordenacao e exclusao registram o usuario autenticado.

### Armazenamento Local

MinIO e opcional. Para habilitar upload no ambiente de desenvolvimento:

```bash
docker compose --profile storage up -d --build
docker compose exec backend python -m app.scripts.init_storage
docker compose exec backend alembic -c alembic.ini upgrade head
```

O inicializador cria um bucket privado e idempotente; nao libera acesso publico
e recusa execucao em producao. MinIO fica em `127.0.0.1:9000` (S3) e
`127.0.0.1:9001` (console), com credenciais locais padrao
`thor-minio` / `thor-minio-dev-only`. Altere-as fora de uma maquina isolada.
O Dockerfile em `deploy/dev/minio/` compila a
[release oficial fixada](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z);
esse componente e apenas para desenvolvimento, nao uma recomendacao de deploy
de uma versao legada em producao.

Para S3 externo, configure `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_REGION`,
`S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` e `S3_FORCE_PATH_STYLE`.
Em OKD, endpoint/bucket ficam no ConfigMap e credenciais no Secret; substitua
os exemplos antes do rollout. Use bucket privado e credenciais com privilegios
minimos de leitura, gravacao e exclusao dos objetos da aplicacao.
Nao ha armazenamento final de uploads no filesystem do pod.

Uploads aceitam JPEG, PNG, TIFF e WebP, por padrao ate 20 MiB
(`UPLOAD_MAX_BYTES`, `UPLOAD_ALLOWED_MIME_TYPES`). O backend confere
o conteudo real, calcula SHA-256, dimensoes e miniatura, e rejeita SVG e
arquivos invalidos. O envio e limitado e processado em memoria.

### Acesso e Indexacao

A fase 4 integra as imagens ao RBAC existente na aplicacao: mutacoes exigem
permissao explicita e autoria, com excecao de ADMIN. `RESTRITO` preserva
a protecao do criador (ou ADMIN); `INTERNO` exige autoria ou consulta
autorizada por escopo. `PUBLICO` continua permitindo conteudo anonimo de
imagem isolada, sem equivaler a publicacao editorial do registro.
O portal apresenta somente campos e referencias de snapshots elegiveis.
Originais e miniaturas de upload passam pelo endpoint autorizado de conteudo,
sem expor chaves S3. Respostas privadas usam `Cache-Control: private, no-store`.
Referencias externas dependem tambem das permissoes e CORS do provedor;
a aplicacao nao torna privada uma URL publica de terceiros.

O indice deriva `possui_imagens`, `total_imagens` e
`imagem_principal_thumbnail`, sem binarios ou URLs S3 temporarias.
A projecao persistida inclui somente imagens publicas; resultados autenticados
sao enriquecidos com as imagens acessiveis ao usuario. A consulta de resumos
e feita em lote, evitando uma consulta por registro. Falhas Redis nao desfazem
o cadastro canonico; reindexe para reparar uma projecao defasada:

```bash
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

### API e Validacao

- `GET/POST /api/v1/imagens`
- `POST /api/v1/imagens/upload` (multipart)
- `GET/PUT/DELETE /api/v1/imagens/{id}`
- `GET /api/v1/imagens/{id}/conteudo?thumbnail=true`
- `GET/POST /api/v1/instrumentos/{id}/registros/{registro_id}/imagens`
- `PATCH /api/v1/instrumentos/{id}/registros/{registro_id}/imagens/reordenar`
- `PATCH/DELETE /api/v1/instrumentos/{id}/registros/{registro_id}/imagens/{imagem_id}`

Testes cobrem validacao, acesso, CRUD, compartilhamento, exclusao bloqueada,
auditoria, ordenacao, upload, compensacao de falhas e indexacao em lote.
Execute a suite backend em bancos PostgreSQL/MongoDB exclusivos de testes:
os testes funcionais limpam dados. Nao aponte a suite para bancos de producao
ou cadastros que deseja preservar.

O teste de navegador `frontend/tests/e2e/imagens.smoke.cjs` usa a API e S3
reais; somente o manifest IIIF externo e simulado. Confira os comandos no
[README frontend](frontend/README.md).

Os builds recentes reportaram alertas de dependencias npm. Eles continuam
pendentes de revisao; nao foi aplicado `npm audit fix --force`.

## Cadastro de Usuarios

Administracao -> Gestao de Usuarios oferece cadastro, filtros e paginacao no
padrao do Gestor. A primeira coluna e o botao Visualizar abrem um popup;
criacao e edicao usam paginas proprias. O formulario inclui nome, usuario,
CPF, e-mail, ativo e observacoes.

Todo acesso gov.br exige usuario local previamente cadastrado e ativo.
O CPF validado e unico vincula a identidade autenticada; o login nao cria
usuarios nem sobrescreve nome/e-mail administrativos. Desativacao e exclusao
logica revogam sessoes, preservando identidades e historico.

A migration `20261012_000008` preserva IDs e concessoes existentes. Cadastros
legados sem CPF valido ou com duplicidade ficam inativos para regularizacao.
Consulte [Administracao de Acessos](docs/administracao_acessos.md), incluindo
o cadastro inicial de administrador antes do primeiro login institucional.

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
[Administracao de Acessos](docs/administracao_acessos.md).

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
Consulte [Massa de testes de acessos](docs/massa_teste_acessos.md).
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

Este software usa a GNU Affero General Public License v3.0 ou posterior, a mesma licenca do `thor_gestor_de_arquivos_digitais`.

Consulte `LICENSE` e `NOTICE.md`.
