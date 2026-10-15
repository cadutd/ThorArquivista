# Administracao de Acessos

Atualizacao de 2026-10-15, adaptada da organizacao administrativa do Thor Gestor
de Arquivos Digitais, sem modificar o projeto de referencia.

## Navegacao

Menu Administracao, com entradas visiveis conforme a permissao Consultar de cada modulo:

- Gestao de Usuarios: `/usuarios`, cadastro completo e consulta em popup;
  `/usuarios/novo` e `/usuarios/{id}/editar` sao paginas proprias.
- Perfis: `/perfis`, consulta em popup, criacao/edicao em paginas proprias e
  exclusao/desativacao confirmada no popup. ADMIN permanece protegido.
- Permissoes: `/permissoes`, catalogo pesquisavel com visualizacao somente leitura.
- Concessoes de acesso: `/acessos`, CRUD global ou por instrumento.

Nao ha menus Eventos ou Administracao Geral. O menu tambem pode ser aberto
no cabecalho em telas pequenas; o dialog reutiliza foco modal e Escape.
A rota anterior `/acessos` continua disponivel para compatibilidade.
Concessoes sao gerenciadas em `/usuarios/{id}/acessos`, acessada pelo botao
Perfis e escopos da edicao. O formulario de edicao nao inclui a busca ou a
listagem de concessoes. Isso preserva uma pagina exclusiva para edicao,
sem substituir o RBAC
por instrumento introduzido na fase 4.

## Reaproveitamento e Identidade

Foram adaptados os fluxos do Gestor: agrupamento de menu, filtros em rascunho,
Enter/Pesquisar, filtros avancados recolhidos, paginacao no servidor acima e
abaixo da tabela, acoes com icones/tooltips, formulario compartilhado e
selecao de permissoes por checkboxes.

Componentes locais AppShell, CrudPagination, ModalFrame e EntitySelect continuam
em uso. Nao foram importados Keycloak, clientes de API ou componentes dependentes
da infraestrutura do Gestor. A autenticacao permanece no gov.br, mas o cadastro
local e obrigatorio e anterior ao login. O formulario tem nome, username, CPF,
e-mail, ativo e observacoes. CPF e validado pelos digitos verificadores,
normalizado para 11 digitos e unico; username e normalizado para minusculas.

