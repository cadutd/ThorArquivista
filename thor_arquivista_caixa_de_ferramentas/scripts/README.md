# Manual dos Scripts - Thor Arquivista

Esta pasta contém os scripts de linha de comando usados pelo Thor Arquivista. Eles também são chamados pela interface gráfica por meio do `Worker`, mas podem ser executados diretamente no terminal.

Execute os comandos a partir da raiz do projeto:

```bash
python scripts/<script>.py --help
```

No Windows, use aspas em caminhos com espaços. Os manifestos BagIt gravam caminhos relativos com `/`, mesmo quando o comando recebe caminhos com `\`.

Quando uma opção de progresso está disponível, os scripts usam logs econômicos: total inicial, atualização em marcos de 5%, quantidade restante e resumo final de duração/média. Esse formato evita excesso de saída em lotes grandes e reduz escrita em disco quando os scripts são executados pela interface gráfica.

---

## Sumário

- [`hash_files.py`](#hash_filespy)
- [`verify_fixity.py`](#verify_fixitypy)
- [`build_bag.py`](#build_bagpy)
- [`incremental_backup_from_fixity.py`](#incremental_backup_from_fixitypy)
- [`build_sip.py`](#build_sippy)
- [`format_identify.py`](#format_identifypy)
- [`replicate_storage.py`](#replicate_storagepy)
- [`backup_plan.py`](#backup_planpy)
- [`duplicate_finder.py`](#duplicate_finderpy)
- [`delete_duplicates_by_manifest.py`](#delete_duplicates_by_manifestpy)
- [`premis_converter.py`](#premis_converterpy)
- [`premis_log.py`](#premis_logpy)
- [Módulo de apoio: `pd_common.py`](#modulo-de-apoio-pd_commonpy)
- [Boas práticas](#boas-praticas)

---

## `hash_files.py`

Gera manifesto BagIt de uma pasta.

Formato de saída:

```text
<hash>  <caminho/relativo>
```

Uso básico:

```bash
python scripts/hash_files.py --raiz "D:/acervo" --saida "D:/acervo/manifest-sha256.txt"
```

Uso com opções:

```bash
python scripts/hash_files.py \
  --raiz "D:/acervo" \
  --saida "D:/relatorios/manifest-sha256.txt" \
  --algo sha256 \
  --ignore-hidden \
  --pattern "**/*.pdf" \
  --workers 8 \
  --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta raiz a varrer. Obrigatório. |
| `--saida` | Arquivo de manifesto a gravar. Obrigatório. |
| `--algo` | Algoritmo de hash. Padrão: `sha256`. |
| `--include-ext` | Extensões a incluir, sem ponto. Ex.: `pdf tif jpg`. |
| `--exclude-ext` | Extensões a excluir, sem ponto. |
| `--min-size` | Tamanho mínimo em bytes. |
| `--max-size` | Tamanho máximo em bytes. |
| `--modified-after` | Inclui arquivos modificados após `YYYY-MM-DD`. |
| `--modified-before` | Inclui arquivos modificados antes de `YYYY-MM-DD`. |
| `--pattern` | Glob relativo. Ex.: `**/*.pdf`. |
| `--ignore-hidden` | Ignora itens ocultos iniciados por ponto. Desativado por padrão; na interface gráfica, a opção correspondente abre desmarcada. |
| `--follow-symlinks` | Segue links simbólicos. |
| `--workers` | Número de threads. |
| `--progress` | Mostra progresso no `stderr` em marcos de 5%, com quantidade restante e resumo final. |

Saída esperada:

```text
f2ca1bb6c7e907d06dafe4687e579fce  documento.pdf
9f86d081884c7d659a2feaa0c55ad015  subpasta/imagem.tif
```

---

## `verify_fixity.py`

Verifica fixidez comparando uma pasta com um manifesto BagIt.

Uso básico:

```bash
python scripts/verify_fixity.py --raiz "D:/acervo" --manifesto "D:/acervo/manifest-sha256.txt"
```

Uso com relatório de extras:

