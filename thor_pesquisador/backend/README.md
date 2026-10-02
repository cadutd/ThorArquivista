# Backend

API do `thor_pesquisador`, implementada com FastAPI.

## Responsabilidades

- Autenticacao gov.br e sessao local da aplicacao.
- Usuarios e sessoes.
- Instrumentos e campos dinamicos em PostgreSQL.
- Registros dinamicos em MongoDB.
- Dashboard administrativo.
- Validacao dos registros conforme schema do instrumento.
- Health check publico.

## Banco de Dados

PostgreSQL e usado para dados governados e relacionais:

- usuarios;
- sessoes;
- instrumentos;
- campos;
- metadados administrativos.

MongoDB e usado como fonte canonica dos registros dinamicos. Consultas operacionais devem usar indices e paginacao por cursor sempre que possivel.

## Comandos

Com o Docker Compose ativo:

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
docker compose exec backend python -m pytest app/tests
```

Health:

```bash
curl http://localhost:8000/api/v1/health
```

## Massas de Teste

Os scripts ficam em `app/scripts/` e sao idempotentes:

```bash
docker compose exec backend python -m app.scripts.seed_instrumentos_pesquisa
docker compose exec backend python -m app.scripts.seed_instrumento_campos
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

A carga cria instrumentos e campos no PostgreSQL e registros dinamicos no MongoDB.

## Testes Funcionais

```bash
docker compose exec backend python -m pytest app/tests/functional
```

Para gerar JUnit XML e relatorios Markdown/HTML consolidados com o frontend, execute na raiz do projeto:

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

## Kubernetes/OKD

O backend deve rodar sem root, com configuracao por Secret/ConfigMap e sem depender de escrita persistente no filesystem do container. As migrations Alembic devem ser executadas de forma controlada antes do rollout ou por procedimento operacional documentado.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
