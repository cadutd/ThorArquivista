# Fase 6 - Portal consultivo e operacao

Implementacao de 2026-10-16, exclusivamente no Thor Pesquisador. Este guia
substitui as regras anteriores de anonimato/sessao dos guias das fases 3/4/5.
As demais garantias editoriais, de autorizacao e de recuperacao permanecem.
O prompt registra a base historica anterior a implementacao, nao seu estado atual.

## Matriz de acesso

| Superficie | Anonimo | Visitante gov.br | Usuario ativo sem concessoes | Usuario autorizado |
| --- | --- | --- | --- | --- |
| Landing / e catalogo /consulta | Sim | Sim | Sim | Sim |
| Nome, tipo e descricao publicada de instrumento elegivel | Sim | Sim | Sim | Sim |
| Schema, busca, facetas, detalhe e galeria publicados | Login requerido | Sim | Sim | Sim |
| Conteudo de imagem PUBLICO de publicacao elegivel | Login requerido | Sim | Sim | Sim |
| Dashboard, pesquisa interna e CRUDs | Nao | Nao | Nao | Conforme RBAC/escopo |
| Auditoria, exportacoes, relatorios e retencao | Nao | Nao | Nao | Conforme RBAC/escopo |
| Configuracao institucional | Nao | Nao | Nao | Permissao global especifica |

Instrumentos INTERNO/RESTRITO, sem publicacao vigente ou arquivados nao entram
no catalogo. Dados de registros, campos, snippets, imagens e anexos nao fazem
parte da descoberta anonima. Publicacao de instrumento nao publica registros
automaticamente. Snapshots imutaveis, campos exibir_publico, estado operacional
ATIVO e direitos atuais continuam cumulativos. Revogacao vale imediatamente;
publicacao defasada no Meilisearch continua retornando 503, nao dados antigos.
Recursos nao elegiveis retornam 404 apos autenticar; ausencia de sessao retorna 401.

### Identidade e bloqueio

Reutilizam-se OIDC gov.br, CPF validado, Sessao, cookie HttpOnly e expiracao.
O callback valida assinatura RS256, emissor, audience, state, nonce e PKCE.
Nao existe cookie/provedor paralelo, Usuario automatico, perfil automatico
ou concessao automatica para visitantes. Login de desenvolvimento continua
restrito a dev/test; nao comprova as regras de um usuario comum.

Uma sessao consultiva tem usuario_id nulo e identidade pseudonima HMAC.
O CPF minimo fica na tabela privada de sessoes para reavaliar bloqueio por
cadastro posterior; nao vai ao catalogo, ranking, logs ou labels de metricas.
Aplicar a politica existente de retencao SESSAO conforme decisao institucional;
expirar token nao significa apagar automaticamente a linha do banco.

Se o CPF ja esta cadastrado inativo/excluido, nao emitir nem aceitar sessao,
inclusive visitante. Se cadastrado posteriormente, uma sessao de visitante
continua consultiva: exige novo login gov.br para vincular o Usuario e suas
concessoes. Isso evita promover silenciosamente um token antigo. Bloqueio
posterior vale na proxima requisicao, mesmo para sessoes consultivas anteriores.
Perfil inativo nao autoriza; ausencia de perfil nao bloqueia consulta publicada.

SessionGuard abre explicitamente apenas /, /consulta e /login. Todas as rotas
aninhadas de registros exigem sessao e as internas exigem tambem RBAC.
Revalidacao em navegacao, foco e a cada 60 segundos foi preservada.
401 em recurso protegido inicia login com next interno validado; 403 nao faz logout.
Falha de rede nao e tratada como credencial invalida na guarda.

## Rotas e configuracao institucional

