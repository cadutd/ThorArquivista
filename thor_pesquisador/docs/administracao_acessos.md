# Administracao de Acessos

Atualizacao de 2026-10-13, adaptada da organizacao administrativa do Thor Gestor
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
e-mail, perfil, ativo e observacoes. CPF e validado pelos digitos verificadores,
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
desativar/excluir o proprio usuario ou remover seu proprio perfil principal ADMIN.

O perfil principal usa a concessao global existente com origem USUARIO;
concessoes MANUAL e escopos por instrumento sao preservados ao troca-lo.
Nao ha segundo mecanismo de autorizacao. Usuarios/perfis usam permissoes por operacao.

A migration `20261012_000008` preserva IDs, normaliza CPFs e gera usernames
unicos para legados. CPFs ausentes, invalidos ou duplicados ficam inativos;
valores anteriores ficam em observacoes para regularizacao administrativa.
Concessoes nao sao apagadas. Quando houver exatamente uma concessao global,
ela passa a representar o perfil principal; multiplas concessoes globais
continuam intactas e o perfil principal deve ser escolhido na edicao.

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
validam as permissoes existentes e propostas. O perfil principal pode ser
atribuido no CRUD de usuario somente se seus privilegios forem delegaveis.
ADMIN permanece protegido e nenhum perfil personalizado recebe wildcard.

A migration `20261013_000009` converte os agrupamentos antigos nos respectivos
codigos granulares. Preserva IDs, perfis personalizados/inativos, permissoes
nao reconhecidas, origem e escopos das concessoes; nao promove usuarios nem
concede administracao a EDITOR/GESTOR_INSTRUMENTOS. Payloads novos nao aceitam
os codigos antigos `consultar`, `gerenciar`, `editar_registro` ou
`gerenciar_imagens`. O rollback dessa migration exige revisao manual:
colapsar permissoes parciais poderia ampliar indevidamente os privilegios.

## API

- GET `/api/v1/usuarios`: q (nome/username/e-mail/CPF), nome, username, email, cpf,
  papel, ativo, limit e offset; listagem nao retorna CPF nem subject do provedor.
- POST `/api/v1/usuarios`; GET/PUT/DELETE `/api/v1/usuarios/{id}`.
- GET de usuario retorna CPF para quem possui `usuarios_consultar`, junto aos dados do popup.
- POST/PUT exigem nome, username, CPF, email e perfil_codigo; ativo e
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

- Suite backend: 165 testes aprovados, incluindo CPF, gov.br, CRUD, sessoes,
  autorizacao e migration/rollback em banco PostgreSQL temporario isolado.
- Contratos frontend: 35 aprovados, incluindo CSS comparado somente por leitura.
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
