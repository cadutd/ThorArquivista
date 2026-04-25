# Frontend - Thor Gestor de Arquivos Digitais

Interface administrativa em Next.js, React, TypeScript, Tailwind CSS e componentes no padrão shadcn/ui.

## Requisitos

- Node.js 24.15.0 ou superior
- Backend FastAPI disponível em `http://localhost:8000`
- Keycloak disponível em `http://localhost:8081`

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

## Rodar

```bash
npm install
npm run dev
```

Acesse `http://localhost:3000`.

## Rodar com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build frontend
```

O Compose expõe o frontend em `http://localhost:3000`, integrado ao backend em `http://localhost:8000` e ao Keycloak em `http://localhost:8081`.

## Estrutura

- `app/` - rotas, layouts e páginas.
- `components/` - componentes reutilizáveis e UI base.
- `features/` - áreas funcionais da aplicação.
- `lib/` - cliente HTTP, autenticação OIDC e utilitários.
- `types/` - contratos TypeScript alinhados ao backend.
