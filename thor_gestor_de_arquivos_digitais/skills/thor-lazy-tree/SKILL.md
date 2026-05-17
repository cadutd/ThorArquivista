---
name: thor-lazy-tree
description: Crie ou refatore arvores navegaveis full-stack com carregamento lazy load no Thor para projetos futuros, independentemente de qualquer modulo existente. Use quando o Codex for solicitado a implementar hierarquia, arvore, expansao de nos, carregamento sob demanda, selecao de no, consulta de filhos por pai, validacao de ciclos, endpoint de arvore, componente frontend de arvore ou navegacao hierarquica.
---

# Thor Lazy Tree

## Fluxo de Trabalho

Use esta skill como um padrao full-stack generico para arvores navegaveis com lazy load. Nao presuma acesso a uma implementacao de arvore existente. Se o projeto ja tiver camadas de backend, componentes de UI, convencoes de rotas, clientes de API ou bibliotecas de estado, adapte os exemplos a esses padroes locais preservando o contrato comportamental.

Leia `references/lazy-tree-pattern.md` ao implementar ou revisar uma arvore. O arquivo contem exemplos genericos de backend e frontend para contrato de API, schemas, servico de hierarquia, endpoints, estado de expansao, busca de filhos sob demanda, hidratacao local da arvore, selecao de no, invalidacao de cache e verificacao.

## Contrato De API

Construa a arvore como contrato de backend mais superficie de frontend. O backend deve expor um endpoint de arvore que aceite `parent_id` e filtros do modulo. O comportamento esperado e:

- Sem `parent_id`, retornar apenas nos raiz ou o recorte definido pelos filtros.
- Com `parent_id`, retornar somente os filhos diretos daquele no.
- Nao retornar descendentes recursivamente na resposta lazy.
- Cada no deve informar `has_children`.
- O array de filhos (`children`, `filhos`, `items` ou nome equivalente do modulo) deve vir vazio ate que aquele no seja expandido.
- A consulta de detalhe do registro selecionado deve ficar em endpoint separado, por `id`.
- Quando houver busca textual ou filtro, mantenha um comportamento explicito: ou retorne apenas o recorte filtrado, ou faca a navegacao lazy partir das raizes filtradas. Evite misturar arvore completa com resultados de busca sem contrato claro.

Calcule `has_children` com consulta de existencia, nao com carregamento completo da relacao. Mantenha indice no campo de pai (`parent_id`, `id_parent`, `id_superior` ou equivalente) e nos campos usados em filtros frequentes.

## Contrato Do Schema

O DTO/schema de no da arvore deve conter identificador, rotulo exibivel, identificador do pai quando aplicavel, `has_children` e uma colecao de filhos vazia por padrao. Use nomes de campos coerentes com o dominio e com a convencao local do projeto. Nao renomeie campos estabelecidos sem necessidade.

Campos recomendados:

- `id`
- `label`, `nome`, `titulo` ou campo equivalente para exibicao
- `parent_id` ou equivalente
- `has_children`
- `children`, `filhos` ou equivalente, com lista vazia no retorno lazy
- metadados pequenos necessarios para a linha da arvore, sem payload pesado

## Padrao Frontend

Implemente a arvore com estado local para navegacao e a biblioteca de busca/cache ja usada no projeto:

- `expanded: Set<string>` para controlar nos abertos.
- `treeChildren: Record<string, Node[]>` para armazenar filhos ja carregados por pai.
- `loadingTreeNodes: Set<string>` para spinner por no.
- `selectedId: string | null` para selecao.
- consulta inicial para carregar a raiz ou o recorte filtrado.
- busca sob demanda no `toggleTreeNode` para carregar filhos com `parent_id`.
- `hydrateTreeNodes(rootNodes, treeChildren)` para mesclar filhos carregados na arvore exibida.
- consulta de detalhe separada quando um no for selecionado.

O `toggleTreeNode` deve alternar o estado visual e buscar filhos apenas quando `node.has_children` for verdadeiro e ainda nao houver entrada em `treeChildren[node.id]`. Nao faca prefetch recursivo de descendentes.

Ao alterar filtros ou busca, limpe `expanded`, `treeChildren` e `loadingTreeNodes` para evitar filhos de consultas antigas misturados com a nova visao.

## Backend

As camadas de backend devem incluir, adaptando nomes a stack:

- modelo/entidade com chave primaria e chave estrangeira opcional para o pai
- migracao com indice no campo de pai
- schema/DTO de no da arvore
- consulta de raizes e consulta de filhos diretos por `parent_id`
- servico para validar hierarquia quando o pai puder ser editado
- router/controller com endpoint de arvore e endpoint de detalhe
- testes de arvore, lazy load e integridade hierarquica

Mantenha regras de hierarquia no backend mesmo quando o frontend tambem validar. Bloqueie autorreferencia, ciclos, pai inexistente e mudancas que violem regras de nivel quando o dominio tiver niveis controlados.

## Padrao Visual

Arvores sao superficies de navegacao operacional. Mantenha a UI densa, escaneavel e previsivel:

- Use icones familiares de expandir, recolher e carregar da biblioteca ja usada no frontend.
- Reserve largura fixa para o botao de expansao para evitar deslocamento do texto.
- A linha inteira pode selecionar o no, mas o botao de expansao deve ser independente quando houver filhos.
- Indente por nivel com valor previsivel, mantendo leitura em telas menores.
- Mostre estado vazio, estado de carregamento e estado de erro.
- Nao carregue dados completos do registro dentro do no se a tela ja tem endpoint de detalhe.

## Regras De Hierarquia

Quando o modulo permitir edicao da hierarquia:

- Bloqueie autorreferencia.
- Bloqueie ciclos ao trocar o pai de um registro.
- Valide a existencia do pai informado.
- Em exclusao, siga o padrao do modulo: impedir quando houver filhos, exigir cascata explicita, ou aplicar exclusao logica se o dominio ja usar esse padrao.

Use constraints e indices no banco quando possivel, mas nao dependa apenas deles para regras que exigem percorrer ancestrais.

## Testes Esperados

Inclua testes cobrindo:

- A rota raiz retorna somente raizes ou recorte inicial.
- Um no com filhos vem com `has_children: true` e `children`/`filhos` vazio.
- A rota com `parent_id` retorna somente filhos diretos.
- Filtros e busca nao forcam carregamento recursivo.
- Autorreferencia e ciclos sao rejeitados quando a hierarquia e editavel.
- No frontend, quando houver teste aplicavel, a expansao busca filhos sob demanda e preserva a selecao.

## Validacao

Depois de implementar ou refatorar uma arvore lazy load no Thor, rode a validacao mais especifica disponivel:

- Testes funcionais do backend do modulo alterado.
- `npm run typecheck` no frontend quando TypeScript foi alterado.
- Lint direcionado ao arquivo modificado quando o projeto suportar.
- Smoke test visual ou Playwright quando a mudanca afetar comportamento de navegacao da arvore.
