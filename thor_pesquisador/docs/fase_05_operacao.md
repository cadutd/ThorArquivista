# Fase 5: Auditoria, Exportacoes e Retencao

Implementacao em 2026-10-15, exclusivamente no Thor Pesquisador. Nao altera o
tema compartilhado, a administracao de acessos ou a politica de sessao da fase 4.
Nao equivale a certificacao de conformidade legal.

Atualizacao da fase 6 (2026-10-16): descoberta de instrumentos e anonima;
registros, busca/facetas e conteudo de imagens exigem sessao, inclusive
para visitante gov.br sem cadastro administrativo. Operacao atual, probes,
metricas, migrations 014/015 e riscos em [Fase 6](fase_06_operacao.md).

## Navegacao

- Auditoria: consulta paginada e pagina de detalhes, sem editar ou excluir eventos.
- Exportacoes: solicitacao em pagina propria, pesquisa paginada, acompanhamento,
  detalhes em pagina propria, download, repeticao, cancelamento e descarte conforme estado.
- Relatorios: instrumentos/estados, registros/situacao e por instrumento,
  publicacoes por periodo, alteracoes autorizadas de usuarios, imagens orfas
  visiveis ao usuario e estados dos jobs. Periodo padrao de 30 dias, maximo 366.
- Retencao: politicas com inclusao, edicao e visualizacao em paginas proprias;
  ativacao/desativacao, simulacao e execucao explicitamente autorizada.
  A categoria e o instrumento tornam-se imutaveis depois de cadastrar a politica.
- No detalhe do registro, operadores autorizados podem bloquear o expurgo ou
  informar a data minima de retencao. Um expurgo iniciado nao pode ser revertido.

Listas usam CrudPagination acima e abaixo da tabela, busca por Enter/botao,
filtros recolhidos e links azuis na primeira coluna; botoes possuem nome
acessivel e tooltip. Pesquisas de instrumentos sao paginadas e sob demanda.
Desde 2026-10-16, Auditoria, Exportacoes, Relatorios e Retencao ficam em
Administracao, inclusive no menu movel. O grupo respeita as permissoes por
instrumento sem liberar a administracao de usuarios/perfis. Essas quatro
funcoes seguem Instrumentos: page-heading, panel/stack, filtros Buscar e
Limpar filtros, formularios em grid e detalhes com Voltar e acoes autorizadas.
Simular/executar uma politica abre o detalhe da execucao gerada.
Relatorios preservam filtros de instrumento/periodo e ocultam resultados
anteriores quando a consulta falha. Confirmacoes destrutivas continuam em dialog.
As telas continuam autenticadas pelo SessionGuard, inclusive /consulta.
Nao foi criado endpoint de exportacao anonima.

## Dados e Auditoria

Migrations novas: 20261015_000011, 20261015_000012 e 20261015_000013, depois de
20261014_000010. Tabelas: auditoria_geral, exportacoes, exportacao_partes,
politicas_retencao, execucoes_retencao e logs_requisicoes. Tambem adicionam
correlacao nos eventos existentes, revisao_dados em instrumentos e impedimentos/
tombstones de expurgo em editorial_registros. Nao renumeram migrations antigas.

A consulta de auditoria combina auditoria_geral, auditoria_imagens e
eventos_editoriais, preservando os IDs, datas e autores originais. Os eventos
de imagens e editoriais nao sao copiados para outro historico. Eventos legados
sem nome de agente continuam com seu usuario_id e aparecem como agente legado.
Triggers impedem UPDATE/DELETE nessas tres tabelas. Um administrador de banco
continua capaz de alterar controles: isto nao substitui backup e governanca.

Instrumentos, campos, usuarios, perfis, concessoes e solicitacoes de reindexacao
usam auditoria na mesma transacao SQL. Concessoes em lote compartilham uma
operacao e geram eventos por concessao. Edicoes e exclusoes de registros
reaproveitam as intencoes/eventos editoriais; criacoes usam intencao e conclusao.
Jobs registram o solicitante e o executor tecnico separadamente. Nomes dos
campos e fatos operacionais sao limitados; CPF, tokens, cookies, senhas e
conteudo completo dos formularios nao entram na auditoria geral.

