# Workers - Thor Gestor de Arquivos Digitais

Área reservada para workers assíncronos do Thor Gestor de Arquivos Digitais.

## Estado Atual

Os workers ainda estão na fase inicial do projeto. A pasta existe para acomodar tarefas futuras de processamento em background, como indexação, validação de pacotes digitais e rotinas de preservação.

Estrutura atual:

```text
workers/
├── pyproject.toml
├── README.md
└── worker_app/
    └── tasks/
        └── index_aip.py
```

## Integrações Previstas

- Redis para filas e coordenação.
- Meilisearch para indexação e busca.
- Backend FastAPI como origem dos dados operacionais.
- PostgreSQL como persistência principal.

## Tarefas Previstas

- Indexar AIPs no Meilisearch.
- Processar validações de fixidez.
- Registrar eventos de preservação gerados por rotinas assíncronas.
- Sincronizar metadados derivados de pacotes digitais.

## Como Evoluir

Antes de ativar workers em produção, defina:

- biblioteca de fila ou executor;
- contrato de configuração por variáveis de ambiente;
- estratégia de retry;
- logs estruturados;
- testes das tarefas;
- serviço correspondente no `docker-compose.yml`.
