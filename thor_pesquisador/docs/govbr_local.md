# Gov.br no Docker Local

## Enderecos

- Aplicacao: https://localhost:8443
- Callback: https://localhost:8443/api/v1/auth/govbr/callback

O perfil usa o mesmo dominio/origem para frontend e API. Um proxy Caddy recebe
HTTPS em 127.0.0.1:8443 e encaminha /api/* para o backend, sem remover o prefixo.
As demais rotas seguem para o frontend. As portas auxiliares do Compose
tambem ficam restritas ao loopback; este ambiente nao e para acesso pela rede.

Esta URL deve ser cadastrada **exatamente** na credencial do provedor antes
de tentar login real. Ela substitui a URL externa anteriormente informada;
criar um endpoint no Docker nao altera o cadastro mantido pelo gov.br.
Se o cadastro institucional nao aceitar localhost, sera necessario um dominio
de desenvolvimento autorizado e adaptar proxy, callback e origem.

O roteiro oficial exige HTTPS e redirect_uri cadastrada:
[integracao gov.br](https://acesso.gov.br/roteiro-tecnico/iniciarintegracao.html).
O padrao deste perfil usa os endpoints de **homologacao** em
sso.staging.acesso.gov.br. As credenciais precisam pertencer a esse ambiente.
Nao foi possivel confirmar o ambiente de emissao apenas pelo identificador
informado. Para producao, usar os endpoints e a credencial de producao
autorizados pela instituicao; nao usar este perfil local.

## Configuracao

.env.example documenta os nomes das variaveis sem credenciais reais.
No computador de desenvolvimento:

- .env: client_id, endpoints, origem/callback e segredo aleatorio de sessao.
- .secrets/govbr_client_secret.txt: segredo do cliente, montado somente no
  backend em /run/secrets/govbr_client_secret como Docker secret.
- .local/govbr-root.crt: certificado publico da CA de desenvolvimento.

Esses arquivos sao ignorados pelo Git. Nunca incluir valores secretos em
issues, commits, capturas ou logs. No Windows, os arquivos locais de
credenciais devem ser acessiveis apenas ao usuario e ao SYSTEM.
O backend aceita GOVBR_CLIENT_SECRET_FILE ou GOVBR_CLIENT_SECRET; o arquivo
tem prioridade e valores secretos sao mascarados na representacao de Settings.
Rotacionar no provedor qualquer segredo compartilhado em conversa.

## Inicializacao

Executar a partir de thor_pesquisador, com Docker Desktop iniciado:

```powershell
docker compose -f docker-compose.yml -f docker-compose.govbr-local.yml build backend frontend
docker compose -f docker-compose.yml -f docker-compose.govbr-local.yml --profile storage up -d minio backend frontend govbr_https
```

Usar sempre os dois arquivos para operar esse perfil. O build e necessario
porque a origem da API e incorporada no frontend pelo Next.js. No perfil
HTTPS, acessar o sistema por https://localhost:8443, nao por HTTP na porta 3000.
Nao executar docker compose config sem --quiet em ambientes com segredos,
pois a configuracao expandida pode incluir o segredo de sessao do .env.

Para executar os processamentos em segundo plano, construir/subir tambem
index_worker, export_worker e import_worker usando os mesmos arquivos.
O agendador de retencao nao e iniciado pelo comando acima.

## Certificado Local

Caddy utiliza uma CA interna persistida em volume Docker e emite o certificado
de localhost. Ela nao e uma CA publica. Sua chave privada permanece no volume;
nao exportar root.key. O certificado publico ja exportado nesta configuracao
esta em .local/govbr-root.crt. Para exportar novamente:

```powershell
docker compose -f docker-compose.yml -f docker-compose.govbr-local.yml cp govbr_https:/data/caddy/pki/authorities/local/root.crt .local/govbr-root.crt
```

O Windows/navegador precisa confiar nessa CA para abrir o sistema sem alerta.
Nesta maquina a instalacao foi autorizada explicitamente e realizada apenas
em CurrentUser/Root; LocalMachine nao foi alterado. Em outro computador, depois
de conferir a origem do certificado, a instalacao opcional no usuario atual e:

```powershell
certutil -user -addstore Root .local/govbr-root.crt
```

Isso confia em certificados emitidos por esta CA local; proteger seu volume
e remover essa confianca ao desativar o ambiente. Alguns navegadores gerenciam
um repositorio proprio. Nao desabilitar validacao TLS global nem usar essa CA
em producao. O volume da CA precisa persistir; sua recriacao altera a raiz.
Referencia: [HTTPS local do Caddy](https://caddyserver.com/docs/automatic-https#local-https).

## Comportamento

O botao Entrar com GOV.BR usa Authorization Code, PKCE/S256, state e nonce.
Somente o backend troca o codigo pelo token via Basic e valida assinatura
RS256/JWKS, emissor, audiencia e expiracao. O segredo e o ID token nao sao
enviados ao frontend. Cookies de autenticacao/sessao usam Secure, HttpOnly
e SameSite=Lax. Credenciais nao concedem perfis ou permissoes automaticamente.
O vinculo continua pelo CPF; usuarios sem cadastro recebem somente a sessao
consultiva conforme a politica existente.

O login de desenvolvimento foi mantido para recuperacao local enquanto o
callback estiver pendente de cadastro. Ele nao pode ser habilitado em
homologacao/producao. As validacoes de seguranca desses ambientes permanecem.
Logout encerra a sessao local do Thor, nao a sessao global do gov.br.
Erros de transporte/provedor sao genericos e nao retornam tokens ou respostas
brutas. Logs de acesso/erro do proxy local sao descartados para nao registrar
codigos de autorizacao em query strings; a API mantem telemetria sanitizada.

## Verificacao

Os testes de backend usam tokens assinados e respostas controladas, nunca
enviam credenciais reais. A suite cobre Basic, PKCE, callback HTTPS, cookies,
nonce, emissor, assinatura, audiencia, expiracao, indisponibilidade e erros.

```powershell
docker compose -f docker-compose.test.yml up -d backend minio storage_init
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider
```

Teste do navegador no perfil local, interceptando o provedor:

```powershell
$env:THOR_E2E_LOCAL_GOVBR="true"
$env:THOR_E2E_TRUSTED_CA="true"
node frontend/tests/e2e/govbr-local.smoke.cjs
```

PLAYWRIGHT_MODULE pode apontar para o Playwright ja instalado no monorepo.
O teste valida a cadeia TLS com a CA exportada. THOR_E2E_TRUSTED_CA=true exige
tambem a confianca normal do navegador, sem excecao TLS. Em ambientes de
teste sem confianca instalada, a ausencia dessa flag permite uma excecao
restrita ao contexto descartavel do navegador automatizado; o teste nao
altera Windows nem o navegador do usuario. O login de desenvolvimento gera
apenas uma sessao de teste local e a encerra ao final.

Validacao em 2026-11-04: 683 testes backend e 76 contratos frontend passaram
no Docker; builds e fluxo em navegador com TLS normal tambem aprovados.

Esses testes nao equivalem a homologacao com o provedor real. Cadastro do
callback, confianca no certificado e confirmacao do ambiente da credencial
sao pendencias externas antes de testar autenticacao real.