```bash
python scripts/verify_fixity.py \
  --raiz "D:/acervo" \
  --manifesto "D:/acervo/manifest-sha256.txt" \
  --report-extras \
  --max-list-items 200 \
  --report-file "D:/acervo/relatorios/fixity_2026-08-01.txt" \
  --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta onde os arquivos esperados estão. Obrigatório. |
| `--manifesto` | Manifesto BagIt a validar. Obrigatório. |
| `--algo` | Força o algoritmo. Se omitido, tenta inferir de `manifest-<algo>.txt`. |
| `--workers` | Número de threads de verificação. |
| `--progress` | Mostra progresso em marcos de 5%, com quantidade restante e resumo de tempo/média. |
| `--strict-missing` | Deixa explícito que faltantes geram erro. |
| `--report-extras` | Compatibilidade. O relatório final sempre lista arquivos extras. |
| `--max-list-items` | Máximo de itens por lista no stdout/log. Padrão: `200`; use `0` para listar tudo. |
| `--report-file` | Caminho para gravar o relatório TXT completo e estruturado. Se omitido, o script gera automaticamente ao lado do manifesto. |

Códigos de saída:

| Código | Significado |
|---|---|
| `0` | Tudo OK. |
| `1` | Há faltantes, divergências ou erro em arquivo. |
| `2` | Parâmetros inválidos, manifesto inválido ou algoritmo não suportado. |

Relatório final:

```text
=== Verificação de fixidez ===
Manifesto : D:\acervo\manifest-sha256.txt
Raiz      : D:\acervo
Algoritmo : sha256
Total no manifesto: 100
Arquivos verificados íntegros: 100
Arquivos verificados corrompidos: 0
Arquivos no manifesto ausentes na pasta analisada: 0
Divergências: 0
Arquivos na pasta analisada ausentes no manifesto: 0

-- Arquivos no manifesto ausentes na pasta analisada --
Nenhum

-- Arquivos verificados corrompidos ou com erro --
Nenhum

-- Arquivos na pasta analisada ausentes no manifesto --
Nenhum

=== Resumo final da verificação ===
Total no manifesto: 100
Arquivos verificados íntegros: 100
Arquivos verificados corrompidos: 0
Arquivos no manifesto ausentes na pasta analisada: 0
Arquivos na pasta analisada ausentes no manifesto: 0
Tempo de verificação: 12.34s
Média por arquivo verificado: 0.1234s/arquivo
```

Exemplo de stdout/log quando há lista grande compactada:

```text
[INFO] Verificação finalizada: 30860 arquivo(s) verificado(s) em 2364.43s; média 0.0766s/arquivo
[INFO] Procurando arquivos extras em disco...
=== Verificação de fixidez ===
Total no manifesto: 30860
Arquivos verificados íntegros: 28363
Arquivos verificados corrompidos: 0
Arquivos no manifesto ausentes na pasta analisada: 2497
Arquivos na pasta analisada ausentes no manifesto: 0

-- Arquivos no manifesto ausentes na pasta analisada --
data/foto_0001.jpg
data/foto_0002.jpg
... 2297 item(s) omitidos nesta visualização.

Relatório completo: D:\acervo\relatorios\fixity_2026-08-01.txt

