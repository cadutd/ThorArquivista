# Configuracao Inicial e Primeiro Administrador

Script: `backend/app/scripts/configurar_sistema.py`. Revisao: 2026-11-05.
Nao altera DNS, TLS, banco de dados, bucket ou cluster automaticamente.
Nao substitui o cadastro de credenciais/callback no gov.br nem o runbook de
deploy do README. Nenhuma senha de usuario e criada: homolog/prod usam gov.br.

## Comandos

| Comando | Efeito |
| --- | --- |
| `modelo --ambiente dev\|homolog\|prod` | Imprime JSON de exemplo, sem ler segredos atuais. |
| `gerar-config --ambiente ... --entrada arquivo.json --destino diretorio-novo` | Valida e grava arquivos privados; nao conecta em dependencias. |
| `administrador --ambiente ... --operador "Nome / ticket" --confirmar` | Apos migrations, cria o primeiro ADMIN global de forma transacional e auditada. |

Geracao/modelo usam somente a biblioteca padrao: Python 3.12 no host e
suficiente, sem instalar as dependencias backend. Tambem podem ser executados
na imagem Python/backend com diretorio de saida montado. O comando administrador
deve rodar na imagem backend da release, com ConfigMap/Secret ou env corretos.

O gerador cria `config.env`, `secrets.env` e `frontend.env`. Em dev cria tambem
`.env` compativel com o Docker Compose local. `frontend.env` informa a URL a
passar como build arg `NEXT_PUBLIC_API_BASE_URL`; nao configura o build sozinho.
`config.env`/`secrets.env` destinam-se aos generators Kustomize `envs`, nao sao
scripts para `source`/`eval`. O segredo de sessao e aleatorio e nao e impresso.

O destino precisa ser novo; o script nunca sobrescreve uma instalacao existente
nem rotaciona segredos ao reexecutar. Se uma gravacao falhar, preserve/revise
os arquivos parciais privados e escolha outro destino. Em POSIX, diretorio 0700
e arquivos 0600; no Windows, restrinja a ACL ao operador e SYSTEM. Use `.local/`
ou um cofre/workspace protegido. Nao envie JSON, envs, CPF ou secrets ao Git/CI.

## Desenvolvimento sem Gov.br

Comandos a partir de `thor_pesquisador`, usando o Compose local HTTP:

```bash
python backend/app/scripts/configurar_sistema.py gerar-config --ambiente dev --destino .local/dev-inicial
docker compose --env-file .local/dev-inicial/.env --profile storage up -d --build minio backend frontend index_worker export_worker import_worker
docker compose --env-file .local/dev-inicial/.env exec backend python -m app.scripts.init_storage
docker compose --env-file .local/dev-inicial/.env exec backend python -m app.scripts.configurar_sistema administrador --ambiente dev --local --operador "Operador local / DEV-001" --confirmar
```

Se o S3 ainda estiver iniciando, aguarde sua disponibilidade e repita somente
`init_storage`; o comando e idempotente e mantem o bucket privado.
Abra http://localhost:3000/login e clique em Entrar em desenvolvimento.
`--local` prepara a mesma conta reservada `desenvolvimento` usada pelo login
local; nao cria sessao, senha ou uma pessoa com CPF real. Exige APP_ENV=dev,
GOVBR_DEV_LOGIN=true e DEV_ADMIN_ENABLED=true. A retencao nao e ligada pelo
comando acima; depende de revisao das politicas.

Esses comandos sao para instalacao nova. Nao os execute sobre o perfil HTTPS
existente sem planejar a mudanca de origem/segredo: o novo `.env` e separado e
nao substitui o atual. Para manter HTTPS local, siga `docs/govbr_local.md` e
execute apenas `administrador --local` no backend desse perfil ja configurado.
Personalizar URLs de dev exige ajustar tambem proxy/build; o Compose base tem
hosts internos de dependencia fixos. Ele nao deve ser usado para homolog/prod.

## Homologacao e Producao

