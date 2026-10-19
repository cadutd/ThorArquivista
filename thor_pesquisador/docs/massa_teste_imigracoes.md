# Massa de Testes de Imigracao

Gerador local de 2026-10-17: instrumento **Registros de Imigracao (dados ficticios)**,
ID fixo 639efff1-507f-5f1e-a043-7d55894b119d. Os dados sao inteiramente sinteticos,
identificados como ficticios na descricao e em cada registro. Nao representam
documentos historicos nem foram importados de pessoas reais.

## Conteudo

Padrao de 200 registros (limite configuravel de 1 a 1000), com:

- Nome e nome da mae.
- Nacionalidade: 10 opcoes, como Italiana, Portuguesa, Japonesa e Libanesa.
- Data de chegada: datas ficticias entre 1880 e 1932.
- Porto de chegada: Santos, Rio de Janeiro, Recife, Salvador, Belem e Rio Grande.
- Codigo do registro, navio ficticio, idade na chegada e observacoes.

Nome, nome da mae, nacionalidade, data e porto possuem filtros avancados.
Nacionalidade e porto sao listas controladas com facetas.
Todos os campos sao consultaveis no snapshot publicado; nome e o titulo do registro.

## Executar Localmente

Somente em dev/test. Em dev, govbr_dev_login e dev_admin_enabled precisam estar
explicitamente habilitados. O gerador exige o UUID de um usuario cadastrado,
ativo e com as permissoes globais necessarias; nao cria usuarios ou concessoes.

Na raiz do Thor Pesquisador:

```powershell
docker compose build backend
docker compose up -d backend frontend index_worker
docker compose exec backend python -m app.scripts.seed_imigracoes --usuario-id UUID_DO_USUARIO --quantidade 200 --publicar
```

--publicar envia instrumento e registros por revisao, aprovacao e publicacao
versionada. Sem essa flag, cria apenas rascunhos, sem disponibilizar o acervo
no portal. O agente dos eventos e o usuario informado, nunca um literal sistema.
O index_worker existente conclui a projecao Meilisearch em segundo plano;
ate a geracao vigente ficar pronta, a busca publicada pode retornar 503.

Nao executar em homologacao/producao; o script recusa esses ambientes.
Para testes automatizados, usar exclusivamente docker-compose.test.yml.

## Reexecucao e Preservacao

Instrumento tem ID fixo e registros possuem identificadores privados da massa.
Reexecutar nao duplica registros ou publicacoes e nao apaga dados.
Edicoes, inativacoes e arquivamentos de registros sao preservados, sem
republicacao automatica desses registros. O identificador privado permite
reconhecer um registro mesmo quando seu codigo visivel foi editado.
Se metadados do instrumento ou schema existentes foram alterados, o gerador
interrompe sem sobrescreve-los. Bloqueio PostgreSQL impede duas cargas simultaneas.

As operacoes sao incrementais e reutilizam os servicos/auditoria existentes.
Nao existe transacao atomica SQL/Mongo/Meilisearch: falha intermediaria pode
deixar uma carga parcial, retomavel pelo mesmo comando. Nao apagar historico
ou forcar estados editoriais para completar a carga.

## Consultar

O instrumento aparece na landing page e no catalogo sem login. A busca,
os detalhes, as facetas e os registros continuam exigindo sessao, inclusive
para dados ficticios. Visitante gov.br nao recebe acesso administrativo.

Portal local: http://localhost:3000/consulta/639efff1-507f-5f1e-a043-7d55894b119d

## Validacao

Nove testes especificos em backend/app/tests/functional/test_massa_imigracoes.py:
repetibilidade/diversidade, publicacao e agente, idempotencia, busca nominal,
paginacao/facetas, consulta autenticada, preservacao de edicoes/codigos,
permissoes, ambientes e limites. Executar com bancos isolados:

```powershell
docker compose -f docker-compose.test.yml exec -T backend python -m pytest -q -p no:cacheprovider app/tests/functional/test_massa_imigracoes.py
```

Pesquisa textual Meilisearch e aproximada; codigo com hifens/zeros nao e filtro
exato. Use nomes para testar busca textual e nacionalidade/porto para facetas.

### Resultado Local em 2026-10-17

- Criados e publicados 200 registros, nove campos, dez nacionalidades e seis portos.
- Geracao publica 210 concluida pelo worker; busca disponivel sem indice defasado.
- Segunda execucao: 200 existentes, zero criados, zero republicados e zero campos criados.
- Comparacao de conteudo/estados confirmou preservacao dos sete instrumentos
  e 17 registros anteriores, incluindo campos e controles editoriais.
- Nove testes especificos passaram; suite backend completa: 401 passaram.
- Navegador real confirmou card publico, retorno de login, pagina de 20 registros,
  busca nominal e filtro Japonesa com 20 resultados; detalhe com filiacao/data/porto
  e layouts desktop/mobile sem overflow ou erros JavaScript.
- Permanecem os avisos conhecidos de depreciacao httpx no TestClient e alias
  Pydantic em teste concorrente, sem falha nessa execucao.
