# Frontend

Interface web do `thor_pesquisador`, implementada com Next.js, React e TypeScript.

## Responsabilidades

- Login institucional com gov.br e login de desenvolvimento local.
- Dashboard inicial autenticado em `/dashboard`.
- Shell administrativo com identidade visual alinhada ao Thor Gestor.
- Instrumentos, campos dinamicos, registros e pesquisa.
- Busca avancada por instrumento com filtros, facetas, ordenacao e reindexacao manual.
- Consumo da API FastAPI.

## Identidade Visual

O frontend deve manter a mesma linguagem visual do `thor_gestor_de_arquivos_digitais`:

- paleta clara com azul institucional;
- sidebar administrativa;
- header fixo;
- cards de metricas;
- tabelas e formularios objetivos;
- dashboard como pagina inicial autenticada.

Os dois frontends importam uma copia identica de `app/thor-theme.css`, com
tokens de cor e tipografia base do Thor Gestor. As copias permitem builds Docker
independentes; ao alterar o tema, atualizar ambos os arquivos. O teste
`theme-contract.test.mjs` verifica a paridade quando executado no monorepo.
Os estilos especificos do Pesquisador continuam em `app/globals.css`, usando
14 px para controles e tabelas, 16 px para titulos de paineis e 24 px para
titulos de pagina, sem reduzir o tamanho raiz de 16 px.

A tela de login usa o asset:

```text
public/images/login_pesquisador.png
```

## Comandos

Via Docker Compose:

```bash
docker compose build frontend
docker compose up -d frontend
```

Teste funcional de contrato, executado localmente como no Thor Gestor:

```bash
npm run test:functional
npm run test:functional:report
```

Rotas principais:

- `http://localhost:3000/login`
- `http://localhost:3000/dashboard`
- `http://localhost:3000/instrumentos`
- `http://localhost:3000/instrumentos/novo`
- `http://localhost:3000/instrumentos/{id}`
- `http://localhost:3000/instrumentos/{id}/editar`
- `http://localhost:3000/pesquisa`

## CRUD de Instrumentos

O CRUD de instrumentos segue o padrao Thor CRUD Base:

- listagem paginada no servidor com `limit` e `offset`;
- busca simples por `q` com reset para a primeira pagina;
- paginas completas para criacao e edicao;
- visualizacao somente leitura em rota propria;
- formulario reutilizavel com campos obrigatorios, erros de campo e estado `Salvando...`;
- exclusao com confirmacao explicita antes de chamar a API.

## Busca Avancada

A rota `/pesquisa` consome:

- `POST /instrumentos/{id}/buscar-avancado`
- `GET /instrumentos/{id}/facetas`
- `POST /instrumentos/{id}/reindexar`

Os filtros e ordenacoes sao gerados a partir das propriedades dos campos dinamicos:

- `filtro_avancado`
- `facetavel`
- `ordenavel`

## Configuracao

A URL publica da API e definida por:

```text
NEXT_PUBLIC_API_BASE_URL
```

Em build standalone, o Dockerfile copia `public/` para garantir que imagens e assets estaticos sejam servidos pelo container.

## Kubernetes/OKD

O container deve rodar sem root e com UID arbitrario. Ajuste `PUBLIC_APP_URL`, CORS no backend e Route/Ingress conforme o ambiente.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