- GET /api/v1/auth/estado: sessao opcional, 200 com autenticado=false para anonimo.
- GET /api/v1/auth/opcoes: informa disponibilidade de login dev, sem credenciais.
- GET /api/v1/auth/me e /auth/permissoes: exigem sessao; visitante nao tem permissoes.
- GET /api/v1/publico/instrumentos: catalogo seguro, q/tipo/limit/offset, ordem estavel.
- GET /api/v1/publico/destaques: ate 12 instrumentos elegiveis; padrao 6.
- GET /api/v1/publico/configuracao: somente nome institucional, cores e versao.
- GET/PUT /api/v1/publico/configuracao/administracao: consultar/editar global.
- POST /api/v1/publico/instrumentos/{id}/acessos: sessao valida e instrumento elegivel.
- GET /api/v1/publico/instrumentos/{id}, GET/POST buscar, GET facetas,
  registros/{registro_id} e registros/{registro_id}/imagens: exigem sessao.
- GET /api/v1/imagens/{id}/conteudo: exige sessao, inclusive miniatura.

Administracao -> Configuracao do Portal, em /portal/configuracao:
nome da instituicao, presets Institucional/Floresta/Vinho, cores individuais,
previa, salvar, cancelar e restaurar padrao com confirmacao.
Restaurar altera o rascunho; somente Salvar persiste.
Somente hex #RRGGBB e chaves permitidas; contraste minimo 4.5:1 entre fundo e
texto/primaria/secundaria/destaque. Valores CSS livres, URLs e campos extras
sao recusados no servidor. Versao esperada e lock de linha evitam sobrescrita
concorrente (409); alteracao gera auditoria com usuario autenticado.

Os tokens ficam escopados ao PortalShell; AppShell, fonte, escala e tema
administrativo nao mudam. Landing usa imagem institucional ja existente,
pesquisa funcional e cards de metadados, nunca capas extraidas de registros.
CrudPagination e componentes de busca/galeria existentes sao reaproveitados.
Scripts de navegador verificam estilos publicos versus raiz administrativa.
Nao ha prefetch de links para conteudo protegido nem dados de registros em
HTML estatico, metadados SEO ou assets institucionais.

URLs externas ja publicas nao podem ser tornadas privadas pela aplicacao.
Usar bucket privado e endpoint mediado para protecao de originais/miniaturas.
IIIF e repositorios externos dependem dos direitos e CORS de seus provedores.

## Ranking e desempenho

Conta-se uma consulta bem-sucedida por sessao/instrumento/dia UTC. Acesso a card
sem sessao nao conta. Navegador envia o comando apenas apos carregar a busca.
O servidor deduplica com PK e incrementa atomicamente a contagem diaria na mesma
transacao; repeticao nao aumenta o total. Ranking e agregado, nao pessoas unicas.

Ranking soma apenas contagens diarias dos ultimos 30 dias e reavalia
elegibilidade na consulta. Sem historico, mostra Instrumentos publicados;
nao inventa popularidade nem divulga contadores pessoais.
Ordenacao por contagem, data de publicacao e UUID garante desempate estavel.
retention_worker existente limpa deduplicadores e agregados antigos em lotes
limitados, sem novo worker ou alteracao do historico editorial.

Indices cobrem dia/instrumento e PKs. Teste SQL verifica ate duas consultas
SELECT para o ranking, sem N+1. Catalogo tem pagina maxima 100, pesquisa literal,
total no servidor e payload limitado; nao carrega registros para montar cards.
Galeria/facetas sao sob demanda. Consulta publicada ainda usa offset Meilisearch;
registros internos preservam cursor e Carregar mais, sem conversao para offset.
Nao foi acrescentado cache compartilhado: respostas da API ficam private/no-store.
Assets Next estaticos nao contem identidade ou registros.

Benchmark limitado e repetivel, sem criar massa nem tocar bancos operacionais:

```powershell
docker compose -f docker-compose.test.yml exec -T backend python -m app.scripts.medir_portal
```

