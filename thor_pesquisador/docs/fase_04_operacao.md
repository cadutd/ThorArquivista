# Fase 4: Operacao Editorial

Implementada em 2026-10-11, exclusivamente no Thor Pesquisador. Fases 5 e 6
continuam pendentes: exportacoes, retencao ampla e consolidacao operacional.

## Estados e Permissoes

Estado editorial e separado de ATIVO/INATIVO/EXCLUIDO dos registros.

| Comando | Origem | Destino | Permissao |
| --- | --- | --- | --- |
| enviar-revisao | RASCUNHO | EM_REVISAO | enviar_revisao |
| aprovar | EM_REVISAO | APROVADO | revisar |
| devolver | EM_REVISAO, APROVADO | RASCUNHO | revisar |
| publicar | APROVADO | PUBLICADO | publicar |
| arquivar | RASCUNHO, EM_REVISAO, APROVADO, PUBLICADO | ARQUIVADO | arquivar |
| reabrir | ARQUIVADO | RASCUNHO | registros_editar; instrumentos_editar para instrumento |

Devolver e arquivar exigem justificativa. INATIVO nao pode ser revisado,
aprovado ou publicado; EXCLUIDO nao pode ser reaberto ou republicado.
Edicao invalida a aprovacao e cria rascunho. Republicacao usa o mesmo ciclo
enviar-revisao/aprovar/publicar, com nova versao, sem sobrescrever snapshots.
PUT generico nao publica instrumentos. Alteracoes de schema/imagens apos
aprovacao invalidam a elegibilidade da versao aprovada.

| Papel | Acoes |
| --- | --- |
| ADMIN | Todas; gerencia acessos e usuarios |
| GESTOR_INSTRUMENTOS | Consulta, instrumentos/campos, registros, envio para revisao, publicacao, arquivamento, imagens e reindexacao |
| EDITOR | Consulta, CRUD de registros, envio para revisao e imagens |
| REVISOR | Consulta, aprovacao e devolucao |
| CONSULTA_INTERNA | Consulta autorizada |
| PUBLICO_AUTENTICADO | Consulta publicada; nao concede acesso interno |

Concessoes podem ser globais ou limitadas a um instrumento; ADMIN e global.
Permissoes sao verificadas nos servicos, inclusive busca, facetas, campos,
reindexacao, imagens e vinculos. O frontend nao substitui essa verificacao.
Desde a migration `20261013_000009`, Consultar/Incluir/Editar/Excluir sao
independentes em cada CRUD, inclusive Usuarios, Perfis e Concessoes. Nenhum
perfil padrao nao administrativo recebeu novas permissoes administrativas.
Consulte a [matriz granular e regras de delegacao](administracao_acessos.md).
Usuarios devem ser cadastrados antes do login gov.br; o CPF vincula a
identidade. Perfis sao atribuidos exclusivamente por Concessoes de acesso;
o cadastro nao concede acesso nem exige perfil global.

## Primeiro Administrador

Em ambiente sem administrador ativo, cadastrar explicitamente antes do
primeiro login gov.br (substituir os dados pelos dados reais do administrador):

```bash
docker compose exec -T backend python -m app.editorial_cli register-admin --nome "NOME COMPLETO" --username administrador --cpf CPF_VALIDO --email EMAIL_VALIDO
```

Depois, o administrador cadastra usuarios em Administracao -> Gestao de
Usuarios e gerencia concessoes pelo botao Perfis e escopos, em pagina propria.
`/acessos` permanece disponivel, com seletores pesquisaveis
e paginados. Remover/alterar a propria concessao ADMIN e bloqueado.
Em desenvolvimento/testes, DEV_ADMIN_ENABLED=true concede ADMIN somente ao
usuario do login local. A configuracao padrao e false; prod/homolog desabilitam
dev-login e habilitam cookie seguro. Nao habilitar o atalho em producao.

## Migrations e Dados Legados

As migrations 20261011_000004, 000005 e 000006 seguem o head da fase 3.
Criam papeis, acessos, controle editorial, historico, publicacoes, hash de
aprovacao e referencias relacionais de galeria publicada. Nao copiam binarios,
nao concedem papeis a usuarios existentes e nao publicam dados automaticamente.
Snapshots de registros usam `registro_snapshots` no MongoDB.

