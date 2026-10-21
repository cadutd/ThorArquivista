# Backend

## Atualizacao de 2026-10-20

Head Alembic: 20261020_000018. Importacao assincrona reutiliza validacao,
evolucao de schema, RBAC, Mongo canonico, auditoria e indexacao existentes.
Fila duravel PostgreSQL, lease, checkpoints e import_worker dedicado
processam fontes S3 privadas com parser streaming e lotes bulk.
API em /api/v1/instrumentos/{id}/registros/importacoes/assincronas.

Limites padrao: 2 GiB/1 milhao de registros; lotes de 1000 registros/8 MiB.
Backup antes das migrations; subir import_worker junto aos demais servicos.
Nao ha criacao automatica de perfis, concessoes ou publicacoes.
[Operacao e testes de volume](../docs/importacao_assincrona.md).

Suite completa em Docker: 660 testes aprovados. Ensaios canonicos SQL/Mongo/S3
com 200000 e 500000 registros concluidos, sem usar dados locais. O ambiente
local foi migrado apos backup PostgreSQL, preservando os oito instrumentos e
217 registros existentes. Manifesto OKD adicionado, sem rollout institucional.

## Historico de 2026-10-19

Portal da fase 6 com catalogo publico restrito a metadados publicados,
ranking agregado e configuracao institucional auditada. Registros e imagens
de registros exigem sessao; visitantes gov.br nao recebem cadastros, perfis
ou concessoes automaticamente. A area interna preserva permissoes e escopos.

Consultas de instrumentos aceitam filtros combinados no servidor: Nome, Tipo,
Status, Visibilidade e Descricao internamente; Nome, Tipo e Descricao no catalogo.
Capas opcionais usam S3 privado, validacao de imagem e normalizacao JPEG
960 x 540, com limite de 16 megapixels. Upload nao publica: o acesso anonimo
depende da capa vigente no instrumento e no snapshot publicado.

O CRUD interno consulta registros com total/limit/offset em
POST /api/v1/instrumentos/{id}/registros/consultar, preservando os endpoints
por cursor. Filtros aceitam somente chaves pesquisaveis do instrumento,
com validacao de tipo e permissao registros_consultar por escopo.
A pesquisa do portal continua usando a API e o indice derivados de publicacoes;
nenhuma permissao de escrita foi acrescentada. Esta padronizacao nao exige
nova migration Alembic; o indice MongoDB e garantido na inicializacao.

Importacao CSV/JSON reutiliza os servicos de schema, registros e auditoria,
com previa sem gravacao, validacao de todos os registros e operacao retomavel.
Exige registros_incluir/instrumentos_consultar no escopo; novos campos
exigem campos_incluir. Arquivo original nao e persistido e nao ha publicacao
automatica. [API e limites](../docs/importacao_registros.md).

Head atual: 20261019_000017 (importacoes), apos 000016 (capas) e 000014/000015 (portal).
Fazer backup antes de executar alembic upgrade head. As migrations preservam
cadastros existentes; downgrade de capas com referencias existentes e bloqueado.
O seed de imigracao e exclusivo de desenvolvimento/teste, exige agente
autorizado e publicacao explicita, e permite retomada sem duplicar registros.

Validacao mais recente: 479 testes backend e 62 contratos frontend aprovados
em Docker isolado, builds e fluxos E2E de registros e imagens aprovados.
Importacao: 56 testes focados e fluxo CSV/JSON em navegador aprovados,
incluindo retomada sem duplicacao, permissoes e preservacao de campos privados.
Os fluxos E2E de portal/capas foram aprovados na entrega anterior.
Na revisao da pesquisa publicada, 37 testes de portal/editorial foram
reexecutados; portal-registros.smoke.cjs passou com axe desktop/mobile.
As validacoes institucionais de gov.br e OKD continuam pendentes.

Detalhes: [Instrumentos e portal](../docs/instrumentos_portal.md),
[Massa de imigracao](../docs/massa_teste_imigracoes.md) e
[Operacao da fase 6](../docs/fase_06_operacao.md).

## Historico de 2026-10-16

Cadastro de usuarios separado das concessoes; inclusao e edicao de acessos
compartilham pesquisa e selecao multipla. Permissoes por operacao e escopo sao
validadas no backend. Landing page e catalogo de instrumentos sao anonimos;
registros exigem sessao, inclusive para visitantes gov.br sem cadastro.
A area interna mantem RBAC. A massa dev/test possui 60 usuarios e 24 perfis.

Fase 5 implementada: auditoria unificada e imutavel, exportacoes autenticadas
CSV/JSON/pacote, jobs recuperaveis, relatorios, logs estruturados e politicas
de retencao com simulacao, impedimentos e expurgo autorizado.
Validacao acumulada: 360 testes backend e 47 contratos frontend no Docker isolado.
Na revisao de 2026-10-16, os 47 contratos, a compilacao e quatro fluxos Playwright
(conformidade, administracao, sessao e permissoes CRUD) passaram. A verificacao
incluiu exportacao/download, edicao e simulacao de retencao, desativacao/reativacao
de politica, relatorios, escopos, detalhes dedicados e telas desktop/mobile.
Detalhes, operacao, permissoes e limitacoes em
[Operacao da fase 5](../docs/fase_05_operacao.md).
Auditoria, Exportacoes, Relatorios e Retencao ficam em Administracao e seguem
a identidade de Instrumentos. As APIs preservam os escopos globais/por instrumento,
o historico imutavel e os comandos permitidos em cada estado dos jobs.
Migrations da fase 5: 20261015_000011 a 20261015_000013.
Fase 6: 20261016_000014/000015. Capas opcionais: 20261019_000016.
Importacoes de registros: 20261019_000017 (head atual).
Os numeros de validacao nas secoes historicas abaixo referem-se as respectivas
entregas anteriores, nao ao total atual.

