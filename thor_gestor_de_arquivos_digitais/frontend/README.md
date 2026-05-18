# Frontend - Thor Gestor de Arquivos Digitais

Interface administrativa em Next.js, React, TypeScript e Tailwind CSS para operação do Thor Gestor de Arquivos Digitais.

## Responsabilidades

- Autenticar usuários via Keycloak usando OIDC Authorization Code + PKCE.
- Consumir a API FastAPI com token Bearer.
- Exibir dashboard operacional com indicadores agregados do backend.
- Gerenciar unidades de acondicionamento com busca, filtros, paginação, criação, edição, visualização e exclusão.
- Gerenciar mídias de armazenamento.
- Gerenciar endereçamento de armazenamento físico e lógico.
- Gerar topografia, consultar posições e acompanhar ocupação.
- Atribuir posições a unidades, mídias e cópias digitais.
- Gerenciar processos de admissão, reuniões, acordos, sessões de submissão, SIPs e eventos do processo.
- Gerenciar instrumentos de pesquisa, campos e registros dinâmicos.
- Consultar eventos de preservação.

## Stack

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- TanStack Query
- TanStack Table
- Radix UI
- Lucide Icons
- Zod

## Estrutura

```text
frontend/
├── app/             # Rotas, layouts e páginas
├── components/      # Componentes reutilizáveis e UI base
├── features/        # Fluxos funcionais por domínio
├── lib/             # API client, autenticação, configuração e utilitários
├── public/          # Assets estáticos
└── types/           # Contratos TypeScript do domínio
```

## Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env.local
```

Variáveis principais:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8081
NEXT_PUBLIC_KEYCLOAK_REALM=thor
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=thor-api
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Rodar Localmente

```bash
npm install
npm run dev
```

Acesse:

```text
http://localhost:3000
```

## Rodar com Docker Compose

Na raiz do repositório:

```bash
docker compose up --build frontend
```

O Compose expõe o frontend em `http://localhost:3000`, integrado ao backend em `http://localhost:8000` e ao Keycloak em `http://localhost:8081`.

## Telas Principais

- `/login`: entrada via Keycloak.
- `/auth/callback`: callback OIDC.
- `/dashboard`: tela principal do sistema com indicadores.
- `/admissao`: listagem e filtros de processos de admissão.
- `/admissao/novo`: criação de processo de admissão.
- `/admissao/[id]`: visualização do processo com abas de resumo, reuniões, acordos, sessões, SIPs, AIPs, eventos e documentos.
- `/admissao/[id]/editar`: edição do processo de admissão.
- `/unidades`: CRUD de unidades de acondicionamento.
- `/midias`: gestão de mídias.
- `/enderecamento`: módulo de endereçamento de armazenamento.
- `/instrumentos-pesquisa`: gestão de instrumentos, campos e registros dinâmicos.
- `/eventos`: consulta de eventos por unidade.
- `/admin`: área administrativa inicial.

No shell autenticado, o bloco de marca à esquerda, com ícone e texto `Thor Gestor`, aponta para `/dashboard`.

## Dashboard

O dashboard consome `GET /api/v1/dashboard`. Os cartões e o gráfico usam totais calculados no backend, não a primeira página de listagens.

Indicadores exibidos:

- total de unidades;
- AIPs digitais;
- mídias ativas;
- alertas;
- unidades por suporte físico, digital e híbrido.

## CRUD de Unidades

A tela de unidades usa paginação de backend via `limit` e `offset`, com filtros enviados à API.

O componente de paginação exibe:

```text
XX registros de YY | página B de C  Primeira Anterior 1 2 3 ... C Próxima Última
Registros por página: BB
```

Há uma paginação entre a busca e a tabela e outra abaixo da tabela.

## Admissão

O módulo de admissão está disponível em `/admissao` e usa paginação de backend com filtros por número, título, entidade produtora, tipo de processo, tipo de ingresso, suporte, status, processo ativo e intervalo de datas.

Fluxos principais:

- criar, editar, visualizar e excluir processos de admissão;
- exibir todos os campos do processo na aba `Resumo`;
- vincular uma descrição arquivística existente por consulta em pop-up;
- registrar o nome do usuário responsável;
- manter reuniões do processo com CRUD completo e tela de visualização própria;
- gerenciar acordos, sessões, SIPs e eventos relacionados ao processo.

Arquivos principais:

- `frontend/app/(app)/admissao/`
- `frontend/features/admissao/admissao-page.tsx`
- `frontend/features/admissao/processo-admissao-form.tsx`
- `frontend/features/admissao/processo-admissao-detail-page.tsx`
- `frontend/lib/api/admissao.ts`

## Endereçamento de Armazenamento

O módulo está disponível em `/enderecamento` e segue a hierarquia:

```text
Local de Guarda > Zona de Guarda > Estrutura > Compartimento > Posição
```

Telas:

- `/enderecamento/locais`: cadastro e manutenção de locais de guarda.
- `/enderecamento/zonas`: cadastro de zonas e geração de topografia.
- `/enderecamento/estruturas`: estantes, racks, servidores, NAS, buckets e volumes.
- `/enderecamento/compartimentos`: prateleiras, gavetas, slots, diretórios e partições.
- `/enderecamento/posicoes`: consulta central de posições livres, ocupadas e inativas.
- `/enderecamento/mapa`: visualização topográfica navegável por zona.
- `/enderecamento/movimentacoes`: histórico de atribuições e movimentações.
- `/enderecamento/ocupacao`: indicadores resumidos de ocupação.

Arquivos principais:

- `frontend/types/storage.ts`: tipos e enums do endereçamento.
- `frontend/lib/api/storage-addressing.ts`: chamadas para os endpoints do backend.
- `frontend/features/armazenamento/storage-components.tsx`: componentes reutilizáveis.
- `frontend/features/armazenamento/storage-pages.tsx`: telas do módulo.
- `frontend/features/armazenamento/storage-labels.ts`: labels amigáveis para enums.

Os formulários de unidade e mídia incluem seletor de posição livre. Ao salvar, o frontend chama os endpoints de atribuição e atualiza as listas relacionadas.

Para popular o módulo no Docker, execute:

```bash
docker compose exec backend python -m app.scripts.seed_storage_addressing
```

## Comandos de Qualidade

```bash
npm run typecheck
npm run lint
npm run build
```

Com Docker:

```bash
docker exec -w /app thor-frontend npm run typecheck
docker exec -w /app thor-frontend npm run lint
docker exec -w /app thor-frontend npm run build
```

Testes funcionais e E2E disponíveis:

```bash
npm run test:functional
npm run test:e2e:keycloak
```
