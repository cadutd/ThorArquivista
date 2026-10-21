# Importacao Assincrona de Registros

## Acesso e Fluxo

Area interna: Instrumentos -> Registros -> Importacoes. A central segue a
listagem Thor, com filtros, paginacao superior/inferior e acoes com tooltip.
Nova importacao e acompanhamento abrem paginas proprias.

1. Enviar CSV, JSON, JSONL ou NDJSON em partes retomaveis.
2. Aguardar a analise em segundo plano, sem manter a pagina aberta.
3. Associar colunas a campos existentes, ignorar colunas ou definir novos
   campos privados. Nenhum schema ou registro e gravado nessa etapa.
4. Validar integralmente em segundo plano. Conferir previa e baixar erros CSV.
5. Confirmar apenas quando todos os registros forem validos.
6. Acompanhar progresso, velocidade, estimativa e resultado. Os registros
   entram como rascunho; nao ha publicacao automatica.

A analise mostra ate tres amostras por coluna. A previa mostra cinco registros
e a tela limita a exibicao a 100 erros; o download inclui todos os erros
registrados. O numero de linha e o ordinal do registro, sem o cabecalho CSV,
nao necessariamente a linha fisica de um arquivo com quebras entre aspas.
Conversoes e estrutura JSON seguem [os formatos existentes](importacao_registros.md).

Depois de concluido o envio, fechar o navegador nao interrompe o trabalho.
Se o envio for interrompido, selecionar o arquivo original no mesmo navegador
retoma as partes confirmadas. A tela de detalhes tambem permite selecionar o
arquivo original. O navegador guarda somente identificadores e metadados de
retomada, nunca o conteudo completo. Partes divergentes sao recusadas.

## Estados e Recuperacao

Fluxo normal:

```text
RECEBENDO -> ANALISANDO -> AGUARDANDO_MAPA -> VALIDANDO
-> AGUARDANDO_CONFIRMACAO -> PENDENTE -> IMPORTANDO -> CONCLUIDA
```

ERROS_VALIDACAO permite corrigir o mapeamento e validar novamente; alterar o
arquivo exige outra importacao. FALHOU e PAUSADA permitem retomar a fase
interrompida, apos resolver a causa. Mudancas de schema exigem reconciliacao,
e permissoes revogadas precisam ser restabelecidas por pessoa autorizada.
Cancelar e terminal: preserva os lotes ja confirmados e nao oferece retomada.
EXPIRADA preserva o historico, mas exige nova operacao para reenviar o arquivo.

Workers usam lease e checkpoints persistidos em PostgreSQL. Uma queda permite
que outro worker continue apos a expiracao do lease. IDs deterministicos e
upserts insert-only impedem duplicacao da mesma operacao e nao sobrescrevem
edicoes posteriores. Registros expurgados nao sao recriados na retomada.
Nao existe transacao distribuida SQL/Mongo/S3; a recuperacao foi implementada
explicitamente para os intervalos entre gravacao e confirmacao do lote.

A criacao de novos campos e transacional no SQL antes da fila de importacao.
Cancelar depois dessa confirmacao nao desfaz o schema nem os registros.
Uma nova operacao intencional sobre o mesmo arquivo pode criar novos registros.

## Limites e Armazenamento

Valores padrao configuraveis no backend e no worker:

| Variavel de ambiente | Padrao |
| --- | --- |
| importacao_max_bytes | 2147483648 (2 GiB) |
| importacao_max_registros | 1000000 |
| importacao_chunk_bytes | 8388608 (8 MiB) |
| importacao_batch_size | 1000 |
| importacao_batch_bytes | 8388608 (8 MiB) |
| importacao_retencao_dias | 7 |

O parser aceita ate 100 colunas e 1 MiB por registro. Os lotes respeitam tanto
o numero de linhas quanto o limite de bytes, sem carregar o arquivo completo
em memoria. Na analise/validacao a fonte e reconstruida em arquivo temporario
local, com leitura streaming. Prever disco temporario para o maior arquivo.

O original em partes, os lotes normalizados e os erros ficam no S3 privado,
com checksums SHA-256. Expiram sete dias apos a criacao; o worker remove o
prefixo privado e mantem os metadados de historico/auditoria. Nao sao publicados
URLs nem chaves S3. Nao aplicar outra regra de lifecycle mais curta ao prefixo
importacoes-assincronas/. Backups e politicas institucionais devem considerar
que fontes e relatorios podem conter dados pessoais.

Ha limite de cinco operacoes nao concluidas por usuario, incluindo esperas,
pausas e falhas. Cancelar uma operacao libera a cota, mas seus arquivos
permanecem sujeitos a expiracao. Capacidade de S3 deve incluir fontes, dados
normalizados e erros, nao apenas o tamanho original.

## Seguranca e Indexacao

Reutiliza registros_incluir e instrumentos_consultar no instrumento;
campos_incluir e obrigatoria para criar campos. Usuario deve estar ativo.
Proprietario, escopo, schema e permissoes sao conferidos nas requisicoes e
novamente no worker. Cada usuario acompanha somente suas importacoes.
Nao ha novos perfis nem ampliacao automatica de concessoes.

Importacoes simultaneas no mesmo instrumento sao serializadas por advisory
lock PostgreSQL, inclusive em relacao ao importador sincrono legado.
Cada registro gera auditoria por insercao em lote, sem uma chamada SQL por
registro. Uma unica reindexacao derivada e agendada ao concluir; nao sao
enviadas centenas de milhares de mensagens ao Redis. O worker de indexacao
recupera jobs pendentes com mais de 30 segundos se o aviso Redis for perdido.
A indexacao e eventual e nao altera o estado editorial.

## Implantacao