Use ambiente/dados/credenciais separados. Gere o modelo no host e preencha-o
em arquivo privado; os placeholders nao sao aceitos na geracao operacional.
O exemplo Bash aplica umask antes de criar arquivos de entrada:

```bash
umask 077
mkdir -p .local
python backend/app/scripts/configurar_sistema.py modelo --ambiente homolog > .local/entrada-homolog.json
# Preencher o JSON com dominios e credenciais reais usando editor/cofre seguro.
python backend/app/scripts/configurar_sistema.py gerar-config --ambiente homolog --entrada .local/entrada-homolog.json --destino .local/config-homolog
```

Para producao, repita com `--ambiente prod`, arquivo `entrada-prod.json` e
outro destino `config-prod`; nao reutilize os segredos da homologacao.
Opcionalmente inclua `APP_SESSION_SECRET` no JSON para reutilizar um segredo
institucional existente (>=32 caracteres), evitando rotacao nao planejada.
`--entrada -` permite receber o JSON por stdin de um cofre sem valores em args.

| Configuracao gerada | dev | homolog | prod |
| --- | --- | --- | --- |
| APP_ENV | dev | homolog | prod |
| Login/admin local | habilitados | desabilitados | desabilitados |
| AUTH_DISABLED_FOR_TESTS | false | false | false |
| Cookie Secure | conforme HTTPS da API | true | true |
| Gov.br | staging | staging | producao |
| Portal/API | HTTP local permitido | HTTPS obrigatorio | HTTPS obrigatorio |