Fase 6 implementada: landing page institucional, catalogo paginado, ranking
agregado e identidade visual publica configuravel em Administracao.
Consulta publicada autenticada nao cria Usuario, perfil ou concessao.
Migrations 20261016_000014/000015 preservam sessoes e historico existentes.
Probes, metricas protegidas, limites HTTP e manifestos OKD foram evoluidos.
Validacao inicial da fase 6: 392 testes backend, 53 contratos frontend e 13 fluxos E2E
passaram; builds e ensaio isolado de backup/restore tambem foram aprovados.
Validacoes locais, operacao, auditoria de dependencias e pendencias institucionais:
[Operacao da fase 6](../docs/fase_06_operacao.md). Nao houve rollout em cluster.

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
- Auditoria unificada e logs estruturados sem dados sensiveis.
- Exportacoes autenticadas e recuperaveis, processadas pelo export_worker.
- Relatorios autorizados e retencao com simulacao, bloqueios e expurgo explicito.

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
- `POST /api/v1/instrumentos/{id}/registros/consultar`: CRUD interno paginado,
  com q, status ATIVO/INATIVO, filtros tipados por chave de metadado,
  limit (1..100) e offset. Retorna items/total/limit/offset; ordenacao
  deterministica por criado_em e id, sem carregar a colecao inteira.
  Somente campos aparece_busca do instrumento sao aceitos. Valores sao
  tratados como dados, nunca como operadores MongoDB. Excluidos ficam fora
  da listagem e as permissoes registros_consultar/escopos sao preservadas.
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
exige sessao e, para visitantes, vinculo com publicacao elegivel;
INTERNO exige autoria ou consulta autorizada;
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
docker compose -f docker-compose.test.yml --profile e2e stop index_worker export_worker retention_scheduler
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests
```

O backend aplica migrations ao iniciar. A montagem somente leitura evita caches
no checkout. Os workers devem ficar parados durante pytest para nao disputar os
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

`/api/v1/publico/instrumentos` oferece catalogo anonimo. Detalhe/schema,
POST/GET buscar, facetas, registro e galeria paginada exigem sessao.
A projecao publica
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
username unico, situacao e observacoes, busca e filtros paginados.
O login gov.br vincula pelo CPF quando existe cadastro ativo; visitantes sem
cadastro recebem somente sessao consultiva, sem Usuario/perfil/concessao.
Contas inativas/excluidas permanecem bloqueadas. Login nao sobrescreve dados.
CPF ja vinculado nao pode ser alterado.
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

As rotas abertas sao /, /consulta e /login; registros em /consulta/{id}
e /consulta/{id}/{registroId} exigem sessao. A guarda revalida as telas
protegidas ao navegar, retornar a aba/janela e a cada 60 segundos.
401 dos clientes de recursos protegidos, incluindo imagens/upload, inicia login.
O portal usa /auth/estado para consultar sessao opcional sem redirecionamento.
Respostas 403 indicam falta de permissao e nao encerram uma sessao valida.

O parametro next preserva caminho, filtros e fragmento da pagina solicitada.
O login de desenvolvimento e o callback gov.br so aceitam destinos internos;
enderecos externos e retornos para login sao recusados. No gov.br, o destino
fica em cookie HttpOnly temporario e e revalidado no callback, mantendo state,
nonce e demais verificacoes existentes. Desde a fase 6, as APIs de registros
publicados tambem exigem sessao; somente a descoberta de instrumentos e anonima.

Validacao: 230 testes backend e 41 contratos frontend no Docker isolado.
Os testes sessao.smoke.cjs e concessoes-edicao.smoke.cjs verificam navegacao
direta, expiracao durante o uso, retorno seguro e edicao desktop/mobile.

## Massa de Imigracao

app.scripts.seed_imigracoes gera um instrumento publico e, por padrao, 200
registros inteiramente ficticios. Usa campos dinamicos, servicos existentes,
snapshot/publicacao editorial e agente cadastrado com permissoes globais.
Somente dev/test; --publicar e explicito. Preserva edicoes e historico,
reconhece registros mesmo apos alterar seu codigo visivel e impede execucoes
simultaneas. Nenhuma migration ou mudanca de permissao foi necessaria.

Consulte [Massa de testes de imigracao](../docs/massa_teste_imigracoes.md)
para carga, consulta, limites e teste de idempotencia/seguranca.
Validacao em 2026-10-17: nove testes da massa e 401 testes backend na suite
completa passaram; carga local reexecutada sem duplicar ou republicar registros.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
