# Backend - Thor Gestor de Arquivos Digitais

API do Thor Gestor de Arquivos Digitais, implementada em FastAPI com PostgreSQL, SQLAlchemy, Alembic e validação de autenticação via Keycloak.

## Responsabilidades

- Gerenciar unidades de acondicionamento físicas, digitais e híbridas.
- Gerenciar tipos e mídias de armazenamento, incluindo validade e periodicidade de checagem.
- Registrar cópias digitais associadas a unidades.
- Registrar eventos de preservação.
- Registrar eventos PREMIS próprios de mídias de armazenamento.
- Gerenciar endereçamento de armazenamento físico e lógico.
- Gerar topografia de armazenamento.
- Atribuir posições a unidades, mídias e cópias digitais.
- Registrar movimentações de armazenamento.
- Gerenciar processos de admissão de acervos, reuniões, acordos, sessões de submissão, SIPs e eventos do processo.
- Gerenciar instrumentos de pesquisa, campos configuráveis e registros dinâmicos.
- Gerenciar modelos de ficha espelho e gerar fichas para impressão.
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
| Mídias | `/midias-armazenamento` | Cadastro, filtros e paginação |
| Tipos de mídia | `/tipos-midia-armazenamento` | CRUD, ativação/desativação e parâmetros de ciclo de vida |
| Eventos de mídia | `/midias-armazenamento/{id}/eventos-preservacao` | Eventos PREMIS vinculados diretamente à mídia |
| Início de migração | `/midias-armazenamento/{id}/migrar` | Cria mídia destino e registra processo de migração |
| Migrações de mídia | `/migracoes-midias` | Consulta, atualização, etapas, relatórios e conclusão |
| Painel de integridade | `/midias-armazenamento/integridade/resumo` | Contagens por categoria para carregamento rápido do painel |
| Itens de integridade | `/midias-armazenamento/integridade/itens` | Listagem paginada por categoria de integridade |
| Verificações de integridade | `/midias-armazenamento/{id}/verificacoes-integridade` | Histórico, detalhe, registro manual e importação de relatórios |
| Cópias digitais | `/unidades-acondicionamento/{id}/copias` | Cópias por unidade |
| Eventos | `/unidades-acondicionamento/{id}/eventos-preservacao` | Eventos por unidade |
| Locais de guarda | `/locais-guarda` | CRUD lógico com exclusão por inativação |
| Zonas de guarda | `/zonas-guarda` | CRUD e geração topográfica |
| Estruturas | `/estruturas-armazenamento` | CRUD de estantes, racks, NAS, buckets etc. |
| Compartimentos | `/compartimentos-armazenamento` | CRUD de prateleiras, gavetas, slots, diretórios etc. |
| Posições | `/posicoes-armazenamento` | Consulta, posições livres/ocupadas e CRUD |
| Movimentações | `/movimentacoes-armazenamento` | Histórico de movimentação |
| Admissão | `/admissao/processos` | Processos de admissão, filtros e paginação |
| Instrumentos de pesquisa | `/instrumentos-pesquisa` | Instrumentos, campos, registros dinâmicos e busca |
| Fichas espelho | `/fichas-espelho` | Modelos e geração de fichas para impressão |

O endpoint `/dashboard` calcula os totais diretamente no banco, evitando contagens incorretas causadas por listagens paginadas.

O cadastro de mídias usa `tipo_midia_id` para vincular cada mídia a um tipo cadastrado em `/tipos-midia-armazenamento`. Cada tipo define `tempo_duracao_anos` e `periodicidade_checagem_meses`; quando `data_validade` ou `proxima_checagem_integridade` não são informadas manualmente, o serviço calcula esses valores a partir da aquisição/início de uso e da última checagem disponível.

Eventos de mídia são armazenados em tabela secundária própria (`eventos_midia_armazenamento`), separada dos eventos de unidade (`eventos_preservacao`). Criação, atualização, ativação/desativação, reativação e migração de mídia registram eventos automaticamente e preenchem `agente` com o usuário autenticado a partir dos claims Keycloak `name`, `preferred_username`, `email` ou `sub`, nessa ordem. Também é possível registrar eventos manualmente via `POST /midias-armazenamento/{id}/eventos-preservacao`.

O ciclo de migração usa a tabela `migracoes_midias`. `POST /midias-armazenamento/{id}/migrar` cria a mídia destino, vincula `midia_origem_id`, coloca origem e destino em `EM_MIGRACAO` e registra evento PREMIS `MIGRACAO_MIDIA`. As rotas de `/migracoes-midias/{id}/etapas`, `/relatorios` e `/concluir` permitem registrar execução, evidências, relatórios e conclusão. Ao concluir com sucesso, a origem fica `MIGRADA` e inativa, com `data_desativacao` e `motivo_desativacao`, e o destino passa para `ATIVA`.