X-Request-ID aceita UUID valido ou gera um novo UUID, devolvido na resposta.
Logs JSON usam rota parametrizada, metodo, status, duracao e request_id; nao
registram query strings, cabecalhos nem corpo. O access log bruto do Uvicorn
fica desabilitado para nao expor codigos OAuth em callbacks.
LOG_TECNICO_PERSISTIR=true grava os logs tecnicos minimizados no PostgreSQL.
LOG_ACESSO_CONSULTIVO=false por padrao; quando habilitado grava um log consultivo
separado, sem IP, identidade, consulta ou corpo. Cada categoria tem sua retencao.
Falhas na persistencia de log tecnico emitem aviso sanitizado; nao desfazem uma
operacao de dominio ja confirmada. Auditoria de negocio e transacional.

## Permissoes

O catalogo passa a 55 permissoes. ADMIN continua com "*".

| Modulo | Permissoes |
| --- | --- |
| Auditoria | auditoria_consultar |
| Relatorios | relatorios_consultar |
| Exportacoes | exportacoes_consultar, exportacoes_incluir, exportacoes_excluir, exportacoes_repetir |
| Politicas | retencao_consultar, retencao_incluir, retencao_editar, retencao_excluir |
| Execucoes | retencao_simular, retencao_executar, retencao_cancelar |

Consultar nao permite exportar nem expurgar. Exportacao administrativa exige
registros_consultar; publicada exige consulta_publicada e elegibilidade vigente.
Solicitante, usuario ativo, perfil ativo e escopo sao revalidados nos lotes e
downloads. Apenas o solicitante ou ADMIN veem o job de exportacao/retencao.
ADMIN pode administrar outros jobs, mas nao contorna a revogacao do solicitante.
Alteracoes de usuarios em relatorios/auditoria exigem tambem usuarios_consultar;
eventos de perfis/acessos exigem a consulta administrativa correspondente.

A migration adiciona auditoria/relatorios ao REVISOR e auditoria/relatorios/
comandos de exportacao ao GESTOR_INSTRUMENTOS somente quando suas permissoes
ainda correspondem exatamente aos defaults anteriores. Perfis personalizados,
concessoes, origens, IDs e escopos permanecem intactos. Nao concede retencao
automaticamente a perfis comuns. Defaults novos do servico acompanham a migration.

Rollback restaura apenas defaults ainda iguais ao valor aplicado, sem sobrescrever
customizacoes posteriores. 000011 recusa remover tabelas se ja houver auditoria
geral, exportacoes ou execucoes; nesse caso exige plano de preservacao de evidencias.
000012 e 000013 podem ser revertidas sem apagar eventos. Pare workers antes.
Indices transacionais podem bloquear escrita: em bases grandes planeje janela
de manutencao. Nao ha promessa de migration online sem bloqueios.

## Exportacoes

POST /api/v1/instrumentos/{id}/exportacoes recebe operacao_id UUID, formato
CSV|JSON|PACOTE e escopo ADMINISTRATIVO|PUBLICADO. PACOTE exige PUBLICADO.
Repetir a mesma operacao com os mesmos parametros retorna o mesmo job; outros
parametros conflitam. SQL confirma o job mesmo com Redis indisponivel.

GET /api/v1/exportacoes e /{id} consultam; POST /{id}/repetir retoma uma falha
nao expirada; DELETE /{id} cancela pendentes/em processamento ou descarta um
arquivo concluido/falho. Repeticoes da exclusao sao idempotentes e mantem o job.

| Estado | Proximos estados |
| --- | --- |
| PENDENTE | PROCESSANDO, CANCELADA, EXPIRADA |
| PROCESSANDO | CONCLUIDA, FALHOU, CANCELADA, EXPIRADA |
| FALHOU | PENDENTE (repetir), DESCARTADA, EXPIRADA |
| CONCLUIDA | DESCARTADA, EXPIRADA |
| CANCELADA, DESCARTADA, EXPIRADA | terminais |

O export_worker usa PostgreSQL como fila duravel, separado do index_worker e
sem Redis como fonte de verdade. Claim com SKIP LOCKED, token e lease cercam
checkpoint e publicacao. Lease vencida permite retomada; outro token ou
cancelamento impede ressuscitar o job. Falha no armazenamento nao libera parcial.