=== Resumo final da verificação ===
Total no manifesto: 30860
Arquivos verificados íntegros: 28363
Arquivos verificados corrompidos: 0
Arquivos no manifesto ausentes na pasta analisada: 2497
Arquivos na pasta analisada ausentes no manifesto: 0
```

As contagens e seções de listas aparecem mesmo quando o valor é `0`; listas vazias usam `Nenhum`. Quando o manifesto está dentro da pasta analisada, o próprio arquivo de manifesto não é contado como extra. Para listas grandes, o stdout/log mostra apenas os primeiros itens de cada seção e informa o caminho do relatório TXT completo.

O relatório TXT é sempre emitido. Além da visualização humana, ele contém a seção `Dados estruturados para backup incremental` em TSV:

```text
status	path	expected_hash	actual_hash	detail
OK	data/a.txt	<hash>	<hash>
MISSING	data/b.txt	<hash>		Arquivo listado no manifesto ausente na pasta analisada
CORRUPT	data/c.txt	<hash>	<hash_atual>	Hash gerado diferente do hash no manifesto
EXTRA	data/d.txt			Arquivo presente na pasta analisada e ausente no manifesto
```

---

## `build_bag.py`

Cria pacote BagIt completo.

Saídas principais:

```text
bagit.txt
bag-info.txt
manifest-sha256.txt
data/
tagmanifest-sha256.txt   # opcional
```

Uso básico:

```bash
python scripts/build_bag.py "D:/acervo/fonte" "D:/bags/bag_001"
```

Uso com metadados e tagmanifest:

```bash
python scripts/build_bag.py "D:/acervo/fonte" "D:/bags/bag_001" \
  --algo sha256 \
  --mode copy \
  --pattern "**/*.pdf" \
  --tagmanifest \
  --organization "APESP" \
  --source-organization "Secretaria X" \
  --contact-name "Nome do contato" \
  --contact-email "contato@example.org" \
  --description "Transferência 2026-04" \
  --profile apesp \
  --profile-param transfer_id=TRF-2026-001
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `src` | Pasta fonte do payload. Obrigatório. |
| `dst` | Pasta destino do BagIt. Obrigatório. |
| `--algo` | Algoritmo do manifesto. Padrão: `sha256`. |
| `--mode` | `copy`, `link` ou `move`. Padrão: `copy`. |
| `--pattern` | Glob dos arquivos a empacotar. Padrão: `*`. |
| `--include-hidden` | Inclui arquivos ocultos. |
| `--follow-symlinks` | Segue links simbólicos. |
| `--tagmanifest` | Gera tagmanifest dos arquivos de tag. |
| `--organization` | Valor de `Organization`. |
| `--source-organization` | Valor de `Source-Organization`. |
| `--contact-name` | Valor de `Contact-Name`. |
| `--contact-email` | Valor de `Contact-Email`. |
| `--description` | Valor de `External-Description`. |
| `--profile` | Nome lógico em `profiles/[nome]-profileBagit.json` ou caminho JSON. |
| `--profile-param` | Parâmetro extra `chave=valor`. Pode repetir. |

Observações:

- O destino deve não existir ou estar vazio.
- Em `--mode link`, se hardlink não for suportado, o script faz fallback para cópia.
- Profiles podem preencher campos obrigatórios de `bag-info.txt`.
- Transferência e geração do manifesto do payload registram progresso em marcos de 5% e resumo de tempo/média.

---

## `validate_bag.py`

Valida um pacote BagIt gerado pelo Thor Arquivista.

Uso básico:

```bash
python scripts/validate_bag.py "D:/bags/bag_001"
```

Uso com progresso e algoritmo específico:

```bash
python scripts/validate_bag.py "D:/bags/bag_001" --algo sha256 --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `bag` | Pasta raiz do pacote BagIt. Obrigatório. |
| `--algo` | Valida apenas manifestos do algoritmo informado. Se omitido, valida todos os `manifest-*.txt` e `tagmanifest-*.txt`. |
| `--progress` | Mostra progresso no `stderr` em marcos de 5%, com quantidade restante e resumo final. |

Validações executadas:

- presença de `bagit.txt`, `bag-info.txt` e `data/`;
- conteúdo mínimo de `bagit.txt` para BagIt 0.97 e UTF-8;
- hash dos arquivos listados em `manifest-*.txt`;
- arquivos de payload ausentes, corrompidos ou extras em `data/`;
- hash dos arquivos listados em `tagmanifest-*.txt`, quando existirem.

O script retorna `0` quando o pacote é válido e `2` quando encontra inconsistências.

---

## `incremental_backup_from_fixity.py`

Aplica um backup incremental usando o relatório TXT estruturado emitido por `verify_fixity.py`.

Uso básico:

```bash
python scripts/incremental_backup_from_fixity.py \
  --relatorio-fixidez "D:/acervo/verify_fixity_report.txt" \
  --origem "D:/origem" \
  --destino "E:/backup" \
  --progress