As verificações de integridade são registradas em `verificacoes_integridade_midias`. O endpoint `/midias-armazenamento/integridade/resumo` retorna apenas contagens para o painel; `/midias-armazenamento/integridade/itens` lista a página atual da categoria selecionada. Registros manuais e relatórios importados atualizam a mídia, geram evento PREMIS `CHECAGEM_MIDIA` e podem criar eventos de fixidez para unidades/AIPs identificados no relatório.

As permissões do módulo de mídias são normalizadas por `20260616_000031_permissoes_gestao_midias`. As funções cadastradas são `midias`, `tipos-midia`, `migracoes-midias`, `integridade-midias` e `eventos-midia`. Os perfis padrão ficam com a seguinte matriz: `ADMIN` e `GESTOR_ARMAZENAMENTO` com acesso total; `ARQUIVISTA` com consulta; `ADMISSAO` com consulta a mídias e tipos; `CONSULTA` com consulta a mídias, migrações, integridade e eventos.

Rotas principais de instrumentos de pesquisa:

| Rota | Finalidade |
| --- | --- |
| `/instrumentos-pesquisa/{instrumento_id}/campos` | Campos dinâmicos do instrumento |
| `/instrumentos-pesquisa/{instrumento_id}/schema` | Schema usado pelo formulário e listagem dinâmica |
| `/instrumentos-pesquisa/{instrumento_id}/registros` | CRUD e listagem por cursor dos registros no MongoDB |
| `/instrumentos-pesquisa/{instrumento_id}/buscar` | Busca simples inicial por regex nos campos com `aparece_busca` |
| `/instrumentos-pesquisa/{instrumento_id}/buscar-avancado` | Busca avançada dinâmica no Meilisearch, com filtros por todos os campos do schema |
| `/instrumentos-pesquisa/{instrumento_id}/facetas` | Distribuição de facetas dos campos configurados como facetáveis |

Campos dinâmicos de instrumentos podem referenciar entidades do domínio, incluindo `UNIDADE_ACONDICIONAMENTO` e `MIDIA_ARMAZENAMENTO`. Quando esses valores são salvos como objeto `{ id, rotulo }`, a busca avançada filtra pelo identificador em `dados.<campo>.id`; para compatibilidade com registros antigos, também aceita o valor direto em `dados.<campo>`. A listagem dinâmica e a busca avançada retornam os dados brutos do MongoDB, e o frontend transforma essas referências em links de visualização.

Rotas principais de fichas espelho:

| Rota | Finalidade |
| --- | --- |
| `/fichas-espelho/modelos` | Listagem, criação e filtros de modelos |
| `/fichas-espelho/modelos/padrao` | Consulta do modelo padrão ativo |
| `/fichas-espelho/modelos/{modelo_id}` | Visualização, atualização e exclusão do modelo |
| `/fichas-espelho/gerar` | Geração dos dados de fichas para unidades selecionadas |

Endpoints de atribuição:

| Rota | Finalidade |
| --- | --- |
| `/unidades-acondicionamento/{id}/atribuir-posicao` | Move ou atribui posição a uma unidade |
| `/midias-armazenamento/{id}/atribuir-posicao` | Move ou atribui posição a uma mídia |
| `/copias-unidades-acondicionamento-digitais/{id}/atribuir-posicao` | Move ou atribui posição a uma cópia digital |

Rotas principais do módulo de admissão:

| Rota | Finalidade |
| --- | --- |
| `/admissao/processos` | CRUD de processos, filtros, paginação e auditoria de criação/alteração |
| `/admissao/processos/{processo_id}/reunioes` | Listagem e criação de reuniões do processo |
| `/admissao/reunioes/{id}` | Visualização, edição e exclusão de uma reunião |
| `/admissao/processos/{processo_id}/acordos` | Acordos de admissão do processo |
| `/admissao/acordos/{id}/ativar` | Ativação de acordo |
| `/admissao/acordos/{id}/nova-versao` | Criação de nova versão de acordo |
| `/admissao/processos/{processo_id}/sessoes` | Sessões de submissão vinculadas ao processo |
| `/admissao/sessoes/{id}/finalizar` | Finalização de sessão |
| `/admissao/processos/{processo_id}/sips` | SIPs do processo |
| `/admissao/sips/{id}/validar` | Validação de SIP |
| `/admissao/sips/{id}/rejeitar` | Rejeição de SIP |
| `/admissao/sips/{id}/transformar-aip` | Geração de vínculo SIP/AIP com unidade de acondicionamento |
| `/admissao/processos/{processo_id}/eventos` | Eventos operacionais do processo |

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