Mongo e percorrido por chave crescente, sem skip profundo. Lotes sao limitados
por quantidade, com indice composto instrumento_id/_id. O controle SQL dos
registros e validado em lote; nao se varre o historico de auditoria por registro.
O limite aproximado e 8 MiB, mais um documento Mongo; schemas e
referencias sao consultados em lote. Chunks privados no S3 e checkpoints SQL
permitem retomar sem repetir linhas. EXPORTACAO_MAX_REFERENCIAS_LOTE=5000 limita
referencias de imagens por lote; exceder causa falha, nunca truncamento silencioso.
Reduza EXPORTACAO_BATCH_SIZE ou ajuste o limite conforme a memoria disponivel.
O arquivo final e montado via multipart,
sem arquivo final no disco do pod. Multipart em andamento e abortado em falha
capturada; quedas abruptas deixam uploads temporarios para a limpeza por prefixo.
O tamanho de parte e 8 MiB; o limite S3 de 10.000 partes limita o tamanho pratico
do arquivo final a aproximadamente 78 GiB. Acima disso o job falha; particione
o conjunto antes de solicitar esse volume.

JSON inclui manifesto, schema e registros; preserva numeros, booleanos e listas.
CSV usa escaping padrao e neutraliza formulas textuais iniciadas por =,+,-,@,
inclusive apos espacos, tab ou quebra de linha. Numeros negativos continuam
numeros. Pacote inclui somente referencias de imagens publicas atuais, nunca
binarios, chaves S3, URIs externas ou URLs assinadas persistentes.

Consistencia e otimista, nao uma transacao distribuida: revisao_dados precisa
continuar igual entre solicitacao, lotes, conclusao e download. Mudancas invalidam
o resultado; solicite outro job. A intencao e a conclusao de criacoes incrementam
a revisao; documentos sem controle ou com versoes SQL/Mongo divergentes impedem
a exportacao e exigem reconciliacao/backfill editorial dos legados.
PUBLICADO usa snapshots e a intersecao do schema publicado
com campos ainda publicos; nao inclui rascunhos nem dados canonicos confidenciais.

GET /api/v1/exportacoes/{id}/download transmite autenticado pelo backend,
revalidando a cada bloco. Arquivos expirados, incompletos, cancelados ou revogados
nao sao liberados; blocos ja recebidos antes de uma revogacao nao sao recuperaveis.
O cliente web usa Blob para salvar; downloads excepcionalmente grandes devem
usar um cliente autenticado com streaming, considerando a memoria do navegador.

## Retencao

Categorias: LOG_TECNICO, ACESSO_CONSULTIVO, EXPORTACAO, SESSAO e REGISTRO_EXCLUIDO.
Nao ha politica destrutiva preinstalada. SESSAO remove somente expiradas anteriores
ao corte; registro excluido exige instrumento, prazo vencido, ausencia de hold,
reter_ate vencido e ausencia de qualquer snapshot/versao publicada historica.
Simulacao e o padrao: conta analisados, elegiveis e bloqueados sem remover dados.
Execucao definitiva exige permitir_expurgo na politica e retencao_executar.

API: /api/v1/retencao/politicas (CRUD com desativacao logica);
POST /politicas/{id}/execucoes; GET /execucoes e /execucoes/{id};
DELETE /execucoes/{id} cancela; POST /execucoes/{id}/repetir retoma FALHOU.
Estados: PENDENTE -> PROCESSANDO -> CONCLUIDA|FALHOU;
PENDENTE/PROCESSANDO -> CANCELADA; FALHOU -> PENDENTE por comando autorizado.
CONCLUIDA/CANCELADA sao terminais. Politica com execucao ativa nao pode ser editada.

O worker coordena intencao SQL, remocao Mongo, desvinculacao SQL e remocao
confirmada no indice interno, com checkpoint apos sucesso. Erro pode deixar uma
intencao de expurgo com Mongo ja removido; repetir conclui os passos restantes.
O tombstone SQL e os eventos sao mantidos. Snapshots e seus vinculos nao sao
expurgados; imagens compartilhadas ou orfas nao sao apagadas automaticamente.
Indices publicos sao protegidos pela ausencia de publicacao do registro excluido;
nao se tenta remover registros de todas as geracoes historicas por varredura.

Exportacoes vencidas sao bloqueadas imediatamente na API e marcadas EXPIRADA
pelo worker. Prefixos expirados/cancelados/descartados sao limpos em lotes,
inclusive multiparts abandonados, mantendo job e auditoria. Uma marca de limpeza
rotativa permite revisitar escrita tardia de worker cancelado. Limpeza vazia
repetida nao duplica eventos. Nao ha exclusao generica de historico de negocio.

