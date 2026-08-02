# Testes - Backup Preservacional

Esta pasta contém a suíte automatizada do módulo de Backup Preservacional BagIt e do editor de plano JSON.

## Índice

- [Executar](#executar)
- [Cobertura](#cobertura)
- [Relatório HTML](#relatório-html)

## Executar

A partir da raiz do projeto:

```powershell
py tests\run_backup_tests_html.py
```

O comando executa todos os testes `unittest` e gera:

```text
tests/reports/backup_tests_report.html
```

## Cobertura

Os testes cobrem:

- tela **Backup Preservacional** com widgets simulados;
- tela **Editar Plano de Backup** com widgets simulados;
- criação, validação e salvamento de plano JSON;
- compatibilidade com chaves em português e chaves legadas;
- geração de manifesto de origem;
- comparação de manifestos;
- execução inicial do backup;
- execução incremental;
- versionamento de alterados;
- preservação de removidos;
- opções `algo`, `ignore_hidden` e `follow_symlinks`;
- parada segura por `STOP`;
- retomada por checkpoint;
- falha por origem inválida;
- verificação de fixidez e evento PREMIS `FIXITY_CHECK`.
- validação de pacote BagIt gerado pelo `build_bag.py`;
- detecção de payload corrompido e arquivo extra em `data/`.
- emissão de relatório TXT estruturado da verificação de fixidez para uso futuro em backup incremental.
- aplicação de backup incremental usando o relatório estruturado da verificação de fixidez.

## Relatório HTML

O relatório HTML lista:

- total de testes;
- quantidade de sucessos, falhas, erros e ignorados;
- duração total;
- lista numerada dos testes executados;
- finalidade, pré-condições e pós-condições de cada teste;
- status, duração e detalhes.

Um teste de symlink pode aparecer como `SKIP` quando o sistema operacional ou a política local não permite criar links simbólicos.