Confirme as credenciais do ambiente antes de usar. Endpoints oficiais:
[discovery homologacao](https://sso.staging.acesso.gov.br/.well-known/openid-configuration)
e [discovery producao](https://sso.acesso.gov.br/.well-known/openid-configuration).
O script nao envia credenciais nem autentica contra o gov.br ao gerar arquivos.

Associe `config.env` e `secrets.env` ao overlay privado do ambiente, como
documentado no README. O REDIS_URL fica no Secret mesmo quando nao tem senha;
nao o duplique no ConfigMap personalizado. Use o valor de `frontend.env` no
build. Configure DNS/Routes/TLS e registre o callback gerado no gov.br.
Provisione dependencias e bucket privado pela infraestrutura institucional;
o script exige URLs PostgreSQL/Mongo autenticadas, mas nao testa sua conexao,
certificados, permissao de bucket ou validade das credenciais.

Execute primeiro o Job Alembic da mesma release, ate head. O bootstrap recusa
schema defasado e nao executa migrations nem modifica perfis automaticamente.

## Administrador com CPF Real

Crie `.local/admin.json` protegido, substituindo todos os valores de exemplo:

```json
{
  "nome": "Nome completo do administrador autorizado",
  "username": "administrador.institucional",
  "cpf": "SUBSTITUIR_POR_CPF_REAL_VALIDO",
  "email": "administrador@instituicao.gov.br"
}
```

CPF e normalizado/validado pelo schema do CRUD; nome, username e email tambem
sao validados. Nao inclua senha, `govbr_sub`, permissoes ou campos extras.
O vinculo gov.br e confirmado somente pelo login real, nao pelo bootstrap.
Sem `--arquivo`, o comando solicita os dados em terminal interativo e oculta o
CPF; em automacao use arquivo/Secret ou `--arquivo -`, nunca CPF em argumentos.

No OKD, com a configuracao real aplicada e migration concluida, crie o Secret
temporario e uma copia de `deploy/jobs/bootstrap-admin.yaml` em `.local/`.
Na copia, substitua a imagem pela mesma imagem/tag backend da release e
configure imagePullSecret se necessario. O Job reutiliza ConfigMap/Secret
da aplicacao e recebe APP_ENV deles; nao tem atalho de login ou ServiceAccount token.

```bash
set -euo pipefail
export NS=thor-pesquisador-homolog
oc -n "$NS" create secret generic thor-pesquisador-bootstrap-admin --from-file=admin.json=.local/admin.json --from-literal=operador="Nome do operador / CHG-001"
BOOTSTRAP=$(oc -n "$NS" create -f .local/bootstrap-admin.yaml -o name)
oc -n "$NS" wait --for=condition=complete "$BOOTSTRAP" --timeout=360s
oc -n "$NS" logs "$BOOTSTRAP"
# Somente apos confirmar a conclusao e guardar evidencia sem dados pessoais:
oc -n "$NS" delete secret thor-pesquisador-bootstrap-admin
```

Interrompa o procedimento se create/wait falhar; nao remova o Secret de um Job
ainda em execucao. Para prod, selecione o namespace de producao e a copia/tag
correta; os args `--ambiente $(APP_ENV)` sao expandidos pelo Kubernetes.
O Secret temporario nao faz parte do overlay nem deve permanecer como acesso
de bootstrap permanente. O Job e manual, backoffLimit=0 e TTL de 24h.
Depois, o administrador entra pelo gov.br e administra pessoas/perfis/acessos
pelos CRUDs; nenhuma sessao administrativa e fabricada pelo script.

Se a API ja estiver rodando, o mesmo comando pode ser executado no container
backend com stdin vindo do arquivo privado (Bash/runner):

```bash
oc -n "$NS" exec -i deployment/thor-pesquisador-backend -- python -m app.scripts.configurar_sistema administrador --ambiente homolog --arquivo - --operador "Nome do operador / CHG-001" --confirmar < .local/admin.json
```

Em producao troque tambem `--ambiente homolog` por `--ambiente prod`.
Quando usar `exec -it` sem --arquivo, responda ao formulario interativo; nao
misture `-t` com entrada de arquivo. Nao habilite flags dev para executar o script.

## Garantias e Limites

- APP_ENV precisa coincidir com --ambiente; Settings e endpoints gov.br sao
  revalidados antes da gravacao. Local somente em dev com opt-in explicito.
- Lock administrativo existente serializa o bootstrap com alteracoes de
  concessoes. Usuario e concessao ADMIN global sao gravados na mesma transacao
  que o evento CONFIGURACAO_INICIAL_ADMIN na auditoria existente.
- O evento identifica o operador de infraestrutura informado, nao finge uma
  sessao do usuario novo. Logs/resultados nao imprimem CPF, email ou segredo.
- Reexecucao para a mesma conta ja ADMIN retorna ja_configurado, sem duplicar
  auditoria/concessao nem alterar nome/email/CPF. Conta existente consistente
  pode receber o primeiro ADMIN se ainda nao houver administrador ativo.
- Outro administrador ativo impede nova promocao por este script; use o CRUD.
  Usuarios bloqueados/excluidos, colisao CPF/username/email, vinculo inconsistente
  ou perfil ADMIN inativo/alterado sao recusados, sem reparo silencioso.
- Nao redefine senha, nao reativa contas, nao emite sessao, nao cria massa,
  nao publica instrumentos/registros, nao executa retencao e nao apaga historico.
- O script nao e API publica. Restrinja exec/Jobs, cofre e credenciais de banco
  aos operadores autorizados. Nao o execute automaticamente a cada startup.

## Testes

Somente bancos isolados do Compose de testes:

```bash
docker compose -f docker-compose.test.yml up -d backend
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests/test_configuracao_inicial.py app/tests/functional/test_bootstrap_inicial.py
```

Validacao em Docker: 49 testes focados aprovados, incluindo configuracao
dos tres ambientes, arquivos privados, idempotencia, guardas, conflitos e
rollback se a auditoria falhar. Regressao completa: 732 testes backend e 76
contratos frontend aprovados, build backend e smoke sem root/read-only.
O .env tambem foi validado em processo real de container com caracteres especiais
sinteticos. Overlays homolog/prod e Job foram validados localmente, sem aplicar
recursos. Nao equivale a rollout no cluster ou login gov.br real.
