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
- Metadados, vinculos e auditoria de imagens opcionais, com armazenamento S3.

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

- `POST /api/v1/instrumentos/{id}/buscar`: busca simples com `q`, `page_size` e `cursor`.
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

A busca simples consulta `texto_busca_basico` no MongoDB, respeita
`aparece_busca` na composicao desse texto e pagina por cursor.
Ela nao depende de Meilisearch. Busca avancada e facetas sao internas e
autenticadas; o resumo publico das imagens no indice nao publica registros.

Estados atuais: instrumentos RASCUNHO/PUBLICADO/ARQUIVADO; registros
ATIVO/INATIVO/EXCLUIDO. Workflow editorial e RBAC geral estao planejados
para a fase 4, nao sao garantidos apenas por esses metadados.

Se o indice Meilisearch de um instrumento ainda nao existir, a busca avancada retorna resultado vazio com `indice_defasado=true`, e facetas retornam `{}`. Isso evita erro 500 durante selecao de instrumentos ainda nao reindexados.

Para reindexacao em lote via CLI:

```bash
docker compose exec backend python -m app.scripts.reindexar_instrumentos
```

## Testes Funcionais

Use a preparacao de [Testes Isolados](#testes-isolados) antes de executar
`python -m pytest app/tests` ou `app/tests/functional` em container.
Nao execute essas suites no banco operacional.

Para gerar JUnit XML e relatorios Markdown/HTML consolidados com o frontend, execute na raiz do projeto:

O script usa o backend em execucao; somente rode em uma stack exclusiva de
testes, nunca na stack que contem cadastros a preservar.

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

## Imagens e Armazenamento

A migration `20261003_000003` cria `imagens_documento`,
`registro_imagens` e `auditoria_imagens`. Registros permanecem no MongoDB;
imagens nao sao obrigatorias. Vinculos usam instrumento/registro explicitamente
e permitem compartilhamento. A exclusao de imagem vinculada retorna 409.
Excluir registro ou instrumento remove vinculos, nao os objetos compartilhados.
Auditoria preserva identificadores mesmo apos exclusao.

Rotas:

- `GET/POST /api/v1/imagens`: filtros `q`, `tipo`, `direitos`, `limit`, `offset`.
- `GET/PUT/DELETE /api/v1/imagens/{id}`.
- `POST /api/v1/imagens/upload`: multipart com `arquivo`, `titulo`, `direitos_acesso`, `descricao` e `metadados_json`.
- `GET /api/v1/imagens/{id}/conteudo`: original; `thumbnail=true` para miniatura.
- `GET/POST /api/v1/instrumentos/{id}/registros/{registro_id}/imagens`.
- `PATCH /api/v1/instrumentos/{id}/registros/{registro_id}/imagens/reordenar`.
- `PATCH/DELETE /api/v1/instrumentos/{id}/registros/{registro_id}/imagens/{imagem_id}`.

URL/IIIF/repositorio externo aceitam HTTP(S), sem credenciais embutidas.
O upload exige MIME real JPEG/PNG/TIFF/WebP, limite padrao de 20 MiB,
gera miniatura JPEG e registra SHA-256 e dimensoes. Falhas antes da
persistencia removem os objetos ja enviados, quando o storage esta disponivel.

Configuracao:

- `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_REGION`.
- `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_FORCE_PATH_STYLE`.
- `UPLOAD_MAX_BYTES`, `UPLOAD_ALLOWED_MIME_TYPES` (lista JSON).
- `S3_URL_EXPIRATION`: 300 segundos por padrao, entre 1 e 3600.

`ArmazenamentoS3` oferece salvar, obter, excluir, checksum e URL assinada.
A interface atual usa streaming mediado/autorizado pelo backend, nao URLs
assinadas persistidas. Buckets devem ser privados; uploads finais nao dependem
do filesystem do container. Instrucoes para o MinIO opcional estao no README raiz.

Metadados exigem sessao; mutacoes da imagem exigem seu criador.
Conteudo PUBLICO admite acesso anonimo, INTERNO exige sessao e RESTRITO exige
o criador. Os direitos do provedor continuam valendo para referencias externas.
Nao ha novo mecanismo de RBAC nesta fase.

Resumos de imagens usam uma consulta SQL por lote de registros.
O indice Meilisearch persiste somente o resumo publico; a busca autenticada
enriquece resultados com imagens acessiveis ao usuario.
Upload/cadastro e vinculos nao dependem de Redis para persistir.
Quando a fila falhar, uma reindexacao reconstroi a projecao.

### Testes Isolados

Os testes funcionais limpam tabelas e colecoes. Use bancos exclusivos de testes,
nunca o banco operacional. Exemplo, executado na raiz `thor_pesquisador`:

```bash
docker compose exec postgres createdb -U thor thor_pesquisador_test
docker compose run --rm --no-deps -e DATABASE_URL=postgresql+psycopg://thor:thor@postgres:5432/thor_pesquisador_test -e MONGODB_DATABASE=thor_pesquisador_test backend alembic upgrade head
docker compose run --rm --no-deps -v ./backend:/app:ro -e DATABASE_URL=postgresql+psycopg://thor:thor@postgres:5432/thor_pesquisador_test -e MONGODB_DATABASE=thor_pesquisador_test -e INDEXACAO_QUEUE_NAME=thor_pesquisador:test backend python -m pytest app/tests -p no:cacheprovider
```

Crie o banco apenas na primeira execucao. A montagem somente leitura mantem
os testes atuais disponiveis sem gerar caches no checkout.
Cobertura da fase 3: schemas, upload/MIME, compensacao de falhas, permissoes,
CRUD, vinculos compartilhados, capa, ordem, auditoria e resumo em lote.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
