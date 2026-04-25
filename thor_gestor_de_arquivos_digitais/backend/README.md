# Backend - Thor Gestor de Arquivos Digitais

API do Thor Gestor de Arquivos Digitais, implementada em FastAPI com PostgreSQL, SQLAlchemy, Alembic e validação de autenticação via Keycloak.

## Responsabilidades

- Gerenciar unidades de acondicionamento físicas, digitais e híbridas.
- Gerenciar mídias de armazenamento.
- Registrar cópias digitais associadas a unidades.
- Registrar eventos de preservação.
- Expor indicadores agregados para o dashboard.
- Validar tokens JWT emitidos pelo Keycloak nas rotas protegidas.

## Stack

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL via `psycopg`
- Pydantic Settings
- `python-jose` para validação JWT

## Estrutura

```text
backend/
├── alembic/                 # Migrações de banco
├── app/
│   ├── api/                 # Rotas FastAPI
│   ├── core/                # Configuração e infraestrutura
│   ├── db/                  # Sessão e base SQLAlchemy
│   ├── models/              # Modelos ORM
│   ├── schemas/             # Schemas Pydantic
│   ├── scripts/             # Scripts operacionais
│   ├── security/            # Dependências e validação Keycloak
│   ├── services/            # Regras de negócio
│   └── main.py              # Aplicação FastAPI
├── app/tests/               # Testes automatizados
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## Rotas Principais

Todas as rotas abaixo ficam sob `/api/v1`.

| Recurso | Rota | Observação |
| --- | --- | --- |
| Health | `/health` | Pública |
| Usuário autenticado | `/auth/me` | Protegida |
| Dashboard | `/dashboard` | Indicadores agregados |
| Unidades | `/unidades-acondicionamento` | CRUD, filtros e paginação |
| Mídias | `/midias-armazenamento` | Cadastro e listagem |
| Cópias digitais | `/unidades-acondicionamento/{id}/copias` | Cópias por unidade |
| Eventos | `/unidades-acondicionamento/{id}/eventos-preservacao` | Eventos por unidade |

O endpoint `/dashboard` calcula os totais diretamente no banco, evitando contagens incorretas causadas por listagens paginadas.

## Rodar com Docker Compose

Na raiz do repositório:

```bash
docker compose up --build
```

O container do backend:

- aguarda o PostgreSQL;
- executa `alembic -c alembic.ini upgrade head`;
- inicia `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

API local:

```text
http://localhost:8000
```

Documentação OpenAPI:

```text
http://localhost:8000/docs
```

## Rodar Fora do Docker

Pré-requisitos:

- Python 3.13 ou superior.
- PostgreSQL acessível.
- Keycloak acessível para rotas protegidas.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Variáveis de Ambiente

O Compose injeta as variáveis necessárias. Para execução local, use `backend/.env.example` como base.

Principais variáveis:

```env
app_env=dev
app_name=Thor Gestor de Arquivos Digitais
database_url=postgresql+psycopg://thor:thor@localhost:5432/thor_db
redis_url=redis://localhost:6379/0
meili_url=http://localhost:7700
meili_master_key=dev-meili-key
keycloak_url=http://localhost:8081
keycloak_internal_url=http://localhost:8081
keycloak_realm=thor
keycloak_client_id=thor-api
keycloak_verify_audience=true
cors_origins=["http://localhost:3000"]
```

Dentro do Docker, `database_url`, `redis_url`, `meili_url` e `keycloak_internal_url` usam os nomes dos serviços da rede Compose.

## Banco e Migrações

Aplicar migrações manualmente:

```bash
alembic -c alembic.ini upgrade head
```

A migration inicial cria:

- enums PostgreSQL do domínio;
- `unidades_acondicionamento`;
- `unidades_acondicionamento_digitais`;
- `midias_armazenamento`;
- `copias_unidades_acondicionamento_digitais`;
- `eventos_preservacao`;
- índices e constraints principais.

## Massa de Teste

Com os containers rodando:

```bash
docker compose exec backend python -m app.scripts.seed_test_units
```

O script é idempotente e cria/atualiza 50 unidades de teste:

- `25` unidades físicas;
- `25` unidades digitais;
- extensão digital para as unidades digitais.

## Testes e Validação

```bash
python -m pytest app\tests
python -m py_compile app\api\v1\dashboard.py app\schemas\dashboard.py app\api\v1\router.py
```

Se `pytest` não estiver instalado no ambiente local, instale as dependências do projeto antes de executar os testes.