O script exige app_env=test e nomes de bancos terminados em _test, imprime
volumes reais, 50 amostras por rota, p50/p95/max e RSS do processo.
TestClient mede aplicacao/SQL/logs, nao rede, ingress ou capacidade concorrente.
Pagina limitada e agregacao nao comprovam escala de milhoes. Busca regex interna
continua literal e nao e acelerada automaticamente pelo indice text do MongoDB.
Antes de maior escala: medir planos e buscas reais, concorrencia de leitura,
facetas, tempo de indexacao, memoria/respostas, offset Meilisearch e regex.
O indice interno nunca e fallback da projecao publicada.

## Migrations e permissoes

Head da entrega inicial: 20261016_000015, depois de 20261015_000013.
Em 2026-10-19, 20261019_000016 acrescentou capas opcionais, sem alterar as
publicacoes existentes. Regras atuais de catalogo/tabela, filtros, capas e
rollback em [Instrumentos e portal](instrumentos_portal.md).

- 000014: amplia sessoes sem invalidar Usuario/sessoes existentes; cria
  configuracao singleton e deduplicadores diarios. Nao altera publicacoes.
- 000015: cria contagem diaria agregada e faz backfill dos acessos existentes.
  Nenhum cadastro operacional e substituido ou removido.
- Catalogo passa de 55 a 57 permissoes: portal_configuracao_consultar e
  portal_configuracao_editar, ambas globais. Nao ha CRUD artificial de configuracoes.
- ADMIN ja tem wildcard global; perfis personalizados/padroes restantes,
  IDs e concessoes nao recebem novos privilegios automaticamente.

Downgrade 015 preserva os deduplicadores; recriar 015 reconstroi agregados.
Downgrade 014 recusa execucao enquanto existirem sessoes consultivas; nao as apaga
automaticamente. Exige revogacao/retencao aprovada e exportacao das configuracoes
e contagens antes da reversao. Remove somente os dois codigos novos dos perfis.
Restaurar imagem antiga nao desfaz schema ou backfill.
Nao retornar as APIs antigas de registros anonimos sem bloquear essas rotas no
ingress: rollback tecnico nao autoriza reabrir a exposicao.

## Seguranca e dependencias

Mutacoes recusam Origin nao permitido e Sec-Fetch-Site cross-site, alem dos
cookies e CORS existentes. Clientes nao-browser sem Origin continuam sujeitos
a sessao/RBAC. Configurar CORS com origens exatas por ambiente.
Corpo HTTP limitado a 1 MiB, upload ao limite configurado mais 1 MiB de envelope;
limites valem tambem para streaming e Content-Length invalido/excessivo.

Rate limit local por cliente/processo: govbr/start 30/minuto, descoberta/ranking
300/minuto por categoria compartilhada, armazenamento limitado a 4096 chaves HMAC.
429 informa Retry-After. Nao e limitador distribuido; configurar protecao de borda
para multiplas replicas e evitar confiar cegamente em X-Forwarded-For.
Configurar proxies confiaveis conforme a rede institucional; IP de ingress unico
sem repasse confiavel pode juntar visitantes no mesmo limite.

Respostas usam private/no-store, nosniff, referrer same-origin e frame DENY.
Next acrescenta CSP de frame-ancestors/object-src/base-uri, nao uma politica
script-src completa. Nao declarar ausencia de XSS apenas pelos headers.
Homolog/prod recusam dev-login, auth_disabled_for_tests, dev_admin_enabled,
cookie inseguro, secret de sessao curto, credenciais gov.br placeholders e
URLs publicas/callback sem HTTPS.

Atualizacoes testadas: Next 15.5.28, eslint-config-next correspondente,
PostCSS 8.5.30 por override, FastAPI 0.143.3/Starlette 1.8.0,
python-multipart 0.0.32, python-jose 3.5.0, PyMongo 4.18.2.
Lockfile npm e npm ci garantem reproducibilidade.
Audit de producao npm retornou zero vulnerabilidades na execucao local.
O audit completo ainda tem 5 alertas high de ferramentas dev ligadas a
braces/micromatch/fast-glob/eslint-config-next, sem correcao compativel publicada
na versao consultada. Nao foi aplicado audit fix --force; lint somente em codigo
confiavel. Reavaliar dependencias e imagens no pipeline institucional.

