---
name: thor-crud-base
description: Crie ou refatore módulos CRUD full-stack usando o padrão CRUD base do Thor para projetos futuros, independentemente de qualquer código de entidade existente. Use quando o Codex for solicitado a criar modelos de backend, migrações, schemas, repositórios, serviços, rotas de API, listagem frontend, criação, edição, visualização, exclusão, busca simples, filtros avançados, paginação, dados carregados sob demanda, campos obrigatórios ou fluxos de navegação para uma funcionalidade CRUD.
---

# Thor CRUD Base

## Fluxo de Trabalho

Use esta skill como um padrão CRUD full-stack genérico. Não presuma acesso a uma implementação CRUD existente. Se o projeto já tiver camadas de backend, componentes de UI, convenções de rotas, clientes de API ou bibliotecas de estado, adapte os exemplos a esses padrões locais preservando o contrato comportamental.

Leia `references/crud-base-pattern.md` ao implementar ou revisar um CRUD. O arquivo contém exemplos copiáveis de backend e frontend para persistência, contratos de API, paginação, filtros, navegação, páginas de listagem, filtros de tabela, formulários, campos obrigatórios, carregamento sob demanda, mutações e verificação.

## Contrato Principal

Construa cada CRUD como um contrato de backend mais superfícies de frontend.

As camadas de backend devem incluir, adaptando os nomes à stack:

- modelo/entidade de persistência
- migração ou alteração de schema
- schemas ou DTOs de requisição/resposta
- camada de repositório/consulta
- camada de serviço/negócio
- router/controller de API com endpoints de listar, obter, criar, atualizar e excluir
- testes de validação, filtros, paginação e mutações quando o projeto tiver testes

As superfícies de frontend devem incluir:

- rota de listagem: `/entities`
- rota de criação: `/entities/new` ou o equivalente local do projeto, como `/entidades/nova`
- rota de edição: `/entities/{id}/edit` ou o equivalente local do projeto, como `/entidades/{id}/editar`
- componente de tabela reutilizável para listagem, busca, filtros avançados, paginação e ações de linha
- componente de formulário reutilizável para criação e edição
- componente ou rota opcional de detalhes para visualização somente leitura

Mantenha os contratos de backend e frontend alinhados: nomes de campos, valores de enum, campos obrigatórios, campos anuláveis, nomes de filtros, formatos de data, parâmetros de paginação e comportamento de erro devem coincidir.

Use uma página completa para fluxos de criação, não um popup. A ação principal da listagem navega para a rota de criação. A tela de criação inclui um botão `Voltar`. Após criar com sucesso, navegue de volta para a listagem, salvo se o usuário pedir outro destino.

Use uma página completa para fluxos de edição, não um popup. A ação de editar na tabela e nos detalhes navega para a rota de edição. A tela de edição carrega a entidade por ID, reutiliza o formulário de criação/edição, inclui um botão `Voltar` para a listagem e, após salvar com sucesso, navega de volta para a listagem salvo se o usuário pedir outro destino.

Visualização pode ser rota ou diálogo dependendo do projeto. A exclusão deve exigir confirmação explícita antes da mutação.

## Comportamento da API Backend

Exponha endpoints previsíveis no estilo REST, salvo se o projeto usar outro estilo de API:

- `GET /entities` retorna `{ items, total }`
- `GET /entities/{id}` retorna um registro ou `404`
- `POST /entities` valida e cria
- `PUT` ou `PATCH /entities/{id}` valida e atualiza
- `DELETE /entities/{id}` exclui, faz exclusão lógica ou desativa conforme as regras de negócio

Endpoints de listagem devem suportar paginação no servidor. Prefira `limit` e `offset`, ou mapeie para a convenção existente do projeto, como `page` e `pageSize`. Aplique filtros na consulta do backend, não depois de carregar todas as linhas em memória.

Endpoints de busca devem suportar:

- consulta simples de texto, como `q`
- filtros avançados para campos exatos, enums, booleanos, intervalos numéricos e intervalos de data
- ordenação determinística, normalmente mais recentes primeiro ou por identificador estável
- tamanho máximo de página explícito para proteger a API

Campos obrigatórios e valores de enum do backend são a fonte da verdade. Espelhe-os na validação do frontend, mas nunca dependa apenas da validação do frontend.

## Comportamento da Listagem

Busque da API apenas a página atual. Não carregue todos os registros apenas para paginar localmente quando o conjunto de dados puder crescer.

