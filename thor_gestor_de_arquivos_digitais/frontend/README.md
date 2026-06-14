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
- Disponibilizar telas consultivas de pesquisa sem ações de inclusão, edição ou exclusão.
- Gerenciar modelos de ficha espelho e pré-visualizar o layout de impressão.
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
- `/pesquisa/descricao-arquivistica`: consulta de descrições arquivísticas sem ações de gestão.
- `/pesquisa/instrumentos-pesquisa`: consulta de instrumentos e registros dinâmicos sem ações de gestão.
- `/modelos-ficha-espelho`: gestão de modelos de ficha espelho.
- `/modelos-ficha-espelho/[id]`: visualização do modelo com prévia de impressão.
- `/modelos-ficha-espelho/[id]/editar`: edição do modelo com prévia dinâmica.
- `/modelos-ficha-espelho/nova`: criação de modelo com prévia dinâmica.
- `/fichas-espelho/imprimir`: impressão das fichas geradas.
- `/eventos`: consulta de eventos por unidade.
- `/admin`: área administrativa inicial.

No shell autenticado, o bloco de marca à esquerda, com ícone e texto `Thor Gestor`, aponta para `/dashboard`.

O grupo `Pesquisa` no menu lateral aponta para rotas sob `/pesquisa`. Essas telas são específicas para perfis de consulta e ocultam botões de criação, edição, exclusão, cadastro dinâmico e associação de unidades.

## Instrumentos de Pesquisa

O módulo de instrumentos permite configurar campos dinâmicos por instrumento e usar esses campos no cadastro, listagem, busca simples e busca avançada de registros.

Fluxos principais:

- no cadastro de instrumento novo, após salvar os metadados básicos, a aba `Campos do Instrumento` fica disponível para cadastrar campos dinâmicos;
- campos dinâmicos podem usar tipos como texto, número, data, booleano, listas, URL, arquivo, imagem, unidade de acondicionamento e mídia de armazenamento;
- campos do tipo `Unidade de Acondicionamento` e `Mídia de Armazenamento` usam botão de lupa no cadastro/edição de registros para pesquisar e selecionar a entidade relacionada;
- a listagem dinâmica e a busca avançada exibem unidade e mídia como links para `/unidades/{id}` e `/midias/{id}`;
- a função `Busca por metadado` na busca avançada mostra todos os campos dinâmicos disponíveis no schema do instrumento, usando controles compatíveis com o tipo de campo.

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

## Ficha Espelho

O módulo de modelos de ficha espelho está disponível em `/modelos-ficha-espelho`. Ele permite configurar:

- nome, descrição e status do modelo;
- papel (`A4` ou `Carta`);
- orientação (`Retrato` ou `Paisagem`);
- número de colunas por página;
- largura e altura da ficha;
- campos exibidos na impressão.

Fluxos principais:

- a listagem possui ações de visualizar, editar e excluir;
- a visualização em `/modelos-ficha-espelho/[id]` mostra os metadados e uma prévia em escala;
- a criação e a edição exibem a prévia abaixo do formulário;
- a prévia é dinâmica e acompanha mudanças em campos, dimensões, papel, orientação e colunas;
- a impressão final usa `/fichas-espelho/imprimir?modeloId=...&unidadeIds=...`.

Arquivos principais:

- `frontend/features/ficha-espelho/modelos-ficha-table.tsx`
- `frontend/features/ficha-espelho/modelo-ficha-form.tsx`
- `frontend/features/ficha-espelho/modelo-ficha-view-page.tsx`
- `frontend/features/ficha-espelho/ficha-espelho-preview.tsx`
- `frontend/app/(app)/fichas-espelho/imprimir/page.tsx`

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
