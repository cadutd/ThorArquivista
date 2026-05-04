# Backend - Thor Gestor de Arquivos Digitais

API do Thor Gestor de Arquivos Digitais, implementada em FastAPI com PostgreSQL, SQLAlchemy, Alembic e validação de autenticação via Keycloak.

## Responsabilidades

- Gerenciar unidades de acondicionamento físicas, digitais e híbridas.
- Gerenciar mídias de armazenamento.
- Registrar cópias digitais associadas a unidades.
- Registrar eventos de preservação.
- Gerenciar endereçamento de armazenamento físico e lógico.
- Gerar topografia de armazenamento.
- Atribuir posições a unidades, mídias e cópias digitais.
- Registrar movimentações de armazenamento.
- Gerenciar instrumentos de pesquisa, campos configuráveis e registros dinâmicos.
- Executar busca simples inicial nos registros dinâmicos.
- Publicar eventos de indexação assíncrona para o worker Celery.
- Expor indicadores agregados para o dashboard.
- Validar tokens JWT emitidos pelo Keycloak nas rotas protegidas.

## Stack

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL via `psycopg`
- MongoDB via `pymongo`
- Redis e Celery
- Meilisearch
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
│   ├── tasks/               # Tarefas Celery
│   ├── worker.py            # Aplicação Celery
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
| Locais de guarda | `/locais-guarda` | CRUD lógico com exclusão por inativação |
| Zonas de guarda | `/zonas-guarda` | CRUD e geração topográfica |
| Estruturas | `/estruturas-armazenamento` | CRUD de estantes, racks, NAS, buckets etc. |
| Compartimentos | `/compartimentos-armazenamento` | CRUD de prateleiras, gavetas, slots, diretórios etc. |
| Posições | `/posicoes-armazenamento` | Consulta, posições livres/ocupadas e CRUD |
| Movimentações | `/movimentacoes-armazenamento` | Histórico de movimentação |
| Instrumentos de pesquisa | `/instrumentos-pesquisa` | Instrumentos, campos, registros dinâmicos e busca |

O endpoint `/dashboard` calcula os totais diretamente no banco, evitando contagens incorretas causadas por listagens paginadas.

Rotas principais de instrumentos de pesquisa:

| Rota | Finalidade |
| --- | --- |
| `/instrumentos-pesquisa/{instrumento_id}/campos` | Campos dinâmicos do instrumento |
| `/instrumentos-pesquisa/{instrumento_id}/schema` | Schema usado pelo formulário e listagem dinâmica |
| `/instrumentos-pesquisa/{instrumento_id}/registros` | CRUD e listagem por cursor dos registros no MongoDB |
| `/instrumentos-pesquisa/{instrumento_id}/buscar` | Busca simples inicial por regex nos campos com `aparece_busca` |

Endpoints de atribuição:

| Rota | Finalidade |
| --- | --- |
| `/unidades-acondicionamento/{id}/atribuir-posicao` | Move ou atribui posição a uma unidade |
| `/midias-armazenamento/{id}/atribuir-posicao` | Move ou atribui posição a uma mídia |
| `/copias-unidades-acondicionamento-digitais/{id}/atribuir-posicao` | Move ou atribui posição a uma cópia digital |

## Endereçamento de Armazenamento

O modelo representa armazenamento físico e lógico na hierarquia:

```text
Local de Guarda
└── Zona de Guarda
    └── Estrutura de Armazenamento
        └── Compartimento de Armazenamento
            └── Posição de Armazenamento
```

Arquivos principais:

- `app/models/armazenamento.py`
- `app/schemas/armazenamento.py`
- `app/services/armazenamento_service.py`
- `app/api/v1/armazenamento.py`

Regras implementadas:

- códigos únicos no escopo definido;
- inativação lógica em exclusões;
- geração topográfica transacional;
- validação de posição ativa;
- validação de capacidade disponível;
- liberação da posição anterior quando um objeto é movido;
- registro de movimentação a cada atribuição;
- consultas de posições livres, ocupadas, localização de unidade e ocupação por local/zona.