Mantenha o estado da listagem explícito:

- `filters`
- `pageIndex`
- `pageSize`

Use uma chave estável de consulta/cache contendo o nome da entidade, filtros, índice da página e tamanho da página. O formato esperado da API paginada é `{ items, total }`, ou adapte o mapper se o backend usar nomes diferentes.

## Busca, Filtros e Paginação

Forneça busca simples:

- campo de busca na barra de ferramentas da tabela
- ícone de busca quando houver biblioteca de ícones
- tecla Enter submete
- botão Buscar submete
- toda nova busca redefine para a primeira página

Forneça busca avançada:

- recolhida por padrão atrás de um botão alternável
- grid responsivo de campos de metadados
- controles de texto, enum, booleano, numérico e intervalo de datas conforme apropriado
- ação de limpar filtros que redefine o rascunho e submete um objeto de filtros vazio

Renderize a paginação acima e abaixo da tabela para conjuntos longos de resultados. Inclua contagem exibida, contagem total, página atual, total de páginas, seletor de tamanho de página, controles de primeira/anterior/próxima/última e links diretos para páginas numeradas da pesquisa. Para muitas páginas, mostre sempre a primeira, a última, a atual e as páginas vizinhas, usando reticências para lacunas entre grupos de páginas.

## Formulários

Use um validador de schema quando a stack suportar, como Zod. Mantenha os valores padrão explícitos. Campos obrigatórios devem estar representados tanto no schema de validação quanto na UI.

Use um marcador visível de obrigatório ao lado dos rótulos. Mostre erros de campo diretamente abaixo dos campos. Mostre erros de mutação perto do envio. Desabilite o envio durante o salvamento e use texto de salvamento, como `Salvando...`.

Use layout responsivo:

- grids de duas colunas para campos curtos em telas maiores
- campos de largura total para descrições longas
- seções condicionais com borda quando um campo revelar dados dependentes

No modo de edição, redefina os valores do formulário a partir da entidade carregada. No modo de criação, redefina para os padrões após sucesso apenas se permanecer no formulário; caso contrário, navegue para fora.

## Carregamento Sob Demanda

Use carregamento sob demanda de forma intencional:

- pagine dados de listagem no servidor com `limit`/`offset` ou `page`/`pageSize`
- busque listas de opções apenas quando o formulário ou campo estiver visível
- use `enabled` ou proteções equivalentes para consultas que dependem de IDs, modos selecionados, rotas de edição ou diálogos abertos
- busque detalhes pesados de linha apenas quando o usuário abrir os detalhes
- mantenha o estado de busca em segundo plano separado dos estados vazio/erro

## Mutações

Use mutações de criação, atualização e exclusão. Em caso de sucesso:

- invalide ou atualize a consulta da listagem
- invalide consultas relacionadas de lookup/detalhe quando necessário
- chame um callback `onSaved` ou equivalente para que o componente pai controle navegação/fechamento
- mantenha a confirmação de exclusão próxima da ação destrutiva

Converta campos numéricos opcionais e strings vazias antes de enviar payloads. Prefira `null` para campos opcionais intencionalmente vazios no backend quando a API esperar valores anuláveis.

## Integridade de Dados no Backend

Mantenha regras de negócio na camada de serviço do backend mesmo quando o frontend também as validar. Use constraints de banco de dados para campos únicos, colunas obrigatórias, chaves estrangeiras, índices para campos pesquisados e colunas de timestamp quando o projeto suportar.

Para filtros e paginação, adicione índices que correspondam às consultas prováveis. No mínimo, considere índices para identificadores estáveis, campos de status, chaves pai/estrangeiras e timestamps de criação/atualização. Para busca textual ampla, use o mecanismo de full-text estabelecido pelo projeto quando disponível; caso contrário, use filtros conservadores `contains`/`ilike` apropriados ao banco.

Retorne erros consistentes:

- `400` ou `422` para erros de validação
- `404` para registros ausentes
- `409` para conflitos de unicidade ou estado
- `500` apenas para falhas inesperadas

## Padrão Visual

Telas CRUD são ferramentas operacionais. Mantenha-as densas, fáceis de escanear e previsíveis. Evite landing pages, fundos decorativos, cards aninhados, layouts hero exagerados e UI puramente ornamental. Use ícones familiares para ações de adicionar, buscar, filtrar, visualizar, editar, excluir e voltar quando disponíveis.
