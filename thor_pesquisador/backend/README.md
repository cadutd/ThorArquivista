# Backend

API do `thor_pesquisador`, implementada com FastAPI.

## Responsabilidades

- Autenticacao gov.br e sessao local da aplicacao.
- Usuarios e sessoes.
- Instrumentos e campos dinamicos em PostgreSQL.
- Registros dinamicos em MongoDB.
- Dashboard administrativo.
- Busca avancada com indice derivado em Meilisearch.
- Jobs de reindexacao e fila Redis para worker.
- Validacao dos registros conforme schema do instrumento.
- CRUD REST de instrumentos, campos e registros dinamicos com paginacao, validacao e erros consistentes.
- Health check publico.

## Banco de Dados

PostgreSQL e usado para dados governados e relacionais:

- usuarios;
- sessoes;
- instrumentos;
- campos;
- metadados administrativos.

MongoDB e usado como fonte canonica dos registros dinamicos. Consultas operacionais devem usar indices e paginacao por cursor sempre que possivel.

Meilisearch e usado apenas como projecao de busca avancada e facetas. Redis transporta eventos para o worker `python -m app.worker`.

Ao excluir um instrumento, o backend tambem remove os registros dinamicos vinculados no MongoDB para evitar documentos orfaos.

## Comandos

Com o Docker Compose ativo:

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
docker compose exec backend python -m pytest app/tests
```

Health:

```bash
curl http://localhost:8000/api/v1/health
```

Principais rotas CRUD:

- `GET/POST /api/v1/instrumentos`
- `GET/PUT/DELETE /api/v1/instrumentos/{id}`
- `GET/POST /api/v1/instrumentos/{id}/campos`
- `PUT/DELETE /api/v1/instrumentos/{id}/campos/{campo_id}`
- `GET/POST /api/v1/instrumentos/{id}/registros`
- `GET/PUT/DELETE /api/v1/instrumentos/{id}/registros/{registro_id}`

## Massas de Teste

Os scripts ficam em `app/scripts/` e sao idempotentes:

```bash
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

A carga cria instrumentos e campos no PostgreSQL, registros dinamicos no MongoDB e pode enfileirar a reindexacao dos instrumentos publicados no Meilisearch.

## Busca e Reindexacao

Endpoints:

- `POST /api/v1/instrumentos/{id}/buscar-avancado`
- `GET /api/v1/instrumentos/{id}/facetas`
- `POST /api/v1/instrumentos/{id}/reindexar`

Variaveis:

- `REDIS_URL`
- `INDEXACAO_QUEUE_NAME`
- `MEILISEARCH_URL`
- `MEILISEARCH_API_KEY`
- `INDEXACAO_BATCH_SIZE`

O worker e stateless. Progresso e falhas ficam em `indexacao_jobs`.

Se o indice Meilisearch de um instrumento ainda nao existir, a busca avancada retorna resultado vazio com `indice_defasado=true`, e facetas retornam `{}`. Isso evita erro 500 durante selecao de instrumentos ainda nao reindexados.

Para reindexacao em lote via CLI:

```bash
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

## Testes Funcionais

```bash
docker compose exec backend python -m pytest app/tests/functional
```

Para gerar JUnit XML e relatorios Markdown/HTML consolidados com o frontend, execute na raiz do projeto:

```powershell
.\scripts\run-tests-with-reports.ps1
```

## Variaveis

- `DATABASE_URL`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `APP_SESSION_SECRET`
- `CORS_ORIGINS`
- `PUBLIC_APP_URL`
- `SESSION_COOKIE_DOMAIN`
- `SESSION_COOKIE_SECURE`
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

O backend deve rodar sem root, com configuracao por Secret/ConfigMap e sem depender de escrita persistente no filesystem do container. As migrations Alembic devem ser executadas de forma controlada antes do rollout ou por procedimento operacional documentado.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
