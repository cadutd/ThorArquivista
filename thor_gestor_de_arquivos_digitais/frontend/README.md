# Frontend - Thor Gestor de Arquivos Digitais

Interface administrativa em Next.js, React, TypeScript e Tailwind CSS para operação do Thor Gestor de Arquivos Digitais.

## Responsabilidades

- Autenticar usuários via Keycloak usando OIDC Authorization Code + PKCE.
- Consumir a API FastAPI com token Bearer.
- Exibir dashboard operacional com indicadores agregados do backend.
- Gerenciar unidades de acondicionamento com busca, filtros, paginação, criação, edição, visualização e exclusão.
- Gerenciar mídias de armazenamento.
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
- `/unidades`: CRUD de unidades de acondicionamento.
- `/midias`: gestão de mídias.
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

## Comandos de Qualidade

```bash
npm run typecheck
npm run lint
npm run build
```