pip-audit dos requisitos atualizados manteve 3 registros em 2 pacotes sem fix
publicado: python-jose PYSEC-2026-4298 e ecdsa PYSEC-2026-1325 (alias duplicado).
A aplicacao fixa algorithms=[RS256] na verificacao OIDC e nao assina ECDSA/HMAC.
Essas restricoes mitigam os caminhos descritos, nao eliminam a necessidade de
acompanhar advisories e rever a biblioteca no proximo ciclo.
Nao se declara auditoria completa de imagens/base OS nem conformidade legal.

## Observabilidade e indisponibilidade

- /api/v1/health: liveness do processo, sem depender de bancos.
- /api/v1/ready: PostgreSQL, head Alembic e MongoDB; 503 generico na falha.
  SQL/Mongo tem timeouts limitados. S3, Redis e Meilisearch nao sao requisitos
  de leitura/cadastro basico; falhas especificas continuam nos comandos/jobs.
- /api/v1/operacao/metricas: sessao administrativa e dashboard_consultar global.
  Prometheus texto com HTTP por template/metodo/classe, histogramas de latencia,
  jobs por estado, idade, tempo sem progresso, processados, retries de exportacao
  e numero de publicacoes aguardando indexacao. Sem CPF, usuario ou registro nas labels.
- Metricas HTTP sao locais ao processo e reiniciam com ele; job gauges derivam SQL.
  Logs estruturados preservam request_id e template, nunca query/token/CPF.

Integracao com OpenShift Monitoring requer rede e autenticacao de scraping
institucionais; endpoint nao foi tornado publico nem se inventou credencial tecnica.
Configurar alertas de 5xx/readiness, fila PENDENTE sem progresso, PROCESSANDO
com lease vencido, publicacao defasada e erros S3. Thresholds devem ser medidos.
Erros/fila nao justificam servir indice antigo ou conceder privilegios.

Na indisponibilidade: manter liveness; readiness tira API com dependencia
essencial falha do servico; recuperar banco antes de retomar comandos.
Para Redis/Meilisearch, recuperar servicos e reconciliar/reindexar com scripts
existentes; para S3, preservar originais/checkpoints e retomar multipart/jobs.
Jobs de exportacao revalidam permissoes no processamento e download.
Dashboard/relatorios/historicos existentes complementam, nao substituem,
monitoramento externo de bancos, storage e plataforma.

## Docker e OKD

Local:

```powershell
docker compose up -d --build backend frontend index_worker export_worker retention_scheduler
```

Compose preserva volumes e ainda executa Alembic no startup local. Em OKD, usar
deploy/jobs/migration.yaml como Job manual pre-deploy, com imagem/tag e
ConfigMap/Secret corretos; nao rodar migration concorrente em cada replica.
deploy/base e overlays dev/homolog/prod continuam a unica estrutura de deploy.

Procedimento institucional:

1. Inventariar jobs, gerar backup consistente, validar restore e registrar head.
2. Bloquear no ingress as antigas rotas anonimas de registros durante a janela
   mista de versoes. Atualizar APIs/migrations antes de liberar o novo frontend.
3. Aplicar Secrets reais, TLS/Route/callback gov.br HTTPS, CORS e cookie seguro.
   O bootstrap de ADMIN segue o procedimento existente, nunca dev-login.
4. Executar Job Alembic ate 015, verificar logs sem secrets e readiness.
5. Atualizar backend e workers com mesma versao; aguardar todas as replicas novas.
6. Compilar frontend com NEXT_PUBLIC_API_BASE_URL correto, depois efetuar rollout.
   Mudar apenas env de runtime nao muda URL ja compilada no standalone.
