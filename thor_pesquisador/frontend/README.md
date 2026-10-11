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
docker compose up -d
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

## Busca Simples de Registros

A busca simples na listagem de registros aplica o termo ao enviar pelo botao
Buscar ou pela tecla Enter. Carregar mais preserva esse termo e o cursor;
editar o texto sem enviar nao altera os resultados ja pesquisados.
Enviar o campo vazio restaura a listagem geral. O teste
`npm run test:e2e:registros-busca` valida esses fluxos com a API real,
criando e removendo apenas dados proprios; requer login de desenvolvimento.

Campo vazio nao abre filtros: recarrega a listagem. Com apenas um registro,
a tabela pode continuar igual. O botao mostra o estado de carregamento;
respostas antigas nao sobrescrevem uma consulta mais recente.

## Busca Avancada

A rota `/pesquisa` consome:

- `POST /instrumentos/{id}/buscar-avancado`
- `GET /instrumentos/{id}/facetas`
- `POST /instrumentos/{id}/reindexar`

Os filtros e ordenacoes sao gerados a partir das propriedades dos campos dinamicos:

- `filtro_avancado`
- `facetavel`
- `ordenavel`

Essa rota e interna e autenticada. Portal consultivo e workflow editorial
sao entregas futuras da fase 4; nao foram implementados nesta atualizacao.

## Configuracao

A URL publica da API e definida por:

```text
NEXT_PUBLIC_API_BASE_URL
```

Em build standalone, o Dockerfile copia `public/` para garantir que imagens e assets estaticos sejam servidos pelo container.
A URL publica da API e compilada no build; alterar somente a variavel de
runtime nao substitui o rebuild com o argumento correto.

## Kubernetes/OKD

O container deve rodar sem root e com UID arbitrario. Ajuste `PUBLIC_APP_URL`, CORS no backend e Route/Ingress conforme o ambiente.

## Imagens (Fase 3)

O menu Imagens abre `/imagens`, com busca, filtros por tipo/acesso e
paginacao no servidor, acima e abaixo da tabela. Acoes usam icones com
nomes acessiveis e tooltip. Rotas completas:

- `/imagens/novo`.
- `/imagens/{id}`.
- `/imagens/{id}/editar`.
- `/instrumentos/{id}/registros/{registroId}`: metadados e aba Imagens.

O formulario compartilhado aceita URL, manifest IIIF, repositorio externo
ou arquivo para upload S3. Metadados adicionais usam JSON. O backend valida
o MIME real e tamanho; a interface apresenta erros sem descartar o formulario.

A galeria carrega apenas ao abrir a aba Imagens. O seletor de imagens existentes
usa busca e paginacao da API, sem carregar o acervo inteiro.
Cada vinculo permite legenda, principal, ordenacao e remocao confirmada.
Uma imagem pode ser reutilizada entre registros. Imagens maiores e manifests
IIIF sao buscados apenas ao abrir a previa; binarios IIIF nao sao duplicados.
Os dialogs usam foco modal nativo e fechamento por Escape.

Miniaturas de upload usam o endpoint autenticado, com cookies da sessao.
A busca mostra resumo e miniatura disponivel, sem carregar a galeria.
Permissoes sao aplicadas pelo backend; alterar/excluir exige o criador da imagem.
IIIF e URLs externas precisam permitir acesso e CORS no provedor.

### Validacao de Navegador

Para contratos, execute `npm run test:functional`. Para o fluxo completo,
inicie toda a stack com armazenamento privado, conforme o README raiz.
Com dependencias frontend e Chromium do Playwright disponiveis:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e:imagens
npm run test:e2e:registros-busca
```

O script usa `BASE_URL` (padrao localhost:3000) e `API_URL` (padrao
localhost:8000/api/v1), cria dados proprios e remove-os ao concluir.
Requer login de desenvolvimento e bucket configurado.
O teste de registros requer apenas a API ativa, sem bucket ou MinIO.
Valida API/S3 reais, upload, acesso protegido, edicao, URL/IIIF, legenda,
capa, ordem, compartilhamento e exclusao bloqueada. Somente o manifest IIIF
externo e simulado. Capturas desktop/mobile ficam no diretorio temporario do SO.

## Licenca

AGPL-3.0-or-later. Consulte `../LICENSE`.