O ID_TOKEN tem assinatura, validade, audience e emissor verificados; o callback
valida state e nonce. sub/preferred_username sao interpretados como CPF conforme
o [roteiro tecnico oficial gov.br](https://acesso.gov.br/roteiro-tecnico/iniciarintegracao.html).
Usuario desconhecido, inativo ou excluido nao recebe sessao. O primeiro login
vincula o cadastro, sem criar contas locais ou alterar nome/e-mail. CPF vinculado
nao pode ser trocado. Esta interface nao cria contas no provedor nem senhas locais.

Desativacao/exclusao logica revogam sessoes, conservando IDs, historico e
concessoes. Reativacao exige novo login e e feita na edicao; registros excluidos
nao reaparecem na listagem e seu CPF permanece reservado. Nao e permitido
desativar/excluir o proprio usuario, revogar o proprio acesso ADMIN ou remover
o ultimo administrador ativo, inclusive em operacoes concorrentes.

O cadastro de usuario trata somente identidade e situacao. Perfis sao atribuidos,
editados e revogados exclusivamente em Concessoes de acesso. Nao existe perfil
principal nem concessao global obrigatoria. Criar/editar um usuario nao cria,
substitui ou remove concessoes.

A migration `20261012_000008` preserva IDs, normaliza CPFs e gera usernames
unicos para legados. CPFs ausentes, invalidos ou duplicados ficam inativos;
valores anteriores ficam em observacoes para regularizacao administrativa.
Concessoes nao sao apagadas. Quando houver exatamente uma concessao global,
ela recebeu originalmente a marcacao de perfil principal. Essa distincao foi
removida pela migration `20261014_000010`, sem alterar os vinculos.

Para primeiro administrador, sem outro administrador ativo:

```bash
docker compose exec -T backend python -m app.editorial_cli register-admin --nome "NOME COMPLETO" --username administrador --cpf CPF_VALIDO --email EMAIL_VALIDO
```

O cadastro permanece sem govbr_sub ate o primeiro login. O atalho local de
desenvolvimento e isolado desse fluxo: usa a conta reservada 00000000000,
nao aceita esse CPF no login gov.br e existe somente com configuracao explicita
em dev/test. A conta de desenvolvimento nao representa uma identidade gov.br.

## Perfis e Permissoes

A migration `20261012_000007` adiciona titulo, descricao e ativo aos papeis
existentes. Mantem codigos, permissoes e concessoes; nenhum usuario e promovido.
O campo codigo permanece imutavel apos a criacao para preservar referencias.
Perfis personalizados permitem combinar as permissoes reais dos servicos.

O perfil ADMIN e protegido contra alteracao, exclusao ou desativacao.
Wildcard administrativo nao pode ser concedido a perfis personalizados.
Perfil padrao ou vinculado a usuario e desativado ao excluir; suas concessoes
nao sao apagadas. Perfil personalizado sem vinculos pode ser excluido fisicamente.
Perfis inativos nao autorizam rotas, listagens por escopo ou mutacoes de imagens,
e nao podem receber novas concessoes. Reativacao e feita na edicao do perfil.

O catalogo de permissoes e somente leitura: nao e possivel criar codigos sem
implementacao de autorizacao correspondente. PUBLICO_AUTENTICADO permanece
sem acesso interno por simples autenticacao.

## Permissoes Granulares

O catalogo tem 42 permissoes. Cada CRUD tem Consultar, Incluir, Editar e Excluir,
sem uma operacao autorizar implicitamente as outras:

| Modulo | Prefixo dos codigos |
| --- | --- |
| Instrumentos | `instrumentos_` |
| Campos dinamicos | `campos_` |
| Registros dinamicos | `registros_` |
| Imagens | `imagens_` |
| Galerias/vinculos de imagens | `galerias_` |
| Usuarios | `usuarios_` |
| Perfis | `perfis_` |
| Concessoes de acesso | `acessos_` |

Os sufixos sao `consultar`, `incluir`, `editar` e `excluir`.
Permissoes, Dashboard, Pesquisa e historico editorial sao superficies de
consulta, sem CRUD artificial. Enviar revisao, revisar, publicar, arquivar e
reindexar continuam exigindo suas permissoes tecnicas independentes.

Formularios usam permissoes de consulta nos lookups e na carga do registro:
conceda tambem Consultar nos modulos envolvidos quando precisar dessas telas.
As operacoes de escrita na API permanecem independentes da permissao de leitura.
Permissoes administrativas so valem em concessoes globais. Concessoes de campos,
registros e galerias preservam o escopo por instrumento. A interface oculta
comandos nao autorizados; a API valida novamente, inclusive exclusao por PUT.

Administracao delegada nunca atribui permissoes superiores as do operador.
Criar/editar perfis, atribuir/revogar concessoes e alterar usuarios privilegiados
validam as permissoes existentes e propostas. A atribuicao de qualquer perfil exige `acessos_incluir` ou `acessos_editar`
e validacao dos privilegios delegaveis, sem atribuicao pelo CRUD de usuario.
ADMIN permanece protegido e nenhum perfil personalizado recebe wildcard.

A migration `20261013_000009` converte os agrupamentos antigos nos respectivos
codigos granulares. Preserva IDs, perfis personalizados/inativos, permissoes
nao reconhecidas, origem e escopos das concessoes; nao promove usuarios nem
concede administracao a EDITOR/GESTOR_INSTRUMENTOS. Payloads novos nao aceitam
os codigos antigos `consultar`, `gerenciar`, `editar_registro` ou
`gerenciar_imagens`. O rollback dessa migration exige revisao manual:
colapsar permissoes parciais poderia ampliar indevidamente os privilegios.

## Usuarios e Concessoes Independentes

A migration `20261014_000010` retira as constraints de perfil principal, mantendo
IDs, usuario, papel, escopo, datas e origem de todas as concessoes. O campo origem
USUARIO dos legados permanece apenas como procedencia historica, sem prioridade
ou obrigatoriedade de escopo global. Novas concessoes usam origem MANUAL.

O formulario de usuario nao tem Perfil. Apos cadastrar, exibe Sem acesso concedido
e o botao Conceder acesso somente para operadores com `acessos_incluir`.
As consultas apresentam todos os perfis distintos, total de concessoes e situacao
de acesso. A API retorna `perfis`, `total_acessos` e `tem_acesso`, sem
`perfil_codigo`/`perfil_nome`. Payloads que tentam atribuir perfil pelo cadastro
sao rejeitados com 422, em vez de ignorados silenciosamente.

Usuarios ativos sem concessoes podem autenticar pelo CPF no gov.br, mas nao
recebem autorizacao interna. A interface apresenta Acesso nao concedido; o
catalogo publico continua acessivel. Revogar todas as concessoes nao exclui a
identidade nem transforma o usuario em inativo.

A protecao do ultimo administrador usa lock transacional no PostgreSQL e cobre
revogacao/edicao de concessoes, exclusao/desativacao de usuario e de perfil.
O provisionamento do primeiro administrador permanece explicito pelo CLI,
criando identidade e concessao ADMIN na mesma transacao.

## API

- GET `/api/v1/usuarios`: q (nome/username/e-mail/CPF), nome, username, email, cpf,
  papel, ativo, limit e offset; listagem nao retorna CPF nem subject do provedor.
- POST `/api/v1/usuarios`; GET/PUT/DELETE `/api/v1/usuarios/{id}`.
- GET de usuario retorna CPF para quem possui `usuarios_consultar`, junto aos dados do popup.
- POST/PUT exigem nome, username, CPF e email; ativo e
  observacoes sao opcionais. Duplicidade retorna 409, validacao 422.
- GET/POST `/api/v1/perfis`; GET/PUT/DELETE `/api/v1/perfis/{codigo}`.
- GET `/api/v1/permissoes`: q, modulo, funcao, acao, limit e offset.
- GET `/api/v1/acessos` aceita usuario_id, alem dos filtros existentes.
- CRUD `/api/v1/acessos` aceita perfis cadastrados ativos e preserva escopo.

Essas rotas exigem a permissao especifica da operacao (ou ADMIN). APIs publicas e workflow editorial permanecem
independentes. Desativacao de perfil tem efeito no backend imediatamente,
inclusive em sessoes ja abertas; interfaces abertas podem precisar de recarga.

## Validacao

Usar a stack isolada documentada em [Operacao da fase 4](fase_04_operacao.md).
Nunca executar os testes funcionais contra os bancos operacionais.

- Suite backend: 230 testes aprovados, incluindo CPF, gov.br, CRUD, sessoes,
  autorizacao e migration/rollback em banco PostgreSQL temporario isolado.
- Contratos frontend: 41 aprovados, incluindo CSS comparado somente por leitura.
- Build Docker/TypeScript e migrations em PostgreSQL isolado aprovados.
- E2e administrativo: perfil CRUD, usuario, concessao por instrumento,
  revogacao, catalogo e desktop/mobile com API real.
- E2e editorial, busca e imagens/S3 reexecutados sem regressao.

Testes: `frontend/tests/e2e/administracao.smoke.cjs`,
`frontend/tests/e2e/usuarios.smoke.cjs` e
`frontend/tests/e2e/perfis-permissoes.smoke.cjs`. O ultimo valida CRUD de
perfis, ADMIN protegido e leitura exclusiva de permissoes.
`frontend/tests/e2e/permissoes-crud.smoke.cjs` valida usuario nao administrador,
separacao de botoes por operacao, resposta 403 e desktop/mobile.
Usar BASE_URL/ API_URL da stack isolada e THOR_E2E_ISOLATED=true;
Playwright/Chromium devem estar
disponiveis conforme o procedimento frontend existente.

O teste `concessoes-independentes.smoke.cjs` valida cadastro sem perfil,
autenticacao sem autorizacao interna, concessao por instrumento, revogacao e
layouts desktop/mobile. A suite backend cobre preservacao da migration e
revogacoes concorrentes em banco PostgreSQL temporario exclusivo de teste.

## Identidade Visual das Concessoes

Concessoes de acesso reutiliza a identidade visual de Usuarios: a primeira
coluna azul e o icone Visualizar abrem popup com campos de leitura em duas
colunas no desktop e uma no celular, acoes de editar/revogar e fechamento por
Escape. A revogacao exige confirmacao no popup. Criacao e edicao sao paginas
proprias, com pesquisa e selecao do usuario, acessos existentes e selecao multipla,
erros de validacao e retorno para a listagem de origem.

A busca tem filtros em rascunho, Enter/Pesquisar, filtros avancados recolhidos,
Limpar e paginacao no servidor acima e abaixo da tabela. Perfil e instrumento
sao apresentados pelo nome, com escopo em coluna separada, sem UUIDs na lista.
GET /acessos aceita instrumento (nome) e escopo GLOBAL/INSTRUMENTO, alem de
q, papel, usuario_id, limit e offset. O contrato mantem os IDs para mutacoes.
O teste concessoes-crud.smoke.cjs verifica o fluxo e screenshots desktop/mobile.

## Inclusao de Concessoes em Lote

A pagina /acessos/novo apresenta, em ordem: pesquisa de usuario por nome,
nome de usuario e email; acessos existentes paginados; selecao de um ou mais
perfis ativos; escolha do escopo global ou por instrumento. A pesquisa de
instrumentos aceita Nome, Tipo e Status, com selecao multipla persistente
entre pesquisas e paginas. Escopo global desabilita a pesquisa e limpa os
instrumentos selecionados. Trocar de usuario limpa o rascunho anterior.

O resumo apresenta usuario, perfis, escopo e quantidade de novos acessos.
Cada perfil selecionado e associado a cada instrumento selecionado; no escopo
global, cada perfil gera uma unica concessao sem instrumento. Edicao individual,
popup de visualizacao e revogacao continuam disponiveis na listagem.

POST /api/v1/acessos/lote recebe usuario_id, perfis (codigos), escopo
GLOBAL/INSTRUMENTO e instrumento_ids. Exige acessos_incluir; os lookups mantem
usuarios_consultar, perfis_consultar, instrumentos_consultar e acessos_consultar
para apresentar o historico de acessos atual.

Antes de qualquer INSERT, o backend valida usuario ativo, perfis ativos,
instrumentos existentes, escopo, privilegios delegaveis e conflitos.
ADMIN e wildcard sao globais. IDs/codigos repetidos e escopos incoerentes
retornam 422; referencias ausentes retornam 404; permissao insuficiente, 403.
Duplicidades e sobreposicao do mesmo perfil entre escopo global e instrumento
retornam 409: revise/revogue os acessos existentes explicitamente antes de
substituir o escopo. Nenhum acesso existente e removido automaticamente.

Limites: 50 perfis, 100 instrumentos e 1000 combinacoes por operacao.
A gravacao e transacional, protegida pelo lock administrativo existente e
constraints de unicidade; qualquer falha desfaz todo o lote. A API individual
anterior permanece compativel, sem alteracao dos registros legados. A edicao
atual usa PUT /acessos/{id}/lote e o mesmo formulario da inclusao.

Validacao adicional: test_concessoes_lote.py cobre 26 cenarios de integracao;
concessoes-lote.smoke.cjs valida o fluxo completo, rejeicao atomica, escopo
global, API real e layout desktop/mobile na stack isolada.

## Edicao de Acessos e Sessao Ativa

Inclusao e edicao reutilizam o mesmo formulario: usuario, acessos existentes,
multiplos perfis e escopo global ou varios instrumentos. A edicao carrega as
selecoes atuais e salva em PUT /api/v1/acessos/{id}/lote. Preserva o ID original,
datas/origem e os outros acessos; somente as combinacoes adicionais sao inseridas.
A operacao exige acessos_editar, e acessos_incluir quando gera novos vinculos.
Duplicidades, sobreposicoes, delegacao indevida e remocao do ultimo administrador
sao bloqueadas, com rollback de toda a operacao.

Todas as telas, inclusive /consulta, verificam a sessao no backend antes de exibir
seu conteudo. A unica tela aberta sem sessao e /login. A guarda revalida ao navegar,
ao retornar a aba/janela e periodicamente a cada 60 segundos. Qualquer resposta
401 dos clientes da API, incluindo imagens/upload, encaminha ao login.
Respostas 403 indicam falta de permissao e nao encerram uma sessao valida.

O parametro next preserva caminho, filtros e fragmento da pagina solicitada.
O login de desenvolvimento e o callback gov.br so aceitam destinos internos;
enderecos externos e retornos para login sao recusados. No gov.br, o destino
fica em cookie HttpOnly temporario e e revalidado no callback, mantendo state,
nonce e demais verificacoes existentes. APIs publicas de publicacoes permanecem
inalteradas; a exigencia de sessao abrange a interface do sistema.

Validacao: 230 testes backend e 41 contratos frontend no Docker isolado.
Os testes sessao.smoke.cjs e concessoes-edicao.smoke.cjs verificam navegacao
direta, expiracao durante o uso, retorno seguro e edicao desktop/mobile.