7. Validar matriz anonimo/visitante/interno, revogacao, cores, jobs e S3 privado.
8. Habilitar scraping/alertas e revisar recursos/HPA com carga institucional.

Backend/frontend non-root, seccomp RuntimeDefault, sem token automatico de
ServiceAccount, sem privilegios/capacidades extras, rootfs read-only;
temporarios em emptyDir limitados e cache Next em volume proprio.
Uploads e exportacoes finais continuam S3, nunca filesystem do pod.
Teste local com UID arbitrario e smoke read-only passou, sem alterar SCC.
NetworkPolicy restringe ingress HTTP a ingress, monitoramento e frontend local.
Nao fecha egress: endpoints institucionais de DNS/SQL/Mongo/S3/gov.br precisam
ser definidos e validados na CNI antes de restringir saida.
Revisar seletores de namespaces/rotas da instituicao. MinIO local nao e storage
institucional recomendado. Probes/requests/limits existentes foram preservados
e complementados com startup/readiness/timeouts; workers mantem leases existentes.

Kustomize base/dev/homolog/prod foi renderizado com sucesso. Nao ha contexto
kubectl configurado nesta maquina: rollout, HPA, rotacao, TLS/callback real,
monitoramento e NetworkPolicy efetiva em OKD nao foram comprovados.
Exemplos de secrets de homolog/prod devem ser substituidos; validacao de runtime
recusa placeholders. Nao se declara prontidao institucional.

## Backup e continuidade

PostgreSQL e MongoDB sao fontes autoritativas; S3 contem originais, miniaturas,
partes e artefatos. Nao existe transacao unica entre eles. Para backup institucional,
pausar mutacoes/workers, concluir ou registrar multipart pendente, registrar
heads/publicacoes/checkpoints e gerar manifesto de referencias S3/tamanhos/SHA256.
Preferir snapshots/versionamento/PITR dos provedores com criptografia e acesso minimo.
Definir RPO/RTO e politica de retencao formalmente; nenhum SLA foi presumido.

Ensaio isolado:

```powershell
.\scripts\testar_continuidade.ps1
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests/functional/test_continuidade.py
```

O script aceita apenas a stack/bancos _test, cria destinos aleatorios guardados,
restaura dumps completos SQL/Mongo e compara cadastros, sessoes, auditoria,
configuracao, head e contagens de colecoes. Limpa apenas os destinos/artefatos
temporarios que criou, nunca os bancos de origem. Em ambiente sem escritas,
contagens e hash de configuracao devem coincidir.
O teste S3 copia/restaura uma amostra com streaming, SHA256 e tamanho reais,
em chaves proprias, e remove apenas essa amostra. Nao e restore integral do
bucket institucional nem prova de consistencia distribuida com mutacoes concorrentes.

Apos restore: conferir manifesto e direitos, reconciliar referencias, regenerar
indices Meilisearch interno/publico a partir de fontes corretas e reabrir
acesso somente apos validar geracoes. Redis nao substitui os jobs persistidos.
Reutilizar reconciliacao/checkpoints existentes; nao reexecutar indiscriminadamente
comandos editoriais nem apagar historicos. Retomar exportacoes com lease/checkpoint;
abortar multipart orfao apenas apos conferir dono/referencias e politica.
Backup nao e validado apenas porque pg_dump terminou: ensaiar recuperacao e
medir RTO institucional com volumes reais.

## Validacao reproduzivel

Somente docker-compose.test.yml, com bancos/filas/bucket isolados. Nunca rodar
pytest funcional no banco operacional; fixtures limpam dados de testes.
Parar index_worker/export_worker/retention_scheduler durante pytest.

```powershell
docker compose -f docker-compose.test.yml --profile e2e stop index_worker export_worker retention_scheduler
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider --tb=short app/tests
docker run --rm -v ./frontend:/app:ro -w /app node:22-alpine npm run test:functional
docker compose -f docker-compose.test.yml --profile e2e up -d --build frontend index_worker export_worker retention_scheduler
```

