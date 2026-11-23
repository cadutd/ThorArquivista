# Testes - Backup Preservacional

Esta pasta contém a suíte automatizada do módulo de Backup Preservacional BagIt e do editor de plano JSON.

## Índice

- [Executar](#executar)
- [Cobertura](#cobertura)
- [Verificação de fixidez: caminhos longos e rede](#verificação-de-fixidez-caminhos-longos-e-rede)
- [Validação de utilitários](#validação-de-utilitários)
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
- emissão de relatório TXT estruturado da verificação de fixidez para backup incremental;
- aplicação de backup incremental usando o relatório estruturado da verificação de fixidez.

## Verificação de fixidez: caminhos longos e rede

Execute apenas os testes de regressão de `verify_fixity.py`:

```powershell
python -m unittest discover -s tests -p test_verify_fixity.py -v
```

O arquivo `test_verify_fixity.py` cobre:

- conversão de caminhos locais e UNC para o formato estendido do Windows, sem duplicar prefixos existentes;
- leitura real e enumeração de um caminho com acentos e mais de 260 caracteres no Windows;
- nova tentativa após falha transitória de leitura;
- repetição da consulta a um arquivo ausente antes de classificá-lo como `MISSING`;
- distinção entre ausência, permissão negada, caminho longo inválido e falha de rede;
- raiz indisponível classificada como erro de acesso;
- contagens separadas de íntegros, corrompidos, ausentes e erros no relatório;
- falha de enumeração registrada como `SCAN_ERROR`, com busca de extras incompleta e código de saída `1`.

Para conferir também a integração com preservação e backup incremental:

```powershell
python -m unittest discover -s tests -p test_preservation_backup_scripts.py -v
```

O teste real de caminho longo é exclusivo do Windows e aparece como `SKIP` em outros sistemas. Os testes de falhas de rede usam simulações; a validação de um compartilhamento real exige nova execução da verificação no ambiente de origem.

## Validação de utilitários

O gerador de execução para Windows fica na raiz do projeto e pode ser validado com:

```powershell
python -m py_compile gerador_bat.py
python gerador_bat.py
```

A execução deve criar `executar_thor_arquivista.bat` e `Thor Arquivista.lnk`. O atalho usa `icons/favicon.ico`.

## Relatório HTML

O relatório HTML lista:

- total de testes;
- quantidade de sucessos, falhas, erros e ignorados;
- duração total;
- lista numerada dos testes executados;
- finalidade, pré-condições e pós-condições de cada teste;
- status, duração e detalhes.

Um teste de symlink pode aparecer como `SKIP` quando o sistema operacional ou a política local não permite criar links simbólicos.