```

Uso em simulação:

```bash
python scripts/incremental_backup_from_fixity.py \
  --relatorio-fixidez "D:/acervo/verify_fixity_report.txt" \
  --origem "D:/origem" \
  --destino "E:/backup" \
  --saida-relatorio "D:/acervo/incremental_report.txt" \
  --dry-run
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--relatorio-fixidez` | Relatório TXT gerado por `verify_fixity.py`. Obrigatório. |
| `--origem` | Pasta de origem do backup. Obrigatório. |
| `--destino` | Pasta de destino a atualizar. Obrigatório. |
| `--saida-relatorio` | Relatório TXT da aplicação incremental. Se omitido, gera no destino. |
| `--dry-run` | Simula sem copiar arquivos. |
| `--progress` | Mostra progresso em marcos de 5%. |

Regras por status do relatório de fixidez:

| Status | Ação |
|---|---|
| `OK` | Ignora. |
| `MISSING` | Copia o arquivo da origem para o destino. |
| `CORRUPT` | Substitui o arquivo do destino pelo arquivo da origem. |
| `ERROR` | Tenta copiar novamente da origem. |
| `EXTRA` | Reporta, mas não exclui automaticamente. |

Exemplo de relatório de aplicação:

```text
=== Backup incremental por relatório de fixidez ===
Relatório de fixidez: D:\acervo\verify_fixity_report.txt
Origem: D:\origem
Destino: E:\backup
Modo simulação: não
Registros lidos: 5
Registros OK ignorados: 1
Registros EXTRA ignorados: 1
Arquivos candidatos a copiar: 3
Arquivos copiados: 3
Arquivos ausentes na origem: 0
Caminhos inválidos no relatório: 0
Falhas de cópia: 0
```

Quando o caminho do relatório começa com `data/`, a origem também é testada sem esse prefixo. Isso permite usar relatórios de pacotes BagIt em que o destino mantém payload sob `data/`, mas a origem do backup é a pasta original.

---

## `build_sip.py`

Cria um SIP simples com objetos, metadados e manifesto SHA-256.

Estrutura gerada:

```text
<saida>/<sip-id>/
  objects/
  metadata/metadata.json
  manifest-sha256.txt
```

Uso básico:

```bash
python scripts/build_sip.py --fonte "D:/acervo/fonte" --saida "D:/sips" --sip-id "SIP_001"
```

Gerar também ZIP:

```bash
python scripts/build_sip.py \
  --fonte "D:/acervo/fonte" \
  --saida "D:/sips" \
  --sip-id "SIP_001" \
  --zip
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--fonte` | Pasta de origem dos objetos. Obrigatório. |
| `--saida` | Diretório onde o SIP será criado. Obrigatório. |
| `--sip-id` | Identificador/nome do SIP. Obrigatório. |
| `--zip` | Compacta o SIP em ZIP. |
| `--no-zip` | Não compacta. Padrão. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

---

## `format_identify.py`

Identifica formato de arquivos em uma pasta.

Se o utilitário externo `sf` (Siegfried) estiver disponível no `PATH`, o script usa Siegfried. Caso contrário, usa fallback por `mimetypes`.

Uso imprimindo no terminal:

```bash
python scripts/format_identify.py --raiz "D:/acervo"
```

Uso gravando JSONL:

```bash
python scripts/format_identify.py --raiz "D:/acervo" --saida "D:/relatorios/formatos.jsonl"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta a varrer. Obrigatório. |
| `--saida` | Arquivo JSONL de saída. Se omitido, imprime no terminal. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

Exemplo de linha JSONL:

```json
{"path":"D:/acervo/doc.pdf","sha256":"...","mime":"application/pdf","id":"fmt/18","format":"Acrobat PDF","basis":"...","relpath":"doc.pdf"}
```

---

## `replicate_storage.py`

Replica arquivos para um ou mais destinos e valida a cópia por manifesto.

Fluxo:

1. Gera `manifest-sha256.txt` da pasta fonte dentro de cada destino.
2. Copia os arquivos.
3. Valida cada destino com `verify_fixity.py`.

As etapas de manifesto, cópia e verificação usam progresso em marcos de 5% quando o script não está em `--quiet`.

Uso com um destino:

```bash
python scripts/replicate_storage.py --fonte "D:/acervo" --destino "E:/backup"
```

Uso com múltiplos destinos:

```bash
python scripts/replicate_storage.py \
  --fonte "D:/acervo" \
  --destino "E:/backup_1" \
  --destino "F:/backup_2"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--fonte` | Pasta de origem. Obrigatório. |
| `--destino` | Pasta de destino. Obrigatório; pode repetir. |
| `--verificar-hash` | Compatibilidade. A verificação por manifesto é sempre executada. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

