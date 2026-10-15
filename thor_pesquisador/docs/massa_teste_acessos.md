# Massa de Testes de Acessos

Gerador explicito e idempotente para o ambiente local do Thor Pesquisador.
Nao e migration e nao e executado na inicializacao da aplicacao.

## Gerar

A partir da pasta thor_pesquisador, com os containers atualizados:

```bash
docker compose exec -T backend python -m app.scripts.seed_acessos --usuarios 60 --perfis 24
```

Para a stack isolada, substitua o inicio por
docker compose -f docker-compose.test.yml exec -T backend.

Limites configuraveis: 1 a 1000 usuarios e 1 a 100 perfis. O comando imprime
quantos registros foram criados e os totais da massa. Uma segunda execucao
com os mesmos parametros nao duplica dados.

## Conteudo Padrao

- 60 usuarios, com nomes prefixados por Teste - e usernames massa_acesso_001
  a massa_acesso_060; 54 ativos e 6 inativos.
- 24 perfis MASSA_ACESSO_001 a MASSA_ACESSO_024; 22 ativos e 2 inativos.
- Perfis sinteticos de consulta, catalogacao e revisao, sem permissoes
  administrativas nem wildcard.
- Os primeiros 8 usuarios ficam sem concessoes. Usuarios inativos tambem
  nao recebem concessoes.
- Outros usuarios recebem dois perfis globais ou dois perfis em ate dois
  instrumentos ja existentes. Nenhum instrumento e criado ou alterado.
- Emails usam example.org; CPFs sao numeros sinteticos com digitos verificadores.
  Nao representam identidades verificadas. Nao ha vinculo gov.br, senha ou
  sessao criada para esses usuarios.

Pesquise usuarios por massa_acesso_ e perfis por MASSA_ACESSO_ para conferir
a paginacao. A pesquisa do formulario de concessao considera somente ativos.

## Seguranca e Reexecucao

Permitido apenas em app_env=dev ou test. Em dev, tambem exige
dev_admin_enabled e govbr_dev_login explicitamente habilitados.
Nao utilizar CPFs ou dados desta massa em integracao real com gov.br.

Registros existentes nao sao sobrescritos. Edicoes e concessoes revogadas
pelo CRUD nao sao restauradas. Para usuarios ja existentes, o comando nao
adiciona novos vinculos. Colisao de CPF, username ou codigo de perfil de
outro cadastro interrompe e reverte toda a transacao. IDs sao deterministas,
e os dados da massa possuem marcador MASSA_ACESSOS.

## Validacao

Os testes de integracao test_massa_acessos.py cobrem idempotencia, preservacao
de registros externos e de edicoes manuais, rollback de colisao, ausencia de
administradores/sessoes, limites e bloqueio de ambientes operacionais.

O teste de navegador concessoes-identidade.smoke.cjs compara o formulario
com Usuarios e valida pesquisas paginadas, selecao persistente entre paginas
e layouts desktop/mobile. Execute exclusivamente na stack Docker isolada.
