# Workers - Thor Gestor de Arquivos Digitais

Documentação dos workers assíncronos do Thor.

## Estado Atual

O worker ativo é o serviço `index_worker` definido em `docker-compose.yml`.
Ele usa a mesma imagem do backend e executa Celery:

```bash
celery -A app.worker.celery_app worker --loglevel=INFO --queues=indexacao --concurrency=1
```

## Arquitetura

Fluxo de indexação de registros dinâmicos:

1. A API salva o registro do instrumento de pesquisa no MongoDB.
2. A API publica um evento Celery no Redis.
3. O `index_worker` consome a fila `indexacao`.
4. O worker lê o documento no MongoDB.
5. O worker cria ou atualiza o documento no Meilisearch.

Esse fluxo evita que o cadastro de registros dependa diretamente do tempo de resposta do motor de busca.

## Eventos

Eventos suportados:

- `REGISTRO_CRIADO`
- `REGISTRO_ATUALIZADO`
- `REGISTRO_EXCLUIDO`
- `REINDEXAR_INSTRUMENTO`

Publicador:

```text
backend/app/services/instrumento_indexing_events.py
```

Tarefas:

```text
backend/app/tasks/instrumento_indexacao.py
```

Aplicação Celery:

```text
backend/app/worker.py
```

## Meilisearch

Cada instrumento de pesquisa usa um índice próprio:

```text
instrumento_{instrumento_id}
```

Documento indexável:

```json
{
  "id": "uuid",
  "instrumento_id": "uuid",
  "schema_version": 1,
  "titulo": "Titulo do registro",
  "texto_geral": "Texto consolidado para busca",
  "dados": {},
  "unidade_acondicionamento_ids": [],
  "registro_descritivo_ids": [],
  "status": "ATIVO",
  "criado_em": "2026-04-28T00:00:00Z"
}
```

## Comandos

Subir worker e dependências:

```bash
docker compose up -d redis meilisearch mongo backend index_worker
```

Ver logs:

```bash
docker compose logs -f index_worker
```

Reindexar um instrumento:

```bash
docker compose exec backend python -c "from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher; InstrumentoIndexingEventPublisher.reindexar_instrumento('UUID_DO_INSTRUMENTO')"
```

Reexecutar a massa de registros e publicar eventos de indexação:

```bash
docker compose exec backend python -m app.scripts.seed_instrumento_registros
```

## Observações

- Redis é o broker e backend de resultado do Celery.
- Meilisearch continua sendo o motor de busca dedicado.
- O diretório `workers/worker_app/` é legado e permanece apenas como placeholder histórico; o worker atual vive no pacote `backend/app`.
