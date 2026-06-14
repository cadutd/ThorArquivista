# Thor Gestor de Arquivos Digitais

Manual de desenvolvimento do sistema Thor, uma aplicação para gestão de unidades de acondicionamento físicas e digitais, admissão de acervos, endereçamento de armazenamento, mídias, cópias digitais, instrumentos de pesquisa, pesquisa consultiva, fichas espelho e eventos de preservação.

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Requisitos](#requisitos)
- [Primeira Subida com Docker](#primeira-subida-com-docker)
- [Configuração do Keycloak](#configuração-do-keycloak)
- [Como Carregar as Massas de Teste](#como-carregar-as-massas-de-teste)
- [Como Executar Testes Funcionais e de Integração](#como-executar-testes-funcionais-e-de-integração)
- [Backend](#backend)
- [Frontend](#frontend)
- [Docker Compose](#docker-compose)
- [Banco de Dados e Migrations](#banco-de-dados-e-migrations)
- [Observações de Desenvolvimento](#observações-de-desenvolvimento)
- [Validação Local](#validação-local)
- [Problemas Comuns](#problemas-comuns)

## Visão Geral

O projeto é um monorepo composto por aplicações, serviços de apoio e scripts operacionais. A arquitetura foi desenhada para separar claramente interface, regras de negócio, persistência relacional, persistência documental, autenticação, indexação e processamento assíncrono.

Aplicações principais:

- `backend/`: API em FastAPI responsável pelas regras de negócio, validação de autenticação, orquestração das persistências, publicação de eventos assíncronos e exposição dos endpoints REST.
- `frontend/`: interface administrativa em Next.js, React, TypeScript e Tailwind CSS, responsável pela experiência de operação, autenticação OIDC no navegador e consumo da API.
- `index_worker`: worker Celery definido no `docker-compose.yml`, construído a partir da mesma imagem do backend, responsável por consumir eventos de indexação e manter o Meilisearch sincronizado.
- `workers/`: documentação histórica e operacional dos workers. O worker ativo vive hoje no pacote `backend/app`.

Serviços auxiliares sobem via Docker Compose:

- PostgreSQL principal: banco da aplicação.
- PostgreSQL do Keycloak: banco separado para identidade.
- Keycloak: provedor OIDC usado no login do frontend e na validação de tokens do backend.
- MongoDB: armazenamento dos registros dinâmicos dos instrumentos de pesquisa.
- Redis: infraestrutura de fila para Celery e coordenação operacional.
- Meilisearch: motor de busca local usado pelos registros dinâmicos dos instrumentos de pesquisa.
- pgAdmin: administração visual do PostgreSQL.

## Arquitetura

### Decisão Arquitetural

O Thor usa uma arquitetura modular em camadas, empacotada como monorepo e executada localmente por Docker Compose. A escolha principal é manter o domínio central em uma API REST única, com frontend desacoplado, banco relacional para dados transacionais, banco documental para registros de estrutura dinâmica, motor de busca dedicado para consulta avançada e fila assíncrona para trabalhos que não devem bloquear a operação do usuário.

Essa composição foi escolhida porque o sistema combina necessidades diferentes:

- operações administrativas transacionais, como CRUDs, admissão, endereçamento e movimentações, que exigem integridade, constraints, migrations e consistência forte;
- registros de instrumentos de pesquisa com campos configuráveis por instrumento, que mudam de forma sem exigir alteração de schema relacional a cada novo instrumento;
- busca consultiva e avançada sobre campos dinâmicos, facetas e texto consolidado, que é mais eficiente em um motor especializado do que em consultas relacionais genéricas;
- autenticação centralizada via OIDC, para permitir integração institucional e validação padronizada de identidade;
- indexação assíncrona, para que cadastro/edição de registros continue responsivo mesmo quando a busca precisa ser atualizada em segundo plano.

### Visão de Alto Nível

```text
Navegador
  |
  | OIDC Authorization Code + PKCE
  v
Frontend Next.js  <------------------------>  Keycloak
  |
  | HTTP REST + Bearer token
  v
Backend FastAPI
  |       |             |             |
  |       |             |             +--> Redis/Celery --> index_worker --> Meilisearch
  |       |             |
  |       |             +--> MongoDB
  |       |
  |       +--> PostgreSQL
  |
  +--> JWKS/issuer/audience validation via Keycloak
```

Fluxo principal de autenticação e uso:

1. O usuário acessa o frontend em `http://localhost:3000`.
2. Ao clicar em `Entrar com Keycloak`, o frontend inicia o fluxo OIDC Authorization Code + PKCE no Keycloak em `http://localhost:8081`.
3. O Keycloak autentica o usuário e redireciona para `http://localhost:3000/auth/callback`.
4. O frontend troca o `code` por tokens e guarda a sessão no navegador.
5. Chamadas ao backend usam `Authorization: Bearer <access_token>`.
6. O backend valida o JWT usando o JWKS do Keycloak pela URL interna Docker `http://keycloak:8080`.
7. A API persiste metadados relacionais no PostgreSQL em `postgres:5432`.
8. Registros dinâmicos de instrumentos de pesquisa são salvos no MongoDB.
9. A API publica eventos de indexação no Redis e o `index_worker` processa esses eventos em segundo plano.
10. O worker envia documentos indexáveis ao Meilisearch, usando um índice por instrumento.

### Camadas do Backend

O backend segue uma divisão explícita por responsabilidades:

| Camada | Diretório | Responsabilidade | Motivo da escolha |
| --- | --- | --- | --- |
| Entrada HTTP | `backend/app/api/v1/` | Define rotas FastAPI, parâmetros, status codes, dependências de autenticação e contratos de entrada/saída. | Mantém o protocolo HTTP isolado da regra de negócio e facilita versionamento sob `/api/v1`. |
| Schemas | `backend/app/schemas/` | Define DTOs Pydantic de criação, atualização, leitura, filtros, paginação e payloads específicos. | Garante validação consistente na borda da API e evita expor diretamente modelos ORM. |
| Serviços | `backend/app/services/` | Concentra regras de negócio, transações, validações de domínio, composição de consultas e orquestração entre bancos/fila/busca. | Evita que rotas virem scripts procedurais e permite testar comportamento de domínio sem acoplar tudo ao transporte HTTP. |
| Modelos | `backend/app/models/` | Define entidades SQLAlchemy, enums, relacionamentos, constraints e campos persistidos no PostgreSQL. | Centraliza o modelo relacional e mantém o Alembic alinhado com a evolução do schema. |
| Banco relacional | `backend/app/db/` | Configura sessão SQLAlchemy, base declarativa e conexão com PostgreSQL. | Separa infraestrutura de persistência do domínio e permite injeção de sessão nas rotas/serviços. |
| Banco documental | `backend/app/db/mongo.py` | Configura acesso ao MongoDB para registros dinâmicos. | Permite persistir documentos de instrumentos sem alterar tabelas para cada conjunto de campos. |
| Segurança | `backend/app/security/` | Valida JWT, JWKS, issuer, audience e extrai claims do usuário autenticado. | Mantém autenticação/autorização como preocupação transversal e reutilizável. |
| Configuração | `backend/app/core/config.py` | Lê variáveis de ambiente por Pydantic Settings. | Padroniza configuração para Docker e execução local, com tipagem e defaults controlados. |
| Workers e tarefas | `backend/app/worker.py`, `backend/app/tasks/` | Define app Celery e tarefas de indexação. | Reusa código do backend no worker sem duplicar modelos, serviços e configuração. |
| Scripts operacionais | `backend/app/scripts/` | Seeds idempotentes e cargas auxiliares. | Permite preparar ambientes de teste/demonstração por comandos reproduzíveis. |

### Backend FastAPI

FastAPI foi escolhido por combinar tipagem, validação automática, geração de OpenAPI e boa ergonomia para APIs REST. No Thor, ele atua como a única porta de entrada para as regras de negócio. As rotas sob `/api/v1` usam dependências para autenticação, sessão de banco e autorização básica, enquanto os serviços executam as validações de domínio.

O backend também concentra a integração entre componentes:

- consulta e grava dados relacionais no PostgreSQL;
- grava registros dinâmicos no MongoDB;
- publica eventos Celery no Redis;
- lê configurações de busca e monta documentos indexáveis para o Meilisearch;
- valida tokens emitidos pelo Keycloak;
- expõe contratos estáveis para o frontend.

Essa centralização evita que o frontend fale diretamente com bancos, fila ou motor de busca. Com isso, a regra de negócio fica auditável no servidor e o navegador recebe apenas APIs de domínio.

### Frontend Next.js

Next.js foi escolhido para entregar uma aplicação React com roteamento por arquivos, build otimizado, tipagem TypeScript e organização clara entre `app/`, `features/`, `components/` e `lib/`.

No Thor, o frontend é uma aplicação administrativa autenticada. Ele:

- inicia o fluxo OIDC Authorization Code + PKCE;
- guarda a sessão no navegador;
- injeta `Authorization: Bearer <access_token>` nas chamadas;
- organiza telas por módulo funcional;
- usa clientes em `frontend/lib/api/` para isolar detalhes de endpoints;
- mantém componentes de domínio em `frontend/features/`;
- usa React Query para cache, invalidação e estado remoto.

A escolha por frontend desacoplado permite evoluir a experiência de usuário sem alterar diretamente a API e permite que a API seja consumida futuramente por integrações ou ferramentas administrativas alternativas.

### PostgreSQL Principal

PostgreSQL é o banco transacional do sistema. Ele armazena entidades que dependem de integridade referencial, constraints, enums, transações e histórico consistente:

- unidades de acondicionamento;
- unidades digitais;
- mídias de armazenamento;
- cópias digitais;
- eventos de preservação;
- endereçamento de armazenamento;
- movimentações;
- processos de admissão;
- reuniões, acordos, sessões, SIPs e vínculos SIP/AIP;
- usuários administrativos;
- instituições de arquivo;
- entidades produtoras;
- descrições arquivísticas;
- modelos de ficha espelho;
- metadados de instrumentos de pesquisa e campos configurados.

O PostgreSQL foi escolhido para essas partes porque o domínio arquivístico possui muitos vínculos formais, estados controlados e necessidade de consistência. Migrations Alembic garantem evolução rastreável do schema.

### MongoDB

MongoDB é usado para os registros dinâmicos dos instrumentos de pesquisa. Esses registros possuem campos configuráveis por instrumento, o que torna inadequado criar uma tabela nova ou uma coluna nova para cada variação de formulário.

A separação adotada é:

- PostgreSQL guarda o instrumento, sua configuração e campos;
- MongoDB guarda os registros preenchidos conforme essa configuração;
- Meilisearch guarda uma projeção indexável desses registros.

Essa decisão preserva governança relacional onde ela é necessária e dá flexibilidade documental onde o domínio exige variação estrutural.

### Meilisearch

Meilisearch é o motor de busca local para registros dinâmicos de instrumentos de pesquisa. Ele foi escolhido para busca textual, filtros e facetas em estruturas que mudam por instrumento. Cada instrumento usa um índice próprio no padrão:

```text
instrumento_{instrumento_id}
```

A API não depende do Meilisearch para confirmar uma gravação. Primeiro salva no MongoDB, depois publica evento de indexação. Isso evita que uma indisponibilidade momentânea do motor de busca impeça o cadastro operacional.

Na busca avançada de instrumentos, a tela `Busca por metadado` monta filtros para todos os campos dinâmicos configurados no schema do instrumento. Campos facetáveis usam opções vindas do índice quando disponíveis; campos de intervalo usam limites `De`/`Até`; e campos de referência, como `Unidade de Acondicionamento` e `Mídia de Armazenamento`, usam lookup por lupa para selecionar o registro relacionado. Esses campos de referência são persistidos nos registros dinâmicos como `{ id, rotulo }`, filtrados no Meilisearch pelo `id` e exibidos nas listagens como links para `/unidades/{id}` e `/midias/{id}`.

### Redis e Celery

Redis atua como broker Celery e infraestrutura de coordenação operacional. Celery foi escolhido para processar tarefas assíncronas com semântica simples de fila, separando requisições HTTP de trabalhos em segundo plano.

No fluxo de instrumentos de pesquisa:

1. A API cria, atualiza ou exclui um registro dinâmico.
2. A operação principal é persistida.
3. A API publica um evento no Redis.
4. O `index_worker` consome a fila `indexacao`.
5. O worker atualiza ou remove o documento no Meilisearch.

Essa arquitetura reduz latência percebida pelo usuário, limita acoplamento entre API e busca e permite reprocessar indexações sem recriar a operação de negócio.

### Worker de Indexação

O `index_worker` usa a mesma imagem do backend e executa:

```bash
celery -A app.worker.celery_app worker --loglevel=INFO --queues=indexacao --concurrency=1
```

Ele fica separado da API para que falhas, lentidão ou picos de indexação não consumam os mesmos workers HTTP do Uvicorn. A mesma base de código foi mantida para evitar duplicação de schemas, serviços, configuração e lógica de montagem dos documentos indexáveis.

Eventos suportados:

- `REGISTRO_CRIADO`
- `REGISTRO_ATUALIZADO`
- `REGISTRO_EXCLUIDO`
- `REINDEXAR_INSTRUMENTO`

### Keycloak

Keycloak é o provedor de identidade OIDC. Ele foi escolhido para separar autenticação da aplicação, usar um padrão aberto e permitir futura integração com políticas institucionais de identidade.

No ambiente local:

- o navegador acessa o Keycloak por `http://localhost:8081`;
- o backend valida tokens usando a URL interna Docker `http://keycloak:8080`;
- o issuer esperado permanece baseado na URL pública do realm;
- o serviço `keycloak_config` configura automaticamente o client `thor-api`;
- o frontend usa Authorization Code + PKCE, adequado para aplicações públicas em navegador.

Essa separação reduz a responsabilidade da aplicação sobre senhas, login e sessão primária. O backend se limita a validar tokens e interpretar claims.

### pgAdmin

pgAdmin é incluído apenas como ferramenta operacional local. Ele facilita inspeção do PostgreSQL durante desenvolvimento, suporte e validação de seeds. Não faz parte do caminho crítico da aplicação.

### Docker Compose

Docker Compose foi escolhido como orquestração local porque o sistema depende de múltiplos serviços com versões específicas. Ele permite subir um ambiente completo com um único comando, mantendo nomes DNS internos previsíveis:

- `postgres`
- `mongo`
- `redis`
- `meilisearch`
- `keycloak`
- `backend`
- `frontend`
- `index_worker`

O Compose também automatiza dependências de inicialização, healthcheck do PostgreSQL, execução de migrations e configuração do Keycloak.

### Versionamento e Evolução do Banco

Alembic é usado para versionar o PostgreSQL. O container do backend executa automaticamente:

```bash
alembic -c alembic.ini upgrade head
```

Essa escolha garante que o banco acompanhe o código na subida do ambiente, reduz divergências entre desenvolvedores e registra a evolução do modelo relacional.

### Fronteiras de Persistência

O sistema usa persistência poliglota, mas com fronteiras claras:

| Componente | Guarda | Não deve guardar |
| --- | --- | --- |
| PostgreSQL | Dados transacionais, relacionamentos, enums, configurações, histórico e entidades centrais. | Registros altamente variáveis que mudam por instrumento. |
| MongoDB | Conteúdo flexível dos registros dinâmicos dos instrumentos. | Entidades com integridade relacional forte ou regras de movimentação transacional. |
| Meilisearch | Projeções de busca, facetas e texto consolidado. | Fonte canônica de dados. |
| Redis | Mensagens Celery e estado operacional efêmero. | Dados de negócio permanentes. |

### Consistência e Assincronia

O PostgreSQL e o MongoDB são fontes de verdade para seus respectivos dados. Meilisearch é uma projeção derivada e eventualmente consistente. Isso significa que uma gravação pode estar confirmada na API antes de aparecer na busca avançada. Essa troca é deliberada: privilegia confiabilidade da operação principal e permite reindexação quando necessário.

Para cargas e correções operacionais, a API expõe caminho de reindexação por evento:

```bash
docker compose exec backend python -c "from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher; InstrumentoIndexingEventPublisher.reindexar_instrumento('UUID_DO_INSTRUMENTO')"
```

### Segurança

As rotas de domínio são protegidas por token Bearer. A rota de health é pública para facilitar verificação de disponibilidade.

Decisões relevantes:

- autenticação delegada ao Keycloak;
- frontend usa PKCE em vez de client secret, porque roda no navegador;
- backend valida assinatura via JWKS;
- backend valida issuer/audience conforme configuração;
- CORS é restrito ao frontend local no Compose;
- credenciais do ambiente Docker são de desenvolvimento e não devem ser usadas em produção.

### Observabilidade Local

O ambiente local prioriza diagnósticos simples:

- logs por serviço via `docker compose logs -f <serviço>`;
- OpenAPI em `http://localhost:8000/docs`;
- pgAdmin para PostgreSQL;
- Meilisearch em `http://localhost:7700`;
- testes backend via `pytest`;
- testes frontend funcionais via `node --test`;
- relatório consolidado via `scripts/run-tests-with-reports.ps1`.

URLs locais principais:

| Serviço | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| Backend docs | `http://localhost:8000/docs` |
| Keycloak | `http://localhost:8081` |
| pgAdmin | `http://localhost:5051` |
| Meilisearch | `http://localhost:7700` |

## Estrutura do Repositório

```text
.
├── backend/              # FastAPI, SQLAlchemy, Alembic e scripts operacionais
├── frontend/             # Next.js, React, Tailwind CSS e autenticação OIDC
├── workers/              # Documentação de workers assíncronos
├── infra/keycloak/       # Scripts de configuração automática do Keycloak
├── pgadmin/provisioning/ # Configuração automática de servidores no pgAdmin
├── docker-compose.yml    # Stack local completa
└── README.md             # Este manual
```

## Requisitos

Para rodar com Docker:

- Docker Desktop ou Docker Engine com Compose.
- Portas livres: `3000`, `5051`, `5433`, `6379`, `7700`, `8000`, `8081`, `27017`.

Para rodar fora do Docker:

- Node.js `24.15.0` ou superior para o frontend.
- Python `3.13` recomendado para o backend.
- PostgreSQL acessível.
- Keycloak acessível.

## Primeira Subida com Docker

Na raiz do projeto:

```bash
docker compose up --build
```

Esse comando:

- constrói o backend;
- constrói o frontend;
- sobe PostgreSQL, MongoDB, Redis, Meilisearch, Keycloak, pgAdmin e o worker de indexação;
- executa migrations Alembic no backend antes de iniciar a API;
- executa `keycloak_config`, que ajusta o client `thor-api` para aceitar o callback do frontend.

Após os containers estabilizarem:

- Abra `http://localhost:3000`.
- Clique em `Entrar com Keycloak`.
- Use um usuário existente no realm `thor`.

Credenciais administrativas locais:

| Serviço | Usuário | Senha |
| --- | --- | --- |
| Keycloak admin | `admin` | `admin` |
| pgAdmin | `admin@thor.com` | `admin` |
| PostgreSQL app | `thor` | `thor` |

Banco principal:

- Database: `thor_db`
- Host dentro do Docker: `postgres`
- Host no sistema local: `localhost`
- Porta no sistema local: `5433`
- Porta dentro da rede Docker: `5432`

## Configuração do Keycloak

O serviço `keycloak_config` usa o script:

```text
infra/keycloak/configure-client.sh
```

Ele autentica no Keycloak usando o admin local e configura o ambiente de identidade do Thor. O script é idempotente e:

- cria o realm `thor` se ele ainda não existir;
- cria/atualiza o usuário local `admin` no realm `thor`;
- cria/atualiza o client `thor-api`;
- ajusta o client para uso pelo frontend público com PKCE.

Configurações aplicadas ao client:

- `redirectUris`: `http://localhost:3000/auth/callback` e `http://localhost:3000/*`
- `webOrigins`: `http://localhost:3000`
- fluxo padrão OIDC habilitado;
- client público habilitado.

Se o Keycloak já estava rodando e você quiser reaplicar a configuração:

```bash
docker compose run --rm keycloak_config
```

## Como Carregar as Massas de Teste

As massas de teste ficam em scripts idempotentes no pacote `backend/app/scripts/`. A recomendação é carregá-las com a stack Docker em execução, porque assim os scripts usam as mesmas URLs internas, enums PostgreSQL, migrations e serviços auxiliares usados pela aplicação.

Antes de carregar qualquer massa, suba a stack e aguarde backend, MongoDB, Redis, Meilisearch e worker estabilizarem:

```bash
docker compose up --build
```

Em outro terminal, confirme que a API responde:

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"
```

Se o ambiente já estava rodando, aplique migrations manualmente antes da carga:

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

### Ordem Recomendada de Carga

Para um ambiente de desenvolvimento completo, use esta ordem:

```bash
docker compose exec backend python -m app.scripts.seed_instituicao_arquivo_apesp
docker compose exec backend python -m app.scripts.seed_entidades_produtoras
docker compose exec backend python -m app.scripts.seed_perfis_permissoes
docker compose exec backend python -m app.scripts.seed_test_units
docker compose exec backend python -m app.scripts.seed_storage_addressing
docker compose exec backend python -m app.scripts.seed_midias_armazenamento
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

Essa ordem evita dependências ausentes nos fluxos administrativos: primeiro cadastra dados institucionais, entidades produtoras, perfis e permissões, depois unidades, endereçamento, mídias e, por fim, instrumentos com campos e registros dinâmicos.

Massa de permissões e perfis:

```bash
docker compose exec backend python -m app.scripts.seed_perfis_permissoes
```

Esse script é idempotente e cria permissões para cada função mapeada do sistema, sempre com as ações `CRIAR`, `EDITAR`, `CONSULTAR` e `EXCLUIR`. Também cria/atualiza os perfis padrão `Administrador`, `Arquivista`, `Admissão`, `Gestor de Armazenamento` e `Consulta`, vincula permissões coerentes a cada perfil e associa usuários legados ao perfil correspondente quando `usuarios.papel` tiver o mesmo código do perfil. O perfil legado `Operador` é removido; usuários com papel legado `OPERADOR` são migrados para `Arquivista`.

Existe um script idempotente para criar 50 unidades de teste:

- `25` unidades físicas;
- `25` unidades digitais;
- `25` extensões em `unidades_acondicionamento_digitais` para as unidades digitais.

Script:

```text
backend/app/scripts/seed_test_units.py
```

Com os containers rodando:

```bash
docker compose exec backend python -m app.scripts.seed_test_units
```

O script usa identificadores fixos:

- `TEST-FIS-001` até `TEST-FIS-025`
- `TEST-DIG-001` até `TEST-DIG-025`

Pode ser executado várias vezes. Se os registros já existirem, eles são atualizados, não duplicados.

Para conferir no PostgreSQL:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select tipo_suporte, count(*) from unidades_acondicionamento where identificador like 'TEST-%' group by tipo_suporte order by tipo_suporte;"
```

Também existe um script idempotente para criar massa de endereçamento de armazenamento:

```text
backend/app/scripts/seed_storage_addressing.py
```

Com os containers rodando:

```bash
docker compose exec backend python -m app.scripts.seed_storage_addressing
```

Essa massa cria:

- `1` local de guarda: `TEST-DEP-01`;
- `2` zonas: `ZT01` e `ZT02`;
- `20` estantes por zona;
- `5` prateleiras por estante;
- `10` posições por prateleira;
- `2.000` posições no total.

Para conferir no PostgreSQL:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select lg.codigo as local, count(distinct zg.id) zonas, count(distinct ea.id) estruturas, count(distinct ca.id) compartimentos, count(pa.id) posicoes from locais_guarda lg join zonas_guarda zg on zg.id_local_guarda = lg.id join estruturas_armazenamento ea on ea.id_zona_guarda = zg.id join compartimentos_armazenamento ca on ca.id_estrutura_armazenamento = ea.id join posicoes_armazenamento pa on pa.id_compartimento_armazenamento = ca.id where lg.codigo = 'TEST-DEP-01' group by lg.codigo;"
```

Massa de instrumentos de pesquisa:

```bash
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

Esses scripts são idempotentes e criam:

- instrumentos de pesquisa de teste;
- campos dinâmicos por instrumento;
- registros dinâmicos no MongoDB;
- eventos Celery para indexação assíncrona no Meilisearch.

O seed de registros gera 35 registros por instrumento e publica eventos na fila `indexacao`. O `index_worker` deve estar rodando para que a massa também seja indexada no Meilisearch.

Para acompanhar a indexação:

```bash
docker compose logs -f index_worker
```

Para reindexar manualmente um instrumento depois da carga:

```bash
docker compose exec backend python -c "from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher; InstrumentoIndexingEventPublisher.reindexar_instrumento('UUID_DO_INSTRUMENTO')"
```

Massa de mídias de armazenamento:

```bash
docker compose exec backend python -m app.scripts.seed_midias_armazenamento
```

O script é idempotente e cria/atualiza 72 mídias de teste, com tipos variados (`FILESYSTEM`, `NAS`, `NFS`, `LTO`, `S3`, `CLOUD`) e status ativo/inativo. Essa massa permite validar busca, filtros por metadado, paginação e lazy load na tela `/midias`.

### Conferências Pós-Carga

Conferir unidades:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select tipo_suporte, count(*) from unidades_acondicionamento where identificador like 'TEST-%' group by tipo_suporte order by tipo_suporte;"
```

Conferir endereçamento:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select lg.codigo as local, count(distinct zg.id) zonas, count(distinct ea.id) estruturas, count(distinct ca.id) compartimentos, count(pa.id) posicoes from locais_guarda lg join zonas_guarda zg on zg.id_local_guarda = lg.id join estruturas_armazenamento ea on ea.id_zona_guarda = zg.id join compartimentos_armazenamento ca on ca.id_estrutura_armazenamento = ea.id join posicoes_armazenamento pa on pa.id_compartimento_armazenamento = ca.id where lg.codigo = 'TEST-DEP-01' group by lg.codigo;"
```

Conferir mídias:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select tipo, status, count(*) from midias_armazenamento group by tipo, status order by tipo, status;"
```

Conferir instrumentos no PostgreSQL:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select codigo, nome, status from instrumentos_pesquisa order by codigo;"
```

Conferir registros dinâmicos no MongoDB:

```bash
docker compose exec mongo mongosh thor_db --eval "db.instrumento_registros.countDocuments()"
```

### Reset Completo das Massas

Para recriar o ambiente do zero, remova volumes e suba novamente:

```bash
docker compose down -v
docker compose up --build
```

Depois execute novamente a ordem recomendada de carga. Use `down -v` com cuidado, pois remove dados do PostgreSQL, Keycloak, MongoDB, Redis, Meilisearch e pgAdmin.

## Como Executar Testes Funcionais e de Integração

O projeto possui testes backend em `backend/app/tests`, testes funcionais de contrato no frontend em `frontend/tests/functional` e teste E2E de login Keycloak em `frontend/tests/e2e`.

### Pré-Requisitos

Para testes com maior fidelidade ao ambiente real, use Docker:

```bash
docker compose up --build
```

O backend no container já instala `pytest` a partir de `backend/requirements.txt`. O frontend deve ser testado a partir do diretório `frontend/` no ambiente local de desenvolvimento, porque o container `thor-frontend` é uma imagem de produção e não inclui todos os arquivos de teste e fontes usados por `lint`, `typecheck` e `node --test`.

### Testes Backend

Executar toda a suíte backend:

```bash
docker exec thor-backend pytest /app/app/tests
```

Executar apenas testes funcionais backend:

```bash
docker exec thor-backend pytest /app/app/tests/functional
```

Executar apenas testes de integração backend:

```bash
docker exec thor-backend pytest /app/app/tests/integration
```

Executar um fluxo específico de admissão:

```bash
docker exec thor-backend pytest /app/app/tests/functional/test_crud_admissao.py /app/app/tests/integration/test_admissao_integrado.py
```

Os testes backend usam `TestClient` do FastAPI e sobrescrevem a dependência de usuário autenticado em `backend/app/tests/conftest.py`, permitindo testar rotas protegidas sem depender de login real no Keycloak.

### Testes Funcionais Frontend

Os testes funcionais do frontend validam contratos locais dos clientes de API e cobertura das funções CRUD expostas para as telas.

```bash
cd frontend
npm install
npm run test:functional
```

### Teste E2E com Keycloak

O teste E2E usa Playwright e valida o fluxo real de login do usuário via Keycloak:

```bash
cd frontend
npm install
npx playwright install chromium
npm run test:e2e:keycloak
```

O `playwright.config.mjs` usa `http://localhost:3000` como `baseURL` por padrão, podendo ser sobrescrito por `E2E_APP_URL`.

### Relatórios de Teste

Existe um script PowerShell para executar backend e frontend funcional, coletar JUnit XML e gerar resumo Markdown/HTML:

```powershell
.\scripts\run-tests-with-reports.ps1
```

Saídas geradas:

- `test-reports/backend/junit.xml`
- `test-reports/frontend/junit.xml`
- `test-reports/summary.md`
- `test-reports/summary.html`

### Validação Complementar

Além dos testes funcionais e de integração, rode validações estáticas do frontend:

```bash
cd frontend
npm run typecheck
npm run lint
```

Para validar o backend fora da suíte completa:

```bash
docker exec thor-backend python -m py_compile /app/app/api/v1/router.py /app/app/main.py
```

## Backend

Stack principal:

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL via `psycopg`
- MongoDB via `pymongo`
- Redis e Celery para eventos assíncronos
- Meilisearch para busca dedicada dos registros dinâmicos
- Keycloak JWT validation via `python-jose`
- Pydantic Settings

Arquivos importantes:

- `backend/app/main.py`: cria a aplicação FastAPI, adiciona CORS e registra as rotas.
- `backend/app/api/v1/router.py`: agrega as rotas públicas e protegidas.
- `backend/app/api/v1/dashboard.py`: expõe indicadores agregados do dashboard.
- `backend/app/api/v1/armazenamento.py`: expõe CRUD, topografia, atribuição de posições e movimentações de armazenamento.
- `backend/app/models/armazenamento.py`: models do endereçamento de armazenamento.
- `backend/app/services/armazenamento_service.py`: regras de negócio de ocupação, capacidade, movimentação e geração topográfica.
- `backend/app/services/instrumento_registro_service.py`: cadastro, listagem, busca simples e publicação de eventos de indexação dos registros dinâmicos.
- `backend/app/services/instrumento_search_service.py`: montagem dos documentos indexáveis e comunicação com Meilisearch.
- `backend/app/tasks/instrumento_indexacao.py`: tarefas Celery para indexação assíncrona.
- `backend/app/worker.py`: aplicação Celery usada pelo serviço `index_worker`.
- `backend/app/security/keycloak_jwt.py`: valida JWT e busca JWKS no Keycloak.
- `backend/app/core/config.py`: configurações por variáveis de ambiente.
- `backend/alembic/versions/`: migrations do banco.
- `backend/app/scripts/`: scripts operacionais, incluindo seed de teste.

Rodar fora do Docker:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Variáveis principais usadas pelo backend no Compose:

```env
app_env=dev
app_name=Thor Gestor de Arquivos Digitais
database_url=postgresql+psycopg://thor:thor@postgres:5432/thor_db
redis_url=redis://redis:6379/0
meili_url=http://meilisearch:7700
meili_master_key=dev-meili-key
keycloak_url=http://localhost:8081
keycloak_internal_url=http://keycloak:8080
keycloak_realm=thor
keycloak_client_id=thor-api
keycloak_verify_audience=true
cors_origins=["http://localhost:3000"]
```

Rotas de domínio são protegidas por Keycloak. A rota de health é pública.

Rotas principais sob `/api/v1`:

| Rota | Finalidade |
| --- | --- |
| `/health` | Health check público |
| `/auth/me` | Dados do usuário autenticado |
| `/dashboard` | Totais agregados para o dashboard |
| `/unidades-acondicionamento` | CRUD, filtros e paginação de unidades |
| `/midias-armazenamento` | Cadastro, filtros e paginação de mídias |
| `/unidades-acondicionamento/{id}/copias` | Cópias digitais de uma unidade |
| `/unidades-acondicionamento/{id}/eventos-preservacao` | Eventos de preservação de uma unidade |
| `/locais-guarda` | CRUD de locais de guarda |
| `/zonas-guarda` | CRUD de zonas e geração de topografia |
| `/estruturas-armazenamento` | CRUD de estruturas |
| `/compartimentos-armazenamento` | CRUD de compartimentos |
| `/posicoes-armazenamento` | Consulta e CRUD de posições |
| `/movimentacoes-armazenamento` | Histórico de movimentações |
| `/admissao/processos` | CRUD de processos de admissão, filtros e paginação |
| `/admissao/processos/{id}/reunioes` | Reuniões vinculadas ao processo de admissão |
| `/admissao/processos/{id}/acordos` | Acordos de admissão e versionamento |
| `/admissao/processos/{id}/sessoes` | Sessões de submissão do processo |
| `/admissao/processos/{id}/sips` | SIPs recebidos no processo |
| `/admissao/processos/{id}/eventos` | Linha de eventos do processo de admissão |
| `/instrumentos-pesquisa` | Cadastro de instrumentos, campos e registros dinâmicos |
| `/instrumentos-pesquisa/{id}/registros` | Listagem dinâmica por cursor |
| `/instrumentos-pesquisa/{id}/buscar` | Busca simples inicial no MongoDB, usando campos `aparece_busca` |
| `/instrumentos-pesquisa/{id}/buscar-avancado` | Busca avançada dinâmica no Meilisearch, com filtros por todos os campos do instrumento |
| `/instrumentos-pesquisa/{id}/facetas` | Valores facetados dinâmicos a partir do índice de busca |
| `/fichas-espelho/modelos` | CRUD de modelos de ficha espelho |
| `/fichas-espelho/modelos/padrao` | Modelo padrão ativo de ficha espelho |
| `/fichas-espelho/gerar` | Geração de fichas espelho para impressão |

Endpoints de atribuição de posição:

| Rota | Finalidade |
| --- | --- |
| `/unidades-acondicionamento/{id}/atribuir-posicao` | Atribui posição a uma unidade |
| `/midias-armazenamento/{id}/atribuir-posicao` | Atribui posição a uma mídia |
| `/copias-unidades-acondicionamento-digitais/{id}/atribuir-posicao` | Atribui posição a uma cópia digital |

O dashboard usa uma rota agregada própria para evitar contagens incorretas geradas por listagens paginadas.

## Frontend

Stack principal:

- Next.js `16`
- React `19`
- TypeScript
- Tailwind CSS `4`
- React Query
- TanStack Table
- Radix UI
- Lucide Icons
- Zod

Arquivos importantes:

- `frontend/app/login/page.tsx`: tela de login com imagem institucional de arquivo digital.
- `frontend/app/auth/callback/page.tsx`: callback OIDC.
- `frontend/app/(app)/dashboard/page.tsx`: tela principal do sistema com indicadores.
- `frontend/app/(app)/unidades/page.tsx`: CRUD de unidades de acondicionamento.
- `frontend/app/(app)/enderecamento/`: telas de endereçamento de armazenamento.
- `frontend/features/armazenamento/`: componentes, páginas e labels do módulo de endereçamento.
- `frontend/features/unidades/unidades-table.tsx`: tabela, filtros, ações e paginação de unidades.
- `frontend/lib/auth/oidc.ts`: início e conclusão do fluxo OIDC com PKCE.
- `frontend/lib/auth/auth-provider.tsx`: estado de autenticação.
- `frontend/lib/api/client.ts`: cliente HTTP com token Bearer.
- `frontend/lib/api/domain.ts`: funções de API do domínio, incluindo `getDashboardStats`.
- `frontend/lib/api/storage-addressing.ts`: cliente de API do endereçamento de armazenamento.
- `frontend/lib/config.ts`: URLs públicas do app, API e Keycloak.
- `frontend/public/images/login-digital-archive.png`: imagem da tela de login.

Telas principais:

| Tela | Rota |
| --- | --- |
| Login | `/login` |
| Dashboard | `/dashboard` |
| Admissão | `/admissao` |
| Unidades | `/unidades` |
| Mídias | `/midias` |
| Endereçamento | `/enderecamento` |
| Eventos | `/eventos` |
| Administração | `/admin` |
| Pesquisa de descrição arquivística | `/pesquisa/descricao-arquivistica` |
| Pesquisa de instrumentos | `/pesquisa/instrumentos-pesquisa` |
| Modelos de ficha espelho | `/modelos-ficha-espelho` |

No layout autenticado, o bloco de marca à esquerda do cabeçalho/sidebar (`Thor Gestor`) aponta para `/dashboard`.

O menu `Pesquisa` usa rotas próprias sob `/pesquisa`. Essas telas são consultivas e não exibem ações de inclusão, edição ou exclusão. As rotas de gestão continuam disponíveis em seus módulos administrativos.

As telas de unidades, mídias, instrumentos de pesquisa e busca avançada de registros usam paginação de backend no formato:

```text
XX registros de YY | página B de C  Primeira Anterior 1 2 3 ... C Próxima Última
Registros por página: BB
```

Em instrumentos de pesquisa, os campos dinâmicos podem ser configurados com tipos como texto, número, data, listas, URL, arquivo, imagem, unidade de acondicionamento e mídia de armazenamento. No cadastro e edição de registros, campos de unidade e mídia usam botão de lupa para pesquisar e selecionar o registro relacionado. Nas listagens dinâmica e de busca avançada, esses campos aparecem como links de visualização para a unidade ou mídia selecionada.

Telas do módulo de admissão:

| Tela | Rota |
| --- | --- |
| Listagem de processos | `/admissao` |
| Novo processo | `/admissao/novo` |
| Visualização do processo | `/admissao/{id}` |
| Edição do processo | `/admissao/{id}/editar` |

O processo de admissão registra dados gerais do dossiê, instituição de arquivo, entidade produtora, descrição arquivística associada, responsável, status, datas, volumes e parecer final. A visualização do processo reúne abas para resumo, reuniões, acordos, sessões, SIPs, AIPs, eventos e documentos. Reuniões possuem CRUD completo com visualização dedicada, edição e exclusão.

Telas do módulo de endereçamento:

| Tela | Rota |
| --- | --- |
| Locais de Guarda | `/enderecamento/locais` |
| Zonas de Guarda | `/enderecamento/zonas` |
| Estruturas | `/enderecamento/estruturas` |
| Compartimentos | `/enderecamento/compartimentos` |
| Posições | `/enderecamento/posicoes` |
| Mapa Topográfico | `/enderecamento/mapa` |
| Movimentações | `/enderecamento/movimentacoes` |
| Ocupação | `/enderecamento/ocupacao` |

O módulo permite cadastrar a hierarquia `Local > Zona > Estrutura > Compartimento > Posição`, gerar topografia para zonas, consultar posições livres/ocupadas, atribuir posições a unidades/mídias/cópias digitais e acompanhar movimentações.

Telas de ficha espelho:

| Tela | Rota |
| --- | --- |
| Modelos de ficha espelho | `/modelos-ficha-espelho` |
| Novo modelo | `/modelos-ficha-espelho/nova` |
| Visualização do modelo | `/modelos-ficha-espelho/{id}` |
| Edição do modelo | `/modelos-ficha-espelho/{id}/editar` |
| Impressão de fichas | `/fichas-espelho/imprimir` |

Os modelos de ficha espelho definem papel, orientação, colunas, dimensões e campos exibidos. A criação e a edição mostram uma prévia dinâmica de impressão abaixo do formulário, atualizada conforme os campos do modelo mudam. A listagem possui ação de visualização, e a visualização do modelo também exibe a prévia em escala.

Rodar fora do Docker:

```bash
cd frontend
npm install
npm run dev
```

Variáveis principais:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8081
NEXT_PUBLIC_KEYCLOAK_REALM=thor
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=thor-api
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Comandos úteis:

```bash
npm run typecheck
npm run lint
npm run build
```

## Docker Compose

Subir tudo:

```bash
docker compose up --build
```

Subir apenas o frontend e dependências necessárias:

```bash
docker compose up --build frontend
```

Parar containers:

```bash
docker compose down
```

Parar e remover volumes:

```bash
docker compose down -v
```

Use `down -v` com cuidado: isso remove os dados do PostgreSQL principal, Keycloak, MongoDB, Redis, Meilisearch e pgAdmin.

Ver logs:

```bash
docker compose logs -f backend
docker compose logs -f index_worker
docker compose logs -f frontend
docker compose logs -f keycloak
```

Entrar no backend:

```bash
docker compose exec backend sh
```

Entrar no PostgreSQL:

```bash
docker compose exec postgres psql -U thor -d thor_db
```

Executar seed de unidades:

```bash
docker compose exec backend python -m app.scripts.seed_test_units
```

Executar seed de endereçamento:

```bash
docker compose exec backend python -m app.scripts.seed_storage_addressing
```

Executar seeds de instrumentos, campos e registros dinâmicos:

```bash
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

Executar seed de mídias de armazenamento:

```bash
docker compose exec backend python -m app.scripts.seed_midias_armazenamento
```

Reindexar um instrumento manualmente pela fila Celery:

```bash
docker compose exec backend python -c "from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher; InstrumentoIndexingEventPublisher.reindexar_instrumento('UUID_DO_INSTRUMENTO')"
```

## Banco de Dados e Migrations

O backend executa automaticamente:

```bash
alembic -c alembic.ini upgrade head
```

durante a subida do container.

Para rodar manualmente no container:

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

A migration inicial cria:

- tipos enum do PostgreSQL;
- tabela `unidades_acondicionamento`;
- tabela `unidades_acondicionamento_digitais`;
- tabela `midias_armazenamento`;
- tabela `copias_unidades_acondicionamento_digitais`;
- tabela `eventos_preservacao`;
- índices e constraints principais.

A migration `000002_storage_locations` adiciona:

- enums de local, zona, estrutura, compartimento e posição;
- `locais_guarda`;
- `zonas_guarda`;
- `estruturas_armazenamento`;
- `compartimentos_armazenamento`;
- `posicoes_armazenamento`;
- `movimentacoes_armazenamento`;
- `id_posicao_armazenamento` em unidades, mídias e cópias digitais.

As migrations mais recentes adicionam o módulo de admissão:

- `20260517_000016_admissao`: processos de admissão, reuniões, acordos, sessões, SIPs, vínculos SIP/AIP e eventos.
- `20260518_000017_admissao_responsavel`: nome do usuário responsável no processo.
- `20260518_000018_remove_ata_documento_reunioes`: remove o campo legado `ata_documento` de reuniões.

## Observações de Desenvolvimento

- O frontend chama a API pelo navegador usando `http://localhost:8000/api/v1`; por isso o backend libera CORS para `http://localhost:3000`.
- O backend valida tokens usando a URL interna do Keycloak (`http://keycloak:8080`) para funcionar dentro da rede Docker.
- O issuer esperado no token continua sendo a URL pública `http://localhost:8081/realms/thor`.
- Assets do frontend em `frontend/public` precisam ser copiados para a imagem final. O `frontend/Dockerfile` já faz isso.
- O script de seed usa SQL explícito para respeitar os nomes reais dos enums criados pela migration (`tipo_suporte`, `tipo_unidade`, `nivel_acesso`, `status_unidade`).
- O seed de endereçamento também usa SQL explícito para respeitar os enums PostgreSQL e é seguro para execução repetida.
- O model de mídias usa explicitamente o enum PostgreSQL `tipo_midia_armazenamento`, criado pela migration inicial.
- O worker de indexação é iniciado pelo Compose como `index_worker` e consome a fila Celery `indexacao` no Redis.
- A API não espera o Meilisearch ao cadastrar registros dinâmicos; ela salva no MongoDB e publica um evento para processamento em segundo plano.

## Validação Local

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
```

Backend:

```bash
cd backend
python -m pytest app\tests
```

Validação backend recomendada via Docker:

```bash
docker exec thor-backend pytest /app/app/tests
```

Para frontend, rode `typecheck`, `lint` e testes a partir de `frontend/` no ambiente local. A imagem `thor-frontend` é uma imagem de produção e não é a referência para validações estáticas.

Se `pytest` não estiver instalado no Python local, instale as dependências do backend antes de executar os testes.

## Problemas Comuns

### Keycloak retorna `invalid_redirect_uri`

Reaplique a configuração do client:

```bash
docker compose run --rm keycloak_config
```

Depois tente login novamente em `http://localhost:3000`.

### A imagem da tela de login não aparece no Docker

Reconstrua o frontend sem cache se necessário:

```bash
docker compose build --no-cache frontend
docker compose up --build frontend
```

Confirme que o arquivo existe na imagem:

```bash
docker run --rm --entrypoint sh thor_gestor_de_arquivos_digitais-frontend -c "ls -l /app/public/images/login-digital-archive.png"
```

### Frontend não consegue chamar a API

Verifique:

- backend rodando em `http://localhost:8000`;
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`;
- CORS do backend incluindo `http://localhost:3000`;
- token Keycloak válido na sessão do navegador.

### Reset total do ambiente local

```bash
docker compose down -v
docker compose up --build
docker compose exec backend python -m app.scripts.seed_test_units
docker compose exec backend python -m app.scripts.seed_storage_addressing
```

Isso recria containers e volumes do zero.
