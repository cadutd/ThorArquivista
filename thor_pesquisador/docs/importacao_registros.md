# Importacao de Registros

O fluxo principal evoluiu para a [central de importacao assincrona](importacao_assincrona.md),
com ate 1 milhao de registros/2 GiB e worker dedicado. As secoes abaixo
documentam o importador sincrono legado, mantido para compatibilidade.

Funcionalidade interna do Thor Pesquisador, acessada em Instrumentos ->
Registros -> Importar registros. Nao existe importacao no portal.

## Fluxo

1. Selecionar CSV ou JSON e analisar o arquivo.
2. Associar cada coluna a um campo existente, ignorar a coluna ou criar um novo
   campo informando nome, chave, tipo e obrigatoriedade. O botao Criar campos
   nao associados prepara as definicoes; ainda nao grava o schema.
3. Validar todos os registros e conferir a previa dos cinco primeiros.
4. Confirmar a importacao e consultar o resultado.

Nao ha gravacao de campos ou registros na analise/validacao. Todos os dados
devem ser validos antes da confirmacao. Erros mostram o numero do registro
(ordinal, sem contar o cabecalho CSV), campo e mensagem; ate 100 erros sao
exibidos, com contagem total de registros invalidos.
Campos obrigatorios existentes tambem precisam receber valores.

Novos campos ficam privados, com cadastro/listagem/busca habilitados e sem
facetas ou filtro publico automatico. A criacao usa a evolucao de schema e a
auditoria existentes, colocando o instrumento em rascunho.
Registros entram ATIVO/RASCUNHO; nenhum conteudo e publicado automaticamente.
Registros existentes nao sao atualizados ou substituidos.

## Arquivos e Conversoes

- Limites: 5 MiB, 1000 registros e 100 colunas por arquivo.
- CSV com cabecalho unico, separador virgula, ponto e virgula ou tabulacao,
  aspas e quebras de linha entre aspas. Linhas vazias sao ignoradas.
- UTF-8 com/sem BOM; CSV tambem aceita Windows-1252. JSON exige UTF-8.
- JSON: lista de objetos, ou objeto com uma lista em registros/items.
  As colunas sao a uniao das chaves dos objetos. Nao ha achatamento implicito
  de objetos aninhados: podem ser associados a texto longo como JSON textual.
- Numero: inteiro de 64 bits ou decimal finito, ponto ou virgula decimal,
  sem separador de milhares. Inteiros fora do intervalo sao rejeitados.
- Data: YYYY-MM-DD ou DD/MM/YYYY, armazenada em ISO.
- Booleano: Sim/Nao, true/false ou 1/0, preservando falso e zero.
- Lista multipla: array JSON de textos ou textos separados por |.
- Campos vazios tornam-se null. Identificadores com zeros a esquerda recebem
  sugestao de texto; a sugestao de tipo pode ser alterada antes de gravar.

O arquivo original nao e persistido. Historico SQL guarda identificador,
autor, assinatura SHA-256, mapeamento, schema, contadores e estado, sem copiar
o conteudo dos registros. Registros canonicos permanecem no MongoDB.

## Permissoes e Retomada

Exige usuario local ativo, registros_incluir e instrumentos_consultar no
instrumento. Criar campos exige tambem campos_incluir; nenhuma permissao,
perfil ou concessao e ampliada. Historico recente mostra apenas as ultimas
20 importacoes do proprio usuario no instrumento.

Estados: EM_ANDAMENTO, INTERROMPIDA e CONCLUIDA. Falha de infraestrutura pode
deixar um lote parcial. Reenviar o mesmo arquivo e o mapeamento original pela
acao Retomar preserva o identificador da operacao e os IDs deterministicos.
Uma operacao concluida repetida nao cria duplicatas. Usar Nova importacao
gera outra operacao e pode criar registros adicionais intencionalmente.

A criacao inicial do historico e dos novos campos e transacional em SQL.
Nao ha transacao distribuida SQL/MongoDB: cada registro usa o servico existente,
com intencao auditada e progresso confirmado. A retomada recupera o controle
editorial de um insert Mongo ja confirmado sem sobrescrever edicoes posteriores.
Registros expurgados ou com controle SQL sem documento nao sao recriados.
Permissoes e schema sao conferidos novamente; mudancas de schema podem impedir
a retomada e exigir reconciliacao, sem remover o que ja foi importado.

Importacoes simultaneas do mesmo instrumento sao bloqueadas por advisory lock
PostgreSQL. Processamento e sincrono e limitado; nao foi criado novo worker.
Uma queda do processo pode deixar EM_ANDAMENTO; o bloqueio e liberado pela
conexao e a operacao pode ser retomada com o arquivo original.

## API e Implantacao

Prefixo: /api/v1/instrumentos/{id}/registros/importacoes.

- POST /analisar: multipart arquivo.
- POST /validar: multipart arquivo + configuracao JSON.
- POST no prefixo: confirma ou retoma, com os mesmos campos multipart.
- GET no prefixo: historico recente do proprio usuario.

Configuracao contem operacao_id UUID, schema_version e mapeamentos:

```json
{
  "operacao_id": "f5c6ea7a-d7bd-4cc6-a9bd-05b006640f01",
  "schema_version": 2,
  "mapeamentos": [
    {"origem": "Nome", "destino": "nome"},
    {"origem": "Porto", "novo": {
      "nome": "Porto de chegada", "chave": "porto_chegada",
      "tipo": "TEXTO_CURTO", "obrigatorio": false
    }}
  ]
}
```

Colunas ignoradas nao entram em mapeamentos. Destino repetido, chave de novo
campo existente, origem inexistente e configuracoes conflitantes sao recusados.
O middleware mantem CSRF e limites de upload; valores nunca sao executados.

Migration 20261019_000017 cria importacoes_registros e indices, preservando
dados e permissoes existentes. Fazer backup antes de alembic upgrade head.
Instrumentos com historico de importacao devem ser arquivados, nao apagados.
Downgrade recusa descartar uma tabela de importacoes nao vazia.

## Validacao

Testes de parser/conversoes, integracao SQL/MongoDB, permissoes, schema
concorrente, falha apos gravacao e retomada sem duplicacao.
Frontend inclui contratos e importacao.smoke.cjs com CSV/JSON reais,
confirmacao/cancelamento, novos campos privados, erros, retorno e capturas
desktop/mobile. Executar no ambiente docker-compose.test.yml com
THOR_E2E_ISOLATED=true e BASE_URL/API_URL apontando para localhost:3001/8001.

Resultado: 479 testes backend, 62 contratos frontend e build Docker aprovados.
O fluxo importacao.smoke.cjs passou com API, PostgreSQL e MongoDB reais.
Migration aplicada localmente apos backup PostgreSQL, com os oito instrumentos
e os 200 registros do instrumento de imigracao preservados. A verificacao local
foi somente ate a analise de arquivo sintetico, sem confirmar novos registros.