Prefixo REST: /api/v1/instrumentos/{id}/registros/importacoes/assincronas.
Todas as rotas exigem sessao e escopo do instrumento:

- GET /limites e GET no prefixo com limit/offset/q/status.
- POST no prefixo: operacao_id UUID, nome_arquivo e tamanho_bytes.
- GET /{job_id}: progresso e metadados, mesmo depois da expiracao dos arquivos.
- POST /{job_id}/partes?numero=1: multipart arquivo, partes em ordem,
  numeracao iniciada em 1 e tamanho exato do bloco, salvo a ultima parte.
- POST /{job_id}/finalizar: enfileira a analise apos o upload completo.
- POST /{job_id}/validar: operacao_id, schema_version e mapeamentos
  no mesmo formato do importador legado.
- POST /{job_id}/confirmar, /cancelar e /retomar: comandos por estado.
- GET /{job_id}/erros: CSV privado, com formulas neutralizadas.

Migration aditiva: 20261020_000018, apos 20261019_000017. Fazer backup antes.
O downgrade recusa apagar historico existente. Instrumentos com importacoes
devem ser arquivados em vez de removidos fisicamente.

No Compose, as variaveis IMPORTACAO_MAX_BYTES, IMPORTACAO_MAX_REGISTROS,
IMPORTACAO_CHUNK_BYTES, IMPORTACAO_BATCH_SIZE, IMPORTACAO_BATCH_BYTES e
IMPORTACAO_RETENCAO_DIAS podem ser definidas no ambiente ou em .env.
No OKD, ajustar os mesmos valores no ConfigMap.

```powershell
docker compose exec -T postgres pg_dump -U thor -d thor_pesquisador -Fc -f /tmp/antes_import_async.dump
docker compose build backend frontend import_worker
docker compose run --rm backend alembic upgrade head
docker compose --profile storage up -d minio
docker compose run --rm backend python -m app.scripts.init_storage
docker compose up -d backend frontend import_worker index_worker
```

S3 externo dispensa o MinIO local. Backend e workers precisam da mesma
configuracao PostgreSQL/Mongo/S3 e dos mesmos limites. Sem import_worker os
jobs ficam aguardando; sem index_worker a pesquisa derivada fica pendente.
O arquivo completo nao fica no filesystem da API. O upload usa partes pequenas pelo
endpoint autenticado, evitando exigir corpo HTTP de 2 GiB no proxy.

OKD: deploy/base/import-worker.yaml, uma replica inicialmente. O manifesto
reserva /tmp com emptyDir de 4 GiB e limite de memoria de 512 MiB. Ao elevar
o limite de arquivo, ajustar disco temporario, ephemeral-storage, capacidade
S3, quotas e limites do proxy. Nao houve rollout institucional nesta entrega.

## Testes

Resultado desta entrega: 660 testes backend, 71 contratos frontend e builds
Docker aprovados. importacoes-assincronas.smoke.cjs passou com transporte
simulado e blocos de 8/16 MiB, cobrindo todos os comandos, retomada de envio,
permissoes e polling. importacoes-assincronas-real.smoke.cjs passou com API,
worker e bancos reais, capturas e axe desktop/mobile. O importador sincrono
tambem passou novamente no navegador.

Executar os fluxos de navegador com BASE_URL=http://localhost:3001,
API_URL=http://localhost:8001/api/v1 e THOR_E2E_ISOLATED=true; o fluxo real
requer import_worker e storage_init da stack de testes. AXE_SCRIPT aponta para
o arquivo axe.min.js instalado no ambiente de testes; PLAYWRIGHT_MODULE pode
apontar para o Playwright ja instalado. O fluxo simulado exige
THOR_E2E_MOCK=true e aceita THOR_E2E_CHUNK_BYTES=16777216 para testar 16 MiB.
Nao executar suites funcionais que controlam o worker manualmente enquanto
import_worker ou outros workers automaticos estiverem ligados na stack.

Suites em backend/app/tests incluem parser streaming, bulk SQL/Mongo e
integracao de API/worker/S3, com falhas, leases, cancelamento, escopos,
expiracao e retomada. O importador sincrono continua disponivel em
/instrumentos/{id}/registros/importar, com seus limites legados de 5 MiB/1000
registros; o botao principal agora abre a central assincrona.

Ensaio de volume, exclusivamente na stack isolada:

```powershell
docker compose -f docker-compose.test.yml exec -T backend python -m app.scripts.benchmark_importacao --quantidades 200000 500000
```

O script cria bancos SQL/Mongo descartaveis com identificador exclusivo,
importa dados sinteticos e remove apenas esses bancos e seus objetos S3 ao
final. Mede upload, analise, validacao e gravacao canonica com auditoria.
Indexacao derivada esta fora dessa medicao. Tempos locais nao constituem
garantia de desempenho em producao ou para arquivos mais largos.

Ensaio local aprovado em 2026-10-20 com CSV de uma coluna textual:

| Registros | Analise | Validacao | Gravacao | Total | Pico RSS |
| --- | --- | --- | --- | --- | --- |
| 200000 | 3,66 s | 9,70 s | 173,08 s | 186,87 s | 151,11 MiB |
| 500000 | 5,19 s | 22,35 s | 337,47 s | 365,19 s | 159,68 MiB |

Inclui PostgreSQL, MongoDB e S3 reais em Docker isolado, com auditoria por
registro e conferencia da quantidade canonica. O pico RSS e cumulativo do
processo de ensaio. O banco Mongo descartavel desse script possui o indice
primario _id; a medicao nao inclui o custo dos indices secundarios da
instalacao completa nem carga concorrente. O fluxo real de navegador utiliza
a colecao da aplicacao de testes com os indices normais.