Proteção:

- O destino não pode estar dentro da origem.
- Se a verificação falhar, o script encerra com erro.

---

## `backup_plan.py`

Executa backup preservacional incremental baseado em BagIt. O plano JSON define destino, opções e origens; o destino é mantido como repositório BagIt, com `data/`, `manifest-sha256.txt`, `tagmanifest-sha256.txt`, `bag-info.txt`, `bagit.txt` e histórico em `thor-backup/`.

Uso básico:

```bash
python scripts/backup_plan.py --config "D:/planos/backup.json"
```

Retomar por checkpoint:

```bash
python scripts/backup_plan.py --resume --config "D:/planos/backup.json"
```

Exemplo de plano:

```json
{
  "name": "acervo_institucional",
  "destination": "E:/Backup",
  "sources": [
    {"name": "documentos", "path": "D:/Acervo/Documentos"},
    {"name": "imagens", "path": "D:/Acervo/Imagens"}
  ],
  "options": {
    "algo": "sha256",
    "ignore_hidden": true
  }
}
```

Scripts relacionados:

```bash
python scripts/backup_manifest_build.py --raiz "D:/Acervo" --prefix "data/acervo" --saida "D:/manifest.txt"
python scripts/backup_manifest_diff.py --origem "D:/manifest_origem.txt" --destino "E:/Backup/manifest-sha256.txt"
python scripts/backup_verify.py --destino "E:/Backup" --progress
python scripts/backup_report.py --destino "E:/Backup" --backup "acervo_institucional"
```

Responsabilidades dos scripts relacionados:

| Script | Responsabilidade |
|---|---|
| `backup_manifest_build.py` | Gera manifesto da origem com prefixo BagIt, algoritmo configurável, opção de ignorar ocultos e suporte a symlinks. |
| `backup_manifest_diff.py` | Compara manifesto de origem com manifesto do destino e classifica `new`, `changed`, `same` e `removed`. |
| `backup_verify.py` | Valida fixidez do repositório BagIt de backup e pode registrar evento PREMIS `FIXITY_CHECK`. |
| `backup_report.py` | Lista checkpoints, relatórios e manifestos históricos de um destino de backup. |

Saídas principais:

```text
Backup/
  data/
  manifest-sha256.txt
  tagmanifest-sha256.txt
  bag-info.txt
  bagit.txt
  thor-backup/
    configs/
    manifests/origem/
    manifests/destino/
    manifests/historico/
    checkpoints/
    relatorios/
    logs/
    versoes/
```

Parada segura:

- Crie `thor-backup/checkpoints/STOP` dentro do destino.
- O script termina o arquivo atual, atualiza manifesto/checkpoint, registra PREMIS e encerra como `PAUSED`.
- Remova o arquivo `STOP` antes de executar com `--resume`.

Eventos PREMIS registrados pelo script:

```text
BACKUP_STARTED
BACKUP_INCREMENTAL
BACKUP_PAUSED
BACKUP_RESUMED
BACKUP_COMPLETED
BACKUP_FAILED
FIXITY_CHECK
```

Observações:

- Arquivos alterados têm a versão anterior movida para `thor-backup/versoes/`.
- Arquivos removidos da origem são preservados no destino e mantidos no manifesto do backup.
- O checkpoint fica em `thor-backup/checkpoints/<backup>.state.json`.
- O manifesto BagIt do destino continua sendo a fonte de verdade; nenhum banco SQL é usado.
- Geração de manifesto de origem e aplicação incremental registram progresso em marcos de 5% quando `--progress` está ativo.

Testes do backup preservacional:

```powershell
py tests\run_backup_tests_html.py
```

O comando executa testes de scripts e interface gráfica com widgets simulados e grava o relatório em `tests/reports/backup_tests_report.html`.

---

## `duplicate_finder.py`

Ferramenta multifunção para inventariar arquivos, detectar duplicatas, gerar planilha de decisão, gerar scripts de tratamento e dashboards.

### 1. Inventariar arquivos

```bash
python scripts/duplicate_finder.py \
  --raiz "D:/acervo" \
  --inventario "D:/relatorios/inventario.csv" \
  --mostrar-progresso
```

Gera CSV com hash SHA-256, tamanho e metadados.