Aplicar Alembic antes do rollout; no Compose local, o backend aplica ao iniciar:

```bash
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend python -m app.editorial_cli backfill --limit 100
docker compose exec -T backend python -m app.editorial_cli backfill --limit 100 --after ULTIMO_CURSOR
```

Registrar o ultimo_cursor retornado e repetir ate retornar None. Limite maximo
1000. O comando e repetivel, preserva IDs, conteudo e estados operacionais,
e cria controle RASCUNHO para registros legados. PUBLICADO legado sem
publicacao/schema validos nao libera acesso anonimo; requer revisao e publicacao.
Dashboard usa os controles SQL; executar o backfill para contabilizar legados.
Reconciliacao preserva revogacoes INATIVO/EXCLUIDO ja confirmadas no PostgreSQL.

Se houver registros sem instrumento, o backfill geral para com erro, sem
apagamento. Investigar sua origem. Para completar instrumentos validos sem
reassociar orfaos, usar `backfill --instrumento-id UUID --limit 100` e repetir
com --after no mesmo escopo. Na base local foram encontrados sete registros
orfaos preexistentes; foram preservados e nao ficaram elegiveis para publicacao.

Para snapshots criados em uma instalacao intermediaria desta fase, executar
`backfill-public-images` em lotes ate referencias_recuperadas=0. Conferir
pendentes_no_lote; referencias nao encontradas exigem investigacao, nao liberacao.

## Consistencia e Recuperacao

PostgreSQL e canonico para permissao, estado, versao, publicacao e historico.
MongoDB e canonico para conteudo dinamico e snapshots imutaveis. Nao existe
transacao atomica entre bancos. Publicacao grava snapshot antes de confirmar
ponteiro SQL/historico/referencias. Snapshot orfao nao e divulgado.

Comandos exigem UUID operacao_id e versao esperada. Repetir um comando com
os mesmos parametros retorna o resultado confirmado; reutilizar o identificador
com outros parametros ou atuar sobre versao concorrente retorna 409.
O hash de aprovacao inclui dados, schema e apresentacao da galeria.

Edicao de registro confirma intencao SQL/versao/revogacao antes do CAS MongoDB.
Falha de escrita MongoDB conserva a protecao SQL e impede publicar dados
inconsistentes. Investigar a causa e usar o backfill para reconciliar revisoes,
sem reduzir versao. Historico distingue iniciar_edicao de concluir_edicao.
Nao alterar snapshots manualmente nem apagar historia para resolver conflitos.

Editar PUBLICADO preserva a ultima versao publica ate nova aprovacao/publicacao.
Arquivar, excluir, inativar ou restringir acesso revoga imediatamente. Exclusao
fisica de instrumento com publicacao/historico editorial e bloqueada; rascunhos
descartaveis continuam removiveis quando seguros. Imagens publicadas nao podem
ser fisicamente apagadas enquanto houver referencias historicas.

## Consulta e Projecao Publica

Desde o refinamento de 2026-10-15, a tela `/consulta` exige sessao ativa
via SessionGuard, assim como as demais telas; apenas `/login` fica aberta.
Dashboard permanece a entrada autenticada padrao, preservando retorno next.
As APIs `/api/v1/publico` continuam abertas para conteudo publicado elegivel;
essa regra da API nao torna a tela consultiva anonima.
O portal exige instrumento PUBLICO, publicacao/schema validos, registro ATIVO
e snapshot vigente nao arquivado. Dados internos e rascunhos nunca alimentam
a projecao publica. exibir_publico e false por padrao; aparece_busca/listagem
nao sao autorizacao para divulgar.

Campos visiveis sao a intersecao do schema do snapshot, do schema publicado
vigente e das restricoes atuais. Desmarcar exibir_publico revoga imediatamente;
reabilitar exige politica publicada compativel. Galeria e paginada no SQL,
com legenda/ordem/principal do snapshot e direitos da imagem reavaliados.
Imagem isolada PUBLICO continua anonima pela regra da fase 3; isso nao publica
o registro vinculado. RESTRITO exige criador ou ADMIN; INTERNO exige autoria
ou consulta autorizada. Mutacoes exigem permissao explicita e autoria, salvo ADMIN.

