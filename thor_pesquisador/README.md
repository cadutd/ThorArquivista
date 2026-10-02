# Thor Pesquisador

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
- Busca avancada com Meilisearch como indice derivado.
- Redis e `index_worker` para eventos de indexacao e reindexacao por instrumento.
- Docker Compose funcional.
- Manifests Kustomize iniciais para Kubernetes/OKD.
- Licenca AGPL-3.0, igual ao Thor Gestor.

## Arquitetura

- `backend/`: API FastAPI, migrations Alembic, modelos PostgreSQL, servicos MongoDB e testes.
- `frontend/`: Next.js standalone, `AppShell`, dashboard, login, instrumentos, campos, registros e pesquisa.
- `deploy/`: manifests Kustomize com `base` e overlays `dev`, `homolog` e `prod`.
- `prompts/roadmap/`: prompts por fase para evolucao incremental do sistema.
- `docker-compose.yml`: ambiente local com backend, frontend, worker, PostgreSQL, MongoDB, Redis e Meilisearch.

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

Com os containers ativos:

```bash
docker compose exec backend python -m pytest app/tests
npm --prefix frontend run test:functional
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
- ao excluir um instrumento, os registros dinamicos vinculados sao removidos do MongoDB para evitar documentos orfaos.

## Testes Funcionais com Relatorio

O projeto segue a estrutura do Thor Gestor:

- testes backend em `backend/app/tests/functional`;
- teste funcional de contrato frontend em `frontend/tests/functional`;
- relatorios em `test-reports/`.

Execute:

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
- Fase 3: imagens opcionais por URL, upload, IIIF e object storage.
- Fase 4: publicacao, revisao, versionamento e area consultiva.
- Fase 5: auditoria, exportacao, logs, relatorios e retencao.
- Fase 6: portal consultivo, acessibilidade, desempenho, observabilidade e operacao OKD.

## Licenca

Este software usa a GNU Affero General Public License v3.0 ou posterior, a mesma licenca do `thor_gestor_de_arquivos_digitais`.

Consulte `LICENSE` e `NOTICE.md`.