## Operacao

Comandos a partir de thor_pesquisador:

```powershell
docker compose --profile storage up -d --build
docker compose exec -T backend python -m app.scripts.init_storage
docker compose logs --tail=80 backend export_worker
docker compose --profile jobs run --rm --no-deps retention_worker
```

Compose inicia retention_scheduler, que consulta a fila e artefatos vencidos
a cada 60 segundos; o worker com profile jobs permite execucao manual unica.
No OKD use o CronJob fornecido, a cada 15 minutos, com concurrencyPolicy: Forbid,
limite de duracao e lock PostgreSQL dedicado contra sobreposicao de executores.
Workers de aplicacao ainda usam leases por job. Cron e agendador local processam jobs explicitamente
solicitados e limpa artefatos vencidos; nao cria execucoes destrutivas por conta propria.

EXPORTACAO_BATCH_SIZE=100; EXPORTACAO_VALIDADE_HORAS=24; JOBS_LEASE_SEGUNDOS=180;
JOBS_POLL_SEGUNDOS=3; RETENCAO_BATCH_SIZE=100. Backend e workers compartilham
DATABASE_URL, MONGODB_URL/DATABASE e os S3_* existentes; nao usam volume final.
Em producao use bucket privado, credenciais com privilegios minimos, secrets reais,
gov.br real, sessao segura e migracao explicita antes de iniciar os workers.
O CMD da imagem nao aplica migrations no OKD:

```powershell
oc exec deployment/thor-pesquisador-backend -- alembic upgrade head
oc rollout status deployment/thor-pesquisador-export-worker
oc create job --from=cronjob/thor-pesquisador-retention retencao-manual
```

Comandos OKD sao referencia operacional, nao foram executados em cluster.
Renderizados: base e overlays dev/homolog/prod. A maquina nao possui contexto
Kubernetes configurado; readiness/rollout reais continuam dependentes do ambiente.

Uma criacao Mongo interrompida entre intencao e conclusao pode ser reconciliada,
apos investigar e aguardar pelo menos 10 minutos:

```powershell
docker compose exec -T backend python -m app.conformidade_cli UUID-DA-OPERACAO
```

O comando conclui o controle SQL se o documento existir ou registra cancelamento
se nao existir, sem apagar a intencao. Para outras divergencias, investigue o
historico editorial e a origem antes de repetir; nao altere checkpoints manualmente.
Nao execute reconciliacao enquanto a requisicao original ainda estiver em curso.

## Validacao

360 testes backend e 47 contratos frontend aprovados no Docker isolado.
Cobrem todas as combinacoes de transicao das duas maquinas, S3 multipart real,
JSON/CSV, SQL/Mongo/fila indisponiveis, retomada, concorrencia/idempotencia,
cancelamento, expiracao, revogacao, perfis inativos, holds, snapshots, imagens
compartilhadas e migration/rollback com dados legados e defaults personalizados.
Fluxos Playwright validados incluem sessao, concessoes-edicao, concessoes-crud,
concessoes-lote, concessoes-independentes, administracao, editorial, conformidade
e permissoes-crud. A revisao de 2026-10-16 repetiu conformidade, administracao,
sessao e permissoes-crud, alem dos 47 contratos e da compilacao.
Incluem screenshots desktop/mobile, menu acessivel em tela baixa, escopo limitado
por instrumento e comparacao de identidade com Instrumentos. Os demais CRUDs
administrativos continuam com seus popups de visualizacao.

```powershell
docker compose -f docker-compose.test.yml up -d --build backend storage_init
docker compose -f docker-compose.test.yml --profile e2e stop index_worker export_worker retention_scheduler
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests
docker compose -f docker-compose.test.yml --profile e2e up -d --build frontend index_worker export_worker retention_scheduler
```

O projeto/volumes isolados mantem o nome historico thor_pesquisador_fase4_test
para preservar dados de teste; SQL/Mongo terminam em _test e S3 e independente.
Nunca aponte testes funcionais/E2E ao banco operacional. Ao encerrar pare a stack
de teste, sem remover volumes. A stack operacional deve permanecer disponivel.
Warnings de depreciacao existentes (lifespan/AnyIO/python-jose) nao impedem os testes.
A fase 6 permanece planejada: carga real de producao, acessibilidade abrangente,
rotacao externa de logs e exercicios de backup/restore nao estao certificados aqui.