Indice publico usa `publico_UUID_geracao`, separado do indice interno.
IndexacaoJob PUBLICACAO e duravel no SQL; index_worker processa lotes/checkpoints,
mesmo sem Redis. SQL/Mongo confirmados nao dependem de Meilisearch.
Busca/facetas retornam 503 enquanto geracao_publica != geracao_indexada, sem
totais/facetas antigos. Recursos nao divulgaveis retornam 404 uniforme.

Investigar erro do job e disponibilidade de Meilisearch; apos corrigir:

```bash
docker compose exec -T backend python -m app.editorial_cli retry-public-index
```

O comando reagenda jobs FALHOU preservando checkpoint. O worker confirma a
geracao somente apos concluir tarefas do Meilisearch e verificar concorrencia.
Geracoes antigas nao sao expostas, mas ainda nao possuem coleta automatica:
monitorar armazenamento e estabelecer politica de limpeza operacional.

## Testes Isolados

`docker-compose.test.yml` possui bancos, Redis, indice e bucket independentes,
sem reutilizar volumes operacionais. Testes funcionais limpam seu proprio banco.

```bash
docker compose -f docker-compose.test.yml up -d --build backend storage_init
docker compose -f docker-compose.test.yml --profile e2e stop index_worker
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests
docker compose -f docker-compose.test.yml --profile checks run --rm contracts
docker compose -f docker-compose.test.yml --profile e2e up -d --build frontend index_worker
```

O worker deve ficar parado durante pytest e ativo para os e2e. Frontend de
testes: localhost:3001; API: localhost:8001/api/v1. Os scripts usam Chromium
Playwright disponivel, BASE_URL/API_URL dessas portas e THOR_E2E_ISOLATED=true
para editorial.smoke.cjs. PLAYWRIGHT_MODULE permite indicar instalacao existente.
Nao executar esses fluxos de limpeza contra a stack operacional.
O script PowerShell run-tests-with-reports.ps1 usa essa compose isolada e gera
JUnit/Markdown/HTML, deixando o worker de testes parado.

Validacao inicial da fase 4 (2026-10-11, registro historico):

- 90 testes backend aprovados, incluindo matriz editorial, papeis/escopos,
  bypass por PUT, concorrencia, snapshots, revogacao, falhas e retomada.
- 17 contratos frontend aprovados, incluindo comparacao visual de CSS.
  O relatorio da compose isolada registra 16 aprovados e uma comparacao de
  CSS ignorada por nao montar o outro projeto; com montagem somente leitura
  da folha de estilo do Gestor, os 17 passaram.
- Build Docker backend/index_worker/frontend e TypeScript aprovados.
- E2e editorial: revisao, publicacao, historico, versoes, consulta anonima,
  galeria real, rascunho, republicacao, revogacao e desktop/mobile aprovados.
- E2e busca: Buscar/Enter, cursor filtrado, vazio e limpar aprovados.
- E2e imagens: upload S3 real, protecao, galeria e compartilhamento aprovados.
- Kustomize base/dev/homolog/prod renderizados; rollout OKD nao testado,
  pois nao ha cluster disponibilizado para esta validacao.

Os refinamentos de administracao/sessao foram validados posteriormente com
230 testes backend, 41 contratos frontend e os fluxos descritos nos READMEs
atuais. Os prompts das fases 5 e 6 partem dessa base revisada em 2026-10-15;
essa revisao documental nao implementa as proximas fases.

Avisos da validacao inicial: dependencias frontend existentes reportaram 9 vulnerabilidades
npm (2 low, 1 moderate, 6 high); atualizacao de dependencias exige revisao propria.
Os testes emitem avisos de deprecacao FastAPI/anyio existentes. Esta validacao
nao equivale a certificacao de seguranca ou desempenho em producao.
Producao exige segredos reais, gov.br configurado, S3 institucional privado,
backup coordenado SQL/Mongo/S3 e verificacao de rollout.
