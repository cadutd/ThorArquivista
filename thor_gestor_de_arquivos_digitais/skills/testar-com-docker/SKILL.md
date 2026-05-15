---
name: testar-com-docker
description: Priorize executar testes e validações dentro de containers Docker quando Codex precisar testar, validar ou reproduzir uma função, bug, alteração de código ou fluxo desenvolvido em um projeto que tenha instruções de container, como docker-compose.yml, docker-compose.yaml, compose.yml, compose.yaml, Dockerfile, Makefile com alvos Docker, README com comandos Docker ou documentação equivalente.
---

# Testar com Docker

## Objetivo

Validar código no mesmo ambiente em que o projeto espera rodar. Sempre que houver suporte claro a Docker no repositório, preferir executar testes, linters, migrações de teste, scripts de verificação e reproduções de bug dentro dos containers.

## Fluxo

1. Procurar sinais de ambiente Docker antes de testar: `docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, `compose.yaml`, `Dockerfile`, `Makefile`, `justfile`, `README`, `docs/` ou scripts com comandos Docker.
2. Ler as instruções do projeto e identificar o serviço correto para o teste, por exemplo `backend`, `api`, `web`, `frontend`, `app`, `worker` ou `test`.
3. Subir ou reutilizar os containers pelo comando documentado. Quando não houver comando específico, preferir `docker compose up -d` ou o alvo equivalente do projeto.
4. Executar o teste dentro do container, usando `docker compose exec <servico> <comando>` quando o serviço estiver em execução, ou `docker compose run --rm <servico> <comando>` quando o projeto documentar esse padrão.
5. Se o teste falhar por ambiente parado, imagem desatualizada ou dependência ausente, tentar a correção esperada pelo fluxo Docker do projeto, como rebuild, restart do serviço ou instalação documentada dentro da imagem.
6. Relatar claramente o comando executado, o resultado e qualquer limitação.

## Preferências

- Usar o comando mais específico do projeto quando existir, como `docker compose exec backend pytest`, `docker compose exec frontend npm test`, `make test`, `make docker-test` ou scripts equivalentes.
- Respeitar nomes de serviço, variáveis de ambiente e perfis definidos no compose.
- Rodar testes focados primeiro quando a mudança for localizada; ampliar para suítes maiores quando a alteração tocar comportamento compartilhado.
- Não instalar dependências no host se o projeto fornece caminho Docker funcional.
- Não ignorar Docker apenas porque há comandos locais disponíveis, salvo quando o próprio projeto instruir que o teste deve ser local.

## Quando Docker Não For Viável

Se Docker não estiver disponível, o daemon estiver inacessível, permissões forem negadas, imagens não puderem ser baixadas, ou o compose estiver quebrado por fator externo à mudança, registrar a tentativa e o erro. Só então usar uma alternativa local, explicando que ela é uma aproximação do ambiente esperado.

## Segurança

Antes de comandos potencialmente destrutivos, como remover volumes, limpar banco persistente ou recriar serviços com perda de dados, pedir confirmação do usuário. Para testes comuns, preferir containers efêmeros, bancos de teste e comandos documentados pelo projeto.
