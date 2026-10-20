# Instrumentos: Consulta, Filtros e Capas

Atualizacao de 2026-10-19, exclusivamente no Thor Pesquisador.

## Consulta

O cabecalho publico nao possui mais o link Instrumentos ao lado de Entrar.
Busca da landing e Ver todos continuam levando ao catalogo /consulta.
Cards ficam somente na landing; o catalogo usa tabela, primeira coluna
navegavel azul, acao Consultar registros com tooltip e CrudPagination dupla.
Consulta de registros continua exigindo sessao.

Filtros avancados recolhidos, aplicados somente por Buscar/Enter:

- Area interna /instrumentos: Nome, Tipo, Status, Visibilidade e Descricao.
- Catalogo /consulta: Nome, Tipo e Descricao, sobre metadados publicados.

Busca simples por nome/descricao foi mantida. Limpar filtros e mudar tamanho
reiniciam a pagina. Filtragem e paginacao ocorrem no servidor, com campos
combinados por AND; o catalogo nao divulga metadados de rascunhos ou instrumentos
INTERNO/RESTRITO, independentemente de parametros manipulados.

## Pesquisa de Registros no Portal

/consulta/{id} segue a identidade das listagens do sistema: busca simples,
filtros avancados recolhidos, Limpar filtros, tabela e CrudPagination acima
e abaixo. A API de publicacoes continua sendo a fonte da consulta, com
apenas a pagina atual carregada. Buscar/Enter, limpeza e troca de tamanho
reiniciam a pagina; navegacao preserva os filtros ja aplicados, nao o rascunho.

Cada campo publicado marcado aparece_listagem possui sua propria coluna.
A primeira coluna e um link azul e a acao Visualizar registro tem tooltip.
Sem colunas configuradas, usa-se o titulo publicado como identificacao.
Valores ausentes mostram -, booleanos Sim/Nao e listas sao separadas por virgula.
Nao ha inclusao, edicao ou exclusao no portal.

Filtros usam somente campos publicados autorizados como facetavel ou
filtro_avancado, mantendo o contrato existente. Opcoes de facetas sao
buscadas somente ao abrir os filtros; controles de numero, booleano e data
enviam valores tipados, inclusive zero e falso. Campos privados e rascunhos
nao aparecem na consulta. Falhas e respostas atrasadas tem tratamento explicito.
Sessao continua obrigatoria, inclusive para visitantes gov.br sem cadastro.

Validacao desta revisao: 60 contratos frontend, build Docker e 37 testes
backend de portal/editorial aprovados. O fluxo portal-registros.smoke.cjs
passou com indice Meilisearch real, 21 publicacoes, visitante, sessao,
filtros tipados, paginacao, visualizacao e axe desktop/mobile.
Executar somente na stack docker-compose.test.yml, com
THOR_E2E_ISOLATED=true, BASE_URL=http://localhost:3001,
API_URL=http://localhost:8001/api/v1 e AXE_SCRIPT apontando para axe.min.js:
node frontend/tests/e2e/portal-registros.smoke.cjs.

## Imagem Opcional do Card

Criacao e edicao de instrumento oferecem Imagem do card, previa e remocao
confirmada. Sem imagem ou se o arquivo estiver indisponivel, usa-se a imagem
institucional existente images/login-digital-archive.png.

Upload reutiliza validar_imagem e ArmazenamentoS3: confere MIME real, tamanho,
decodificacao e protecao contra dimensoes excessivas (ate 16 megapixels para
capas, antes da decodificacao completa). Imagem e orientada,
convertida em JPEG 960 x 540 e ajustada com margens, sem distorcao/corte do
conteudo enviado. EXIF/metadados originais nao sao copiados para o JPEG final.
O card e a previa tem dimensoes/proporcao estaveis.

Capas sao assets institucionais separados das imagens de registros:

- POST /api/v1/instrumentos/imagens-card: multipart arquivo e instrumento_id
  opcional. Criacao exige instrumentos_incluir global; edicao exige
  instrumentos_editar no instrumento informado.
- GET /api/v1/instrumentos/imagens-card/{id}: previa autenticada, com validacao
  de propriedade/permissao vigente ou consulta ao instrumento vinculado.
- imagem_card_id opcional em POST/PUT de instrumento; null remove a selecao.
  Nao e permitido associar upload privado de outro usuario, salvo ADMIN.
- GET /api/v1/publico/instrumentos/{id}/imagem-card/{capa_id}: anonimo somente
  se a capa estiver no snapshot publicado vigente e continuar selecionada
  no instrumento PUBLICO elegivel. Capas pendentes, removidas, substituidas
  ou de instrumentos arquivados/privados retornam 404.

Upload sozinho nao publica uma imagem. Salvar instrumento altera rascunho/
versao pelo fluxo existente; a nova capa fica publica apos revisao e publicacao.
URLs de capas antigas deixam de servir o arquivo quando a referencia atual
e removida/substituida. Bucket permanece privado e URLs S3 nao sao expostas.
Imagens/conteudo de registros continuam exigindo sessao.

Upload e vinculo sao etapas separadas: cancelar um formulario pode deixar
um upload sem vinculo. Nao ha limpeza automatica de capas nesta entrega,
pois publicacoes historicas tambem referenciam esses objetos imutaveis.
Uma futura limpeza precisa conferir referencias historicas antes de remover
qualquer arquivo; nao reutilizar limpeza de imagens de registros.

## Banco, Auditoria e Permissoes

Migration 20261019_000016, depois de 20261016_000015, cria instrumento_capas e
FK opcional instrumentos.imagem_card_id. Cadastros/publicacoes existentes
permanecem intactos e passam a usar a imagem padrao.
Downgrade recusa execucao se houver capas, para nao apagar referencias historicas.

Nao foram criadas permissoes artificiais de midia: incluir/editar/consultar
instrumentos e os escopos existentes governam as operacoes. Nenhum perfil foi
ampliado. Upload e alteracoes sao auditados com agente cadastrado.
Storage deve estar configurado; falha S3 nao impede salvar sem imagem.

## Validacao

Backend: filtros combinados e snapshot, upload S3 real 960 x 540, MIME invalido,
autenticacao, permissao revogada, vinculo inexistente, publicacao, substituicao,
remocao e protecao das imagens de registros.
Frontend: contratos de tabela/filtros/default e compilacao Docker.
Navegador: portal.smoke.cjs e instrumentos-portal.smoke.cjs, somente com
THOR_E2E_ISOLATED=true e URLs da stack docker-compose.test.yml.
Capturas desktop/mobile ficam no temporario do sistema.

Resultado em 2026-10-19: 404 testes backend e 54 contratos frontend passaram;
builds Docker aprovados. Os fluxos portal.smoke e instrumentos-portal.smoke
passaram, incluindo axe no portal, filtros, upload S3 real, capa publica,
substituicao/remocao, fallback e capturas desktop/mobile.
Validacao adicional do limite de resolucao e uploads de registros tambem passou.
Migration aplicada localmente com os oito instrumentos preservados; PostgreSQL
foi copiado antes da alteracao. O ambiente local permanece em localhost:3000.