### 2. Detectar duplicatas

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --duplicatas "D:/relatorios/duplicatas.csv"
```

Gera CSV com grupos de duplicatas.

### 3. Gerar modelo de decisões

```bash
python scripts/duplicate_finder.py \
  --from-duplicatas "D:/relatorios/duplicatas.csv" \
  --decisoes "D:/relatorios/decisoes.csv"
```

Gera CSV para revisão humana. Use esse arquivo para indicar o que manter e o que tratar.

### 4. Gerar script de tratamento

Mover para quarentena no Windows:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/tratar.cmd" \
  --sistema windows \
  --acao quarentena \
  --prefixo-quarentena "QUARENTENA_DUP"
```

Mover para quarentena no Linux/macOS:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/tratar.sh" \
  --sistema linux \
  --acao quarentena \
  --prefixo-quarentena "QUARENTENA_DUP"
```

Gerar script de remoção definitiva:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/remover.cmd" \
  --sistema windows \
  --acao remover
```

### 5. Gerar dashboards

Dashboard de potencial de recuperação:

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --duplicatas "D:/relatorios/duplicatas.csv" \
  --dashboard-duplicatas-csv "D:/relatorios/dashboard_duplicatas.csv" \
  --dashboard-duplicatas-xlsx "D:/relatorios/dashboard_duplicatas.xlsx"
```

Dashboard de recuperação planejada:

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --decisoes "D:/relatorios/decisoes.csv" \
  --dashboard-decisoes-csv "D:/relatorios/dashboard_decisoes.csv" \
  --dashboard-decisoes-xlsx "D:/relatorios/dashboard_decisoes.xlsx"
```

Parâmetros principais:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta a inventariar. |
| `--inventario` | CSV de inventário. |
| `--duplicatas` | CSV de duplicatas. |
| `--from-duplicatas` | CSV de duplicatas usado para gerar decisões. |
| `--decisoes` | CSV de decisões. |
| `--gerar-script-remocao` | Caminho do script `.sh` ou `.cmd` a gerar. |
| `--sistema` | `linux` ou `windows`. |
| `--acao` | `quarentena` ou `remover`. |
| `--prefixo-quarentena` | Prefixo da pasta de quarentena. |
| `--script-log-nome` | Nome do log gerado pelo script de tratamento. |
| `--mostrar-progresso` | Mostra progresso no inventário em marcos de 5%, com quantidade restante e resumo final. |
| `--dashboard-duplicatas-csv` | CSV de dashboard de duplicatas. |
| `--dashboard-duplicatas-xlsx` | XLSX de dashboard de duplicatas. |
| `--dashboard-decisoes-csv` | CSV de dashboard de decisões. |
| `--dashboard-decisoes-xlsx` | XLSX de dashboard de decisões. |

Aviso:

- Revise `decisoes.csv` antes de executar qualquer script de tratamento.
- Prefira `quarentena` antes de usar `remover`.

---

## `delete_duplicates_by_manifest.py`

Apaga arquivos de uma pasta de possíveis duplicatas quando o hash SHA-256 já existe no manifesto gerado a partir de uma pasta origem.

Fluxo:

1. Gera `manifest-sha256.txt` da pasta origem.
2. Percorre a pasta de possíveis duplicatas.
3. Apaga arquivos cujo SHA-256 aparece no manifesto.
4. Gera `relatorio_exclusao_duplicatas.csv` com arquivos apagados e espaço recuperado.

Uso básico:

```bash
python scripts/delete_duplicates_by_manifest.py \
  --origem "D:/acervo/originais" \
  --duplicatas "D:/acervo/possiveis_duplicatas"
```

Uso com pastas de saída:

```bash
python scripts/delete_duplicates_by_manifest.py \
  --origem "D:/acervo/originais" \
  --duplicatas "D:/acervo/possiveis_duplicatas" \
  --manifesto "D:/relatorios/manifesto_origem" \
  --relatorio "D:/relatorios/exclusao_duplicatas" \
  --progress
```

Saídas:

```text
D:/relatorios/manifesto_origem/manifest-sha256.txt
D:/relatorios/exclusao_duplicatas/relatorio_exclusao_duplicatas.csv
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--origem` | Pasta usada como referência. Obrigatório. |
| `--duplicatas` | Pasta a percorrer e limpar. Obrigatório. |
| `--manifesto` | Pasta onde será gravado `manifest-sha256.txt`. |
| `--relatorio` | Pasta onde será gravado `relatorio_exclusao_duplicatas.csv`. |
| `--progress` | Mostra progresso em marcos de 5%, com quantidade restante e resumo final. |

Proteções:

- Origem e duplicatas não podem ser iguais.
- Origem e duplicatas não podem ser pastas sobrepostas.
- O manifesto e o relatório não são varridos como candidatos de exclusão.

---

## `premis_converter.py`

Converte registros PREMIS entre XML, CSV e JSON e pode validar XML contra XSD.

Uso para validar XML:

```bash
python scripts/premis_converter.py --in "D:/premis/premis.xml" --validate
```

Converter XML para CSV:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.xml" \
  --out "D:/premis/premis.csv" \
  --validate \
  --schema "schemas/premis-v3-0.xsd"
```

Converter CSV para XML:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.csv" \
  --out "D:/premis/premis.xml" \
  --schema "schemas/premis-v3-0.xsd"
```

Converter JSON para XML:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.json" \
  --out "D:/premis/premis.xml" \
  --validate
```

Gerar exemplos:

```bash
python scripts/premis_converter.py --example
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--in` | Arquivo de entrada `.xml`, `.csv` ou `.json`. |
| `--out` | Arquivo de saída `.xml`, `.csv` ou `.json`. |
| `--validate` | Valida XML de entrada ou saída. |
| `--schema` | Caminho alternativo para `premis-v3-0.xsd`. |
| `--example` | Gera exemplos em `./examples`. |

Observação para Windows:

- Se `--help` falhar por encoding do console, execute em um terminal UTF-8 ou use `chcp 65001` antes do comando.

---

## `premis_log.py`

Acrescenta um evento PREMIS simples em um arquivo JSONL.

Uso básico:

```bash
python scripts/premis_log.py \
  --arquivo-log "logs/premis_events.jsonl" \
  --tipo "fixity check" \
  --obj-id "D:/acervo/manifest-sha256.txt"
```

Uso completo:

```bash
python scripts/premis_log.py \
  --arquivo-log "logs/premis_events.jsonl" \
  --tipo "replication" \
  --obj-id "D:/acervo" \
  --detalhe "Cópia para E:/backup validada com manifesto" \
  --resultado "success" \
  --agente "Thor Arquivista"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--arquivo-log` | Arquivo JSONL de eventos PREMIS. Obrigatório. |
| `--tipo` | Tipo do evento. Obrigatório. |
| `--obj-id` | Identificador do objeto. Obrigatório. |
| `--detalhe` | Detalhe textual do evento. |
| `--resultado` | Resultado do evento. Padrão: `success`. |
| `--agente` | Nome do agente. Padrão: `Sistema de Preservação`. |

Exemplo de linha JSONL:

```json
{"eventIdentifier":"local-...","eventType":"fixity check","eventDateTime":"...Z","eventDetail":"","eventOutcome":"success","linkingObjectIdentifier":"D:/acervo","linkingAgentName":"Thor Arquivista"}
```

---

## Módulo de apoio: `pd_common.py`

`pd_common.py` não é uma ferramenta de uso direto. Ele concentra funções compartilhadas por outros scripts, como:

- cálculo SHA-256;
- cópia segura;
- iteração de arquivos;
- leitura de configuração YAML/JSON;
- suporte opcional a `tqdm`.

Não execute este arquivo como uma tarefa de preservação.

---

## Boas Práticas

- Use `sha256` como algoritmo padrão para preservação.
- Sempre coloque caminhos com espaços entre aspas.
- Faça testes em cópias antes de executar comandos que movem ou apagam arquivos.
- Guarde manifestos e relatórios junto com a documentação da operação.
- Para lotes grandes, use `--progress` ou `--mostrar-progresso`; a saída é limitada a marcos de 5%.
- Em Windows, se um comando exibir caracteres incorretos, tente `chcp 65001`.

---

## Licença

Este projeto é licenciado sob a GNU General Public License v3.0 (GPLv3).

© 2025 Carlos Eduardo Carvalho Amand.
