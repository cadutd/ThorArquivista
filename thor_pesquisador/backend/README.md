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

Instrumentos com publicacao ou historico editorial nao podem ser excluidos
fisicamente. Para rascunhos descartaveis, a exclusao permitida tambem remove
os registros vinculados no MongoDB, preservando imagens e auditoria.

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

Instrumentos e controle editorial de registros usam RASCUNHO, EM_REVISAO,
APROVADO, PUBLICADO e ARQUIVADO. Registros preservam separadamente os
estados operacionais ATIVO/INATIVO/EXCLUIDO. RBAC e workflow sao aplicados
pelos servicos, sem permitir publicacao pelo PUT generico.

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

Metadados privados exigem autoria ou consulta autorizada por escopo.
Mutacoes exigem permissao explicita e autoria, salvo ADMIN. Conteudo PUBLICO
admite acesso anonimo; INTERNO exige autoria ou consulta autorizada;
RESTRITO exige criador ou ADMIN. Direitos externos continuam valendo.
Publicacao editorial usa snapshots e reavalia os direitos atuais das imagens.

Resumos de imagens usam uma consulta SQL por lote de registros.
O indice Meilisearch persiste somente o resumo publico; a busca autenticada
enriquece resultados com imagens acessiveis ao usuario.
Upload/cadastro e vinculos nao dependem de Redis para persistir.
Quando a fila falhar, uma reindexacao reconstroi a projecao.

### Testes Isolados

Os testes funcionais limpam tabelas e colecoes. A compose de testes possui
PostgreSQL, MongoDB, Redis, Meilisearch e MinIO independentes. Execute na raiz
`thor_pesquisador`; nunca aponte os testes para o ambiente operacional:

```bash
docker compose -f docker-compose.test.yml up -d --build backend storage_init
docker compose -f docker-compose.test.yml stop index_worker
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests
```

O backend aplica migrations ao iniciar. A montagem somente leitura evita caches
no checkout. O worker deve ficar parado durante pytest para nao disputar os
jobs dos testes. A suite exige nomes de bancos terminados em `_test`.
Cobertura: CRUD, imagens/S3, estados editoriais, papeis/escopos, concorrencia,
idempotencia, snapshots, privacidade, falhas entre bancos e retomada de jobs.

## Editorial e Consulta Publica (Fase 4)

Migrations `20261011_000004` a `20261011_000006` acrescentam papeis,
acessos, controle editorial, historico append-only, publicacoes e referencias
de imagens. Nao publicam registros legados nem concedem ADMIN a usuarios gov.br.

Transicoes: POST `/api/v1/instrumentos/{id}/{acao}` e
`/api/v1/instrumentos/{id}/registros/{registro_id}/{acao}`, com
`acao` enviar-revisao/aprovar/devolver/publicar/arquivar/reabrir.
Payload: `operacao_id` UUID, `versao` e justificativa para devolver/arquivar.
As rotas `/editorial/{acao}` sao aliases do mesmo servico.
GET historico/versoes sao paginados e autorizados; `/editorial/fila` consulta
pendencias. `/acessos`, `/usuarios` e `/papeis` atendem a gestao autorizada por operacao.

`/api/v1/publico/instrumentos` oferece catalogo, detalhe, POST buscar,
GET buscar/facetas, registro e galeria paginada sem sessao. A projecao publica
e separada do indice interno. Revogacoes valem imediatamente; busca/facetas
retornam 503 enquanto a geracao atual nao estiver indexada, sem servir dados
antigos. Recursos nao divulgaveis retornam 404.

Consulte [Operacao editorial](../docs/fase_04_operacao.md) para as matrizes,
provisionamento ADMIN, backfill em lotes e recuperacao de falhas.

## Administracao de Acessos

A migration `20261012_000007` evolui os papeis existentes com nome de exibicao,
descricao e situacao. `/perfis` oferece CRUD administrativo; `/permissoes`
e um catalogo somente leitura. Perfis vinculados sao desativados em vez de
apagados, com revogacao imediata na autorizacao e nas consultas por escopo.
ADMIN e protegido. `/usuarios` oferece CRUD local com CPF validado/unico,
username unico, perfil, situacao e observacoes, busca e filtros paginados.
O login gov.br exige cadastro previo ativo e vincula pelo CPF, sem criar
usuarios nem sobrescrever seus dados. CPF ja vinculado nao pode ser alterado.
A exclusao e logica; desativacao/exclusao revogam sessoes imediatamente.

A migration `20261012_000008` torna govbr_sub opcional ate o primeiro login,
adiciona os dados administrativos e identifica a concessao de perfil principal
sem substituir a autorizacao por instrumento. Legados invalidos/duplicados
ficam inativos; valores anteriores sao mantidos em observacoes para revisao.
Em ambiente sem administrador ativo, `python -m app.editorial_cli register-admin`
exige --nome, --username, --cpf e --email para o cadastro inicial explicito.

Consulte [Administracao](../docs/administracao_acessos.md) para rotas e regras.

## Permissoes por Operacao

Os oito CRUDs (instrumentos, campos, registros, imagens, galerias, usuarios,
perfis e concessoes) usam codigos independentes para Consultar, Incluir,
Editar e Excluir, inclusive na administracao. Menus e botoes respeitam esses
codigos; a autorizacao efetiva permanece no backend, com escopos por instrumento
e protecao contra escalada de privilegios na delegacao administrativa.

A migration `20261013_000009` preserva os perfis e acessos atuais e substitui
os agrupamentos antigos por permissoes granulares. O catalogo de Permissoes
permanece somente leitura. Consulte a matriz e as regras de rollback em
[Administracao de Acessos](../docs/administracao_acessos.md).

Validacao: 165 testes backend e 35 contratos frontend, executados no Docker
isolado. O teste `frontend/tests/e2e/permissoes-crud.smoke.cjs` cobre a
interface com usuario nao administrador e verificacoes desktop/mobile.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
