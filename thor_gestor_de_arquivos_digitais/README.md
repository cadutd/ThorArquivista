# Thor Gestor de Arquivos Digitais

Manual de desenvolvimento do sistema Thor, uma aplicação para gestão de unidades de acondicionamento físicas e digitais, endereçamento de armazenamento, mídias, cópias digitais e eventos de preservação.

## Visão Geral

O projeto é dividido em duas aplicações principais:

- `backend/`: API em FastAPI responsável pelas regras de negócio, persistência, validação de tokens Keycloak e acesso ao PostgreSQL.
- `frontend/`: interface administrativa em Next.js, React, TypeScript e Tailwind CSS.
- `workers/`: área reservada para tarefas assíncronas futuras, como indexação e validações de preservação.

Serviços auxiliares sobem via Docker Compose:

- PostgreSQL principal: banco da aplicação.
- PostgreSQL do Keycloak: banco separado para identidade.
- Keycloak: provedor OIDC usado no login do frontend e na validação de tokens do backend.
- Redis: infraestrutura de cache/fila para uso operacional.
- Meilisearch: motor de busca local.
- pgAdmin: administração visual do PostgreSQL.

## Arquitetura

Fluxo principal:

1. O usuário acessa o frontend em `http://localhost:3000`.
2. Ao clicar em `Entrar com Keycloak`, o frontend inicia o fluxo OIDC Authorization Code + PKCE no Keycloak em `http://localhost:8081`.
3. O Keycloak autentica o usuário e redireciona para `http://localhost:3000/auth/callback`.
4. O frontend troca o `code` por tokens e guarda a sessão no navegador.
5. Chamadas ao backend usam `Authorization: Bearer <access_token>`.
6. O backend valida o JWT usando o JWKS do Keycloak pela URL interna Docker `http://keycloak:8080`.
7. A API persiste e consulta dados no PostgreSQL em `postgres:5432`.

URLs locais principais:

| Serviço | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| Backend docs | `http://localhost:8000/docs` |
| Keycloak | `http://localhost:8081` |
| pgAdmin | `http://localhost:5050` |
| Meilisearch | `http://localhost:7700` |

## Estrutura do Repositório

```text
.
├── backend/              # FastAPI, SQLAlchemy, Alembic e scripts operacionais
├── frontend/             # Next.js, React, Tailwind CSS e autenticação OIDC
├── workers/              # Workers assíncronos planejados
├── infra/keycloak/       # Scripts de configuração automática do Keycloak
├── pgadmin/provisioning/ # Configuração automática de servidores no pgAdmin
├── docker-compose.yml    # Stack local completa
└── README.md             # Este manual
```

## Requisitos

Para rodar com Docker:

- Docker Desktop ou Docker Engine com Compose.
- Portas livres: `3000`, `5050`, `5432`, `6379`, `7700`, `8000`, `8081`.

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
- sobe PostgreSQL, Redis, Meilisearch, Keycloak e pgAdmin;
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
- Porta: `5432`

## Configuração do Keycloak

O serviço `keycloak_config` usa o script:

```text
infra/keycloak/configure-client.sh
```

Ele autentica no Keycloak usando o admin local e atualiza o client `thor-api` no realm `thor` com:

- `redirectUris`: `http://localhost:3000/auth/callback` e `http://localhost:3000/*`
- `webOrigins`: `http://localhost:3000`
- fluxo padrão OIDC habilitado;
- client público habilitado.

Se o Keycloak já estava rodando e você quiser reaplicar a configuração:

```bash
docker compose run --rm keycloak_config
```

## Massa de Teste

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

## Backend

Stack principal:

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL via `psycopg`
- Keycloak JWT validation via `python-jose`
- Pydantic Settings

Arquivos importantes:

- `backend/app/main.py`: cria a aplicação FastAPI, adiciona CORS e registra as rotas.
- `backend/app/api/v1/router.py`: agrega as rotas públicas e protegidas.
- `backend/app/api/v1/dashboard.py`: expõe indicadores agregados do dashboard.
- `backend/app/api/v1/armazenamento.py`: expõe CRUD, topografia, atribuição de posições e movimentações de armazenamento.
- `backend/app/models/armazenamento.py`: models do endereçamento de armazenamento.
- `backend/app/services/armazenamento_service.py`: regras de negócio de ocupação, capacidade, movimentação e geração topográfica.
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
| `/midias-armazenamento` | Cadastro e listagem de mídias |
| `/unidades-acondicionamento/{id}/copias` | Cópias digitais de uma unidade |
| `/unidades-acondicionamento/{id}/eventos-preservacao` | Eventos de preservação de uma unidade |
| `/locais-guarda` | CRUD de locais de guarda |
| `/zonas-guarda` | CRUD de zonas e geração de topografia |
| `/estruturas-armazenamento` | CRUD de estruturas |
| `/compartimentos-armazenamento` | CRUD de compartimentos |
| `/posicoes-armazenamento` | Consulta e CRUD de posições |
| `/movimentacoes-armazenamento` | Histórico de movimentações |

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
| Unidades | `/unidades` |
| Mídias | `/midias` |
| Endereçamento | `/enderecamento` |
| Eventos | `/eventos` |
| Administração | `/admin` |

No layout autenticado, o bloco de marca à esquerda do cabeçalho/sidebar (`Thor Gestor`) aponta para `/dashboard`.

O CRUD de unidades usa paginação de backend no formato:

```text
XX registros de YY | página B de C  Primeira Anterior 1 2 3 ... C Próxima Última
Registros por página: BB
```

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

Use `down -v` com cuidado: isso remove os dados do PostgreSQL principal, Keycloak, Redis, Meilisearch e pgAdmin.

Ver logs:

```bash
docker compose logs -f backend
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

## Observações de Desenvolvimento

- O frontend chama a API pelo navegador usando `http://localhost:8000/api/v1`; por isso o backend libera CORS para `http://localhost:3000`.
- O backend valida tokens usando a URL interna do Keycloak (`http://keycloak:8080`) para funcionar dentro da rede Docker.
- O issuer esperado no token continua sendo a URL pública `http://localhost:8081/realms/thor`.
- Assets do frontend em `frontend/public` precisam ser copiados para a imagem final. O `frontend/Dockerfile` já faz isso.
- O script de seed usa SQL explícito para respeitar os nomes reais dos enums criados pela migration (`tipo_suporte`, `tipo_unidade`, `nivel_acesso`, `status_unidade`).
- O seed de endereçamento também usa SQL explícito para respeitar os enums PostgreSQL e é seguro para execução repetida.
- Os workers ainda não são iniciados pelo Compose; `workers/` está reservado para a fase de tarefas assíncronas.

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
