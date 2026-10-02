# Frontend

Interface web do `thor_pesquisador`, implementada com Next.js, React e TypeScript.

## Responsabilidades

- Login institucional com gov.br e login de desenvolvimento local.
- Dashboard inicial autenticado em `/dashboard`.
- Shell administrativo com identidade visual alinhada ao Thor Gestor.
- Instrumentos, campos dinamicos, registros e pesquisa.
- Consumo da API FastAPI.

## Identidade Visual

O frontend deve manter a mesma linguagem visual do `thor_gestor_de_arquivos_digitais`:

- paleta clara com azul institucional;
- sidebar administrativa;
- header fixo;
- cards de metricas;
- tabelas e formularios objetivos;
- dashboard como pagina inicial autenticada.

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
- `http://localhost:3000/pesquisa`

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