## Rodar com Docker Compose

Na raiz do repositório:

```bash
docker compose up --build
```

O container do backend:

- aguarda o PostgreSQL;
- executa `alembic -c alembic.ini upgrade head`;
- inicia `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

O serviço `index_worker` usa a mesma imagem do backend e inicia:

```bash
celery -A app.worker.celery_app worker --loglevel=INFO --queues=indexacao --concurrency=1
```

Ele consome eventos no Redis e indexa registros dinâmicos no Meilisearch em segundo plano.

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
- MongoDB acessível para registros dinâmicos.
- Redis acessível para filas Celery.
- Meilisearch acessível para indexação e busca dedicada.
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
mongodb_url=mongodb://localhost:27017/thor_db
meili_url=http://localhost:7700
meili_master_key=dev-meili-key
keycloak_url=http://localhost:8081
keycloak_internal_url=http://localhost:8081
keycloak_realm=thor
keycloak_client_id=thor-api
keycloak_verify_audience=true
cors_origins=["http://localhost:3000"]
```

Dentro do Docker, `database_url`, `redis_url`, `mongodb_url`, `meili_url` e `keycloak_internal_url` usam os nomes dos serviços da rede Compose.

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

A migration `000002_storage_locations` adiciona:

- enums de endereçamento;
- `locais_guarda`;
- `zonas_guarda`;
- `estruturas_armazenamento`;
- `compartimentos_armazenamento`;
- `posicoes_armazenamento`;
- `movimentacoes_armazenamento`;
- vínculo opcional `id_posicao_armazenamento` em unidades, mídias e cópias digitais.

## Massa de Teste

Com os containers rodando:

```bash
docker compose exec backend python -m app.scripts.seed_test_units
```

O script é idempotente e cria/atualiza 50 unidades de teste:

- `25` unidades físicas;
- `25` unidades digitais;
- extensão digital para as unidades digitais.

Massa de endereçamento:

```bash
docker compose exec backend python -m app.scripts.seed_storage_addressing
```

O script é idempotente e cria/atualiza:

- `1` local de guarda: `TEST-DEP-01`;
- `2` zonas: `ZT01` e `ZT02`;
- `20` estantes por zona;
- `5` prateleiras por estante;
- `10` posições por prateleira;
- `2.000` posições no total.

Conferência rápida:

```bash
docker compose exec postgres psql -U thor -d thor_db -c "select lg.codigo as local, count(distinct zg.id) zonas, count(distinct ea.id) estruturas, count(distinct ca.id) compartimentos, count(pa.id) posicoes from locais_guarda lg join zonas_guarda zg on zg.id_local_guarda = lg.id join estruturas_armazenamento ea on ea.id_zona_guarda = zg.id join compartimentos_armazenamento ca on ca.id_estrutura_armazenamento = ea.id join posicoes_armazenamento pa on pa.id_compartimento_armazenamento = ca.id where lg.codigo = 'TEST-DEP-01' group by lg.codigo;"
```

Massa de instrumentos de pesquisa:

```bash
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

Os scripts criam instrumentos, campos configuráveis e registros dinâmicos. O seed de registros grava no MongoDB e publica eventos Celery para o `index_worker` indexar os documentos no Meilisearch.

Reindexar manualmente um instrumento:

```bash
docker compose exec backend python -c "from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher; InstrumentoIndexingEventPublisher.reindexar_instrumento('UUID_DO_INSTRUMENTO')"
```

Eventos de indexação suportados:

- `REGISTRO_CRIADO`
- `REGISTRO_ATUALIZADO`
- `REGISTRO_EXCLUIDO`
- `REINDEXAR_INSTRUMENTO`

## Testes e Validação

```bash
python -m pytest app\tests
python -m py_compile app\api\v1\dashboard.py app\api\v1\armazenamento.py app\schemas\armazenamento.py app\services\armazenamento_service.py app\api\v1\router.py
```

Se `pytest` não estiver instalado no ambiente local, instale as dependências do projeto antes de executar os testes.