Playwright requer modulo existente e browsers; nao instala dependencias no host.
Configurar BASE_URL=http://localhost:3001, API_URL=http://localhost:8001/api/v1,
THOR_E2E_ISOLATED=true e PLAYWRIGHT_MODULE se fora do node_modules local.
Executar node frontend/tests/e2e/portal.smoke.cjs e as regressoes existentes.
portal.smoke exige AXE_SCRIPT apontando para axe.min.js oficial verificado;
na validacao foi axe-core 4.14.0, tarball registry npm com SRI:

```text
sha512-9WTZxEjsZ7b13TH8JPmbV2z8CHbl80/2hm3XPEG4JgNdQLK81IBRXmSxHfMAOkSqQeRxT/0dwNDz2GOm3zzpcQ==
```

O artefato foi extraido em TEMP somente para testes. Conferir dist.integrity
na metadata oficial antes de extrair nova versao; nao baixar script arbitrario.
WCAG 2 A/AA e 2.1 AA automatizado, screenshots desktop/mobile, foco/teclado
e overflow complementam validacao funcional; nao substituem auditoria humana.
Callback de teste usa JWT RSA real e HTTP do provedor controlado; verifica
nonce, emissor, assinatura, expiracao e audience. Nao houve login gov.br real
de producao, nem uso do dev ADMIN como unica prova de visitante.

### Evidencias locais em 2026-10-16

- Suite completa backend: 392 passaram; contratos frontend: 53 passaram.
  Inclui deduplicacao concorrente do ranking, fallback sem acessos e backfill
  real 014->015, alem da preservacao de sessoes e rollback protegido.
- Build Docker backend/frontend/index_worker/export_worker/retention_scheduler passou.
- Portal E2E passou: anonimato, paginacao real, retorno de login, visitante sem
  Usuario/grants, snapshot publicado, isolamento de tema e axe desktop/mobile.
- Regressao de sessao, administracao, permissoes CRUD e cinco fluxos de
  concessoes passaram com API real e verificacao desktop/mobile.
- Conformidade, editorial, imagens S3/IIIF e busca de registros tambem passaram:
  13 fluxos E2E no total. Fixtures de indexacao/publicacao processam somente
  seus proprios dados pelo servico real para nao depender do backlog antigo;
  filas e historicos nao foram apagados.
- Portal operacional em localhost:3000 validado em desktop/mobile e zoom CSS
  200%, sem overflow; APIs de registros/imagens/configuracao administrativa
  sem sessao retornaram 401. Ambiente local no head 015, volumes preservados.
- Benchmark TestClient: 3.674 instrumentos, 416 publicacoes elegiveis,
  3.593 registros Mongo, 23 deduplicadores e 13 contagens diarias.
  Catalogo (20 itens): p50 10,75 ms / p95 11,56 ms / max 13,05 ms.
  Ranking (6 itens): p50 9,12 ms / p95 10,47 ms / max 12,46 ms.
  RSS maxima do processo 127,95 MiB; 50 amostras por rota, sem concorrencia.
- Restore SQL/Mongo em destinos isolados: PASS em 5,15 s, head 015,
  4.215 usuarios/7.189 sessoes/30.064 eventos sinteticos preservados;
  3.593 registros e 452 snapshots restaurados sem falha. E tempo de ensaio
  pequeno local, nao RTO institucional. Teste de amostra S3 tambem passou.
- Kustomize base e tres overlays renderizados; UID arbitrario/read-only
  verificado localmente. Rollout OKD nao executado por ausencia de contexto.

Avisos remanescentes: depreciacao httpx no TestClient Starlette e warnings
Pydantic de alias em testes concorrentes; sem falhas nessa execucao.
Audits de dependencias e limites institucionais estao descritos acima.