## Admissão de Acervos

O módulo de admissão registra o ciclo de entrada de acervos digitais ou físicos. O processo concentra os dados gerais da negociação e recebimento, incluindo instituição de arquivo, entidade produtora, descrição arquivística associada, usuário responsável, status, datas, volumes, restrições e parecer final.

Entidades principais:

- `ProcessoAdmissao`: dossiê principal de admissão.
- `ReuniaoAdmissao`: reuniões vinculadas ao processo, com enum `tipo_reuniao`.
- `AcordoAdmissao`: versões de acordo e regras de recebimento.
- `SessaoSubmissao`: sessões de envio/recebimento de pacotes.
- `SipAdmissao`: pacotes SIP recebidos, validados ou rejeitados.
- `RelacaoSipAip`: vínculo de SIP transformado em AIP/unidade de acondicionamento.
- `EventoAdmissao`: linha de eventos do processo.

Arquivos principais:

- `app/models/admissao.py`
- `app/schemas/admissao.py`
- `app/services/admissao_service.py`
- `app/api/v1/admissao.py`

Observações:

- `criado_por` e `atualizado_por` de processos são preenchidos a partir dos claims do usuário Keycloak.
- `nome_usuario_responsavel` é um campo operacional do processo.
- `id_descricao_arquivistica` vincula o processo a uma descrição existente.
- Reuniões não usam mais os campos legados `codigo_sip`, `responsavel_caminho` e `ata_documento`.

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

A migration `20260614_000024_tipos_midia_lifecycle` cria `tipos_midia_armazenamento`, migra os valores legados do enum de mídias para a nova tabela, substitui a coluna antiga por `tipo_midia_id` e adiciona campos de validade, checagem, capacidade e identificador físico.

A migration `20260615_000025_eventos_midia_armazenamento` cria `eventos_midia_armazenamento`, uma tabela secundária para eventos PREMIS ligados diretamente a `midias_armazenamento`.

A migration `20260615_000026_eventos_midia_premis` adiciona campos PREMIS, data do evento e vínculo entre eventos de mídia. A migration `20260615_000027_evento_reativacao_midia` adiciona o evento `REATIVACAO_MIDIA`. A migration `20260615_000028_migracao_midias` adiciona status de ciclo de vida em mídias, campos de origem/desativação e a tabela `migracoes_midias`.

A migration `20260616_000029_verificacoes_integridade_midias` adiciona verificações de integridade de mídias, contadores de AIPs, relatório JSON e vínculo com evento PREMIS. A migration `20260616_000030_indice_ultima_checagem_midias` adiciona índice para consultas por última checagem. A migration `20260616_000031_permissoes_gestao_midias` atualiza permissões e vínculos dos perfis padrão para mídias, tipos, migrações, painel de integridade e eventos próprios.

Migrations do módulo de admissão:

- `20260517_000016_admissao`: cria processos de admissão, reuniões, acordos, sessões, SIPs, relações SIP/AIP e eventos.
- `20260518_000017_admissao_responsavel`: adiciona `nome_usuario_responsavel` ao processo.
- `20260518_000018_remove_ata_documento_reunioes`: remove o campo legado `ata_documento` de reuniões.

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

Massa de mídias de armazenamento:

```bash
docker compose exec backend python -m app.scripts.seed_midias_armazenamento
```

O script é idempotente e cria/atualiza os tipos iniciais `FILESYSTEM`, `NAS`, `NFS`, `LTO`, `S3` e `CLOUD` quando necessário. Em seguida cria/atualiza 72 mídias de teste vinculadas a esses tipos, com status ativo/inativo, para validar filtros, paginação e lazy load em `/midias`.

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

Com Docker:

```bash
docker exec thor-backend pytest /app/app/tests
docker exec thor-backend pytest /app/app/tests/functional/test_crud_admissao.py /app/app/tests/integration/test_admissao_integrado.py
```

Testes focados em mídias de armazenamento:

```bash
docker exec thor-backend pytest /app/app/tests/functional/test_midias_integridade_migracao.py
docker exec thor-backend pytest /app/app/tests/integration/test_midias_integridade_migracao_integrado.py
```

O arquivo funcional cobre todos os resultados de verificação (`SUCESSO`, `FALHA`, `ALERTA`, `INCONCLUSIVO`), categorias do Painel de Integridade, importação de relatório, eventos gerados e estados de mídia permitidos/bloqueados para migração. O arquivo de integração exercita o fluxo completo com unidade/AIP, cópia digital, eventos de fixidez, painel, endereçamento, etapa, relatório e conclusão de migração.

Se `pytest` não estiver instalado no ambiente local, instale as dependências do projeto antes de executar os testes.
